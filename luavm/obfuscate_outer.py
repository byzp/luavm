from __future__ import annotations

import random
import re
from typing import Optional


def _obfuscate_outer_vm(source: str, rng: random.Random) -> str:
    source = _cff_run_frame(source, rng)
    source = _shuffle_functions(source, rng)
    source = _extract_constants(source, rng)
    source = _rename_identifiers(source, rng)
    source = _encode_strings(source, rng)
    source = _inject_opaque_predicates(source, rng)
    source = _split_dispatch(source, rng)
    source = _polymorph_runtime(source, rng)
    source = _compress_source(source, rng)
    return source


_LUA_RESERVED = {
    "__index",
    "__newindex",
    "__call",
    "__gc",
    "__mode",
    "__eq",
    "__lt",
    "__le",
    "__add",
    "__sub",
    "__mul",
    "__div",
    "__mod",
    "__pow",
    "__unm",
    "__concat",
    "__len",
    "__tostring",
    "__metatable",
}


def _rename_identifiers(source: str, rng: random.Random) -> str:
    pattern = re.compile(r"(__[a-z_]+)")
    seen: dict[str, str] = {}
    parts: list[str] = []
    pos = 0
    for match in pattern.finditer(source):
        parts.append(source[pos : match.start()])
        original = match.group(1)
        if original in _LUA_RESERVED or original.startswith("__vm_"):
            parts.append(original)
        else:
            if original not in seen:
                seen[original] = _make_name(rng, len(seen))
            parts.append(seen[original])
        pos = match.end()
    parts.append(source[pos:])
    return "".join(parts)


def _make_name(rng: random.Random, index: int) -> str:
    consonants = "bcdfghjklmnpqrstvwxyz"
    vowels = "aeiou"
    parts: list[str] = []
    i = index
    parts.append(consonants[i % len(consonants)])
    i //= len(consonants)
    while i > 0:
        parts.append(vowels[i % len(vowels)])
        i //= len(vowels)
        parts.append(consonants[i % len(consonants)])
        i //= len(consonants)
    return "_" + "".join(parts)


_RESERVED_STRINGS = frozenset(
    {
        "__declared",
        "__index",
        "__newindex",
        "__call",
        "number",
        "string",
        "function",
        "table",
        "boolean",
        "nil",
        "userdata",
        "thread",
        "line",
        "call",
        "return",
        "count",
        "local",
        "global",
        "upvalue",
        "field",
        "GLOBAL",
    }
)


def _encode_strings(source: str, rng: random.Random) -> str:
    pattern = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'')
    matches = list(pattern.finditer(source))
    if not matches:
        return source
    replacements: list[tuple[int, int, str]] = []
    for match in matches:
        original = match.group(0)
        if len(original) < 6:
            continue
        line_start = source.rfind("\n", 0, match.start()) + 1
        line_prefix = source[line_start : match.start()].lstrip()
        if line_prefix.startswith("local __VM_"):
            continue
        if "__VM_SKIP_STRING__" in source[line_start : source.find("\n", match.end())]:
            continue
        inner = original[1:-1]
        if any(ord(ch) > 127 for ch in inner):
            continue
        if any(not (32 <= ord(ch) < 127) for ch in inner):
            continue
        if " " in inner:
            continue
        if inner.startswith("LVM"):
            continue
        if any(c in inner for c in "(){}[];:=><+-*/%^#"):
            continue
        if inner in _RESERVED_STRINGS:
            continue
        encoder = rng.choice(["hex_caesar", "xor_table", "reverse_shift"])
        new_str = _encode_string(inner, encoder, rng)
        replacements.append((match.start(), match.end(), new_str))
    parts: list[str] = []
    pos = 0
    for start, end, new_str in replacements:
        parts.append(source[pos:start])
        parts.append(new_str)
        pos = end
    parts.append(source[pos:])
    return "".join(parts)


def _encode_string(inner: str, method: str, rng: random.Random) -> str:
    if method == "hex_caesar":
        key = rng.randrange(1, 256)
        encoded: list[int] = []
        for ch in inner:
            encoded.append((ord(ch) + key) % 256)
        hex_str = "".join(f"{v:02x}" for v in encoded)
        return f'(function(s,k) local r="" for i=1,#s,2 do r=r.._string.char((_tonumber(s:sub(i,i+1),16)-k)%256) end return r end)([=[{hex_str}]=],{key})'
    if method == "sub_table":
        key = rng.randrange(1, 256)
        encoded = []
        for ch in inner:
            encoded.append((ord(ch) - key) % 256)
        tbl = "{" + ",".join(str(v) for v in encoded) + "}"
        return f'(function(t,k) local r="" for i=1,#t do r=r.._string.char((t[i]+k)%256) end return r end)({tbl},{key})'
    if method == "reverse_shift":
        key = rng.randrange(1, 256)
        encoded = []
        for ch in inner:
            encoded.append((ord(ch) + key) % 256)
        encoded.reverse()
        hex_str = "".join(f"{v:02x}" for v in encoded)
        return f'(function(s,k) local r="" for i=#s,1,-2 do r=r.._string.char((_tonumber(s:sub(i-1,i),16)-k)%256) end return r end)([=[{hex_str}]=],{key})'
    key = rng.randrange(1, 256)
    encoded = []
    for ch in inner:
        encoded.append((ord(ch) + key) % 256)
    hex_str = "".join(f"{v:02x}" for v in encoded)
    return f'(function(s,k) local r="" for i=1,#s,2 do r=r.._string.char((_tonumber(s:sub(i,i+1),16)-k)%256) end return r end)([=[{hex_str}]=],{key})'


def _split_dispatch(source: str, rng: random.Random) -> str:
    lines = source.split("\n")
    insert_positions = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("local function ") and i > 5:
            insert_positions.append(i)
    if len(insert_positions) < 3:
        return source
    chosen = rng.sample(insert_positions, min(5, len(insert_positions)))
    decoy_names = [
        "_check",
        "_verify",
        "_validate",
        "_transform",
        "_process",
        "_compute",
        "_resolve",
        "_analyze",
        "_prepare",
        "_finalize",
    ]
    rng.shuffle(decoy_names)
    result_lines = list(lines)
    offset = 0
    for idx, pos in enumerate(sorted(chosen)):
        name = decoy_names[idx % len(decoy_names)]
        indent = "    "
        decoy = [
            f"{indent}local function {name}(...)",
            f"{indent}    return ...",
            f"{indent}end",
        ]
        for j, dl in enumerate(decoy):
            result_lines.insert(pos + offset + j, dl)
        offset += len(decoy)
    return "\n".join(result_lines)


_NUM_CONSTANTS = [
    16777216,
    65536,
    256,
    2147483647,
    4294967296,
    16807,
    48271,
    69621,
    1515870810,
    1010580540,
    0x5A5A5A5A,
    0x3C3C3C3C,
    1103515245,
    12345,
    2147483648,
]


def _split_number(value: int, rng: random.Random) -> str:
    if value <= 10:
        return str(value)
    method = rng.choice(["add", "sub", "shift_add"])
    if method == "add":
        delta = rng.randrange(1, min(value, 1000))
        return f"({value - delta}+{delta})"
    if method == "sub":
        delta = rng.randrange(1, 1000)
        return f"({value + delta}-{delta})"
    shift = rng.randrange(1, 8)
    remainder = value % (1 << shift)
    base = value >> shift
    if remainder == 0:
        return f"({base}*{1 << shift})"
    return f"({base}*{1 << shift}+{remainder})"


def _polymorph_runtime(source: str, rng: random.Random) -> str:
    source = _polymorph_constants(source, rng)
    source = _polymorph_if_chain(source, rng)
    source = _polymorph_junk_blocks(source, rng)
    return source


def _polymorph_constants(source: str, rng: random.Random) -> str:
    for const in _NUM_CONSTANTS:
        pattern = re.compile(r"(?<![a-zA-Z_0-9])" + str(const) + r"(?![a-zA-Z_0-9])")
        replacement = _split_number(const, rng)
        source = pattern.sub(replacement, source, count=rng.randrange(1, 4))
    return source


def _polymorph_if_chain(source: str, rng: random.Random) -> str:
    for func_name in ["binary", "unary"]:
        header_pat = re.compile(
            r"(    local function " + func_name + r"\([^)]*\)\n)",
        )
        hm = header_pat.search(source)
        if not hm:
            continue
        search_start = hm.end()
        error_pat = re.compile(
            r'        _error\("LVM: invalid '
            + func_name
            + r' operation", 0\)\n    end\)',
        )
        em = error_pat.search(source, search_start)
        if not em:
            continue
        body = source[search_start : em.start()]
        branches = re.findall(r"        if op == \d+ then return.+?\n", body)
        if len(branches) < 3:
            continue
        rng.shuffle(branches)
        source = source[:search_start] + "".join(branches) + source[em.start() :]
    return source


def _polymorph_junk_blocks(source: str, rng: random.Random) -> str:
    lines = source.split("\n")
    insert_positions = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("end") and len(indent) == 4 and i > 10:
            if i + 1 < len(lines) and lines[i + 1].lstrip().startswith(
                "local function "
            ):
                insert_positions.append(i + 1)
    if not insert_positions:
        return source
    chosen = rng.sample(insert_positions, min(3, len(insert_positions)))
    junk_templates = [
        "do local _=0 if _~=0 then _=1+2+3 end end",
        "do local _=nil if _ then _=_+1 end end",
        "do local _=false if _ then _=not _ end end",
    ]
    result_lines = list(lines)
    offset = 0
    for pos in sorted(chosen):
        junk = junk_templates[rng.randrange(len(junk_templates))]
        result_lines.insert(pos + offset, "    " + junk)
        offset += 1
    return "\n".join(result_lines)


def _dedent_lines(lines: list[str], base_indent: int) -> list[str]:
    result: list[str] = []
    for line in lines:
        if not line.strip():
            result.append("")
            continue
        leading = len(line) - len(line.lstrip())
        if leading >= base_indent:
            result.append(line[base_indent:])
        else:
            result.append(line.lstrip())
    return result


def _indent_lines(lines: list[str], prefix: str) -> list[str]:
    return [prefix + line if line.strip() else line for line in lines]


def _generate_block_ids(count: int, rng: random.Random) -> list[int]:
    used: set[int] = set()
    ids: list[int] = []
    for _ in range(count):
        while True:
            bid = rng.randint(1, (1 << 24) - 1)
            if bid not in used:
                used.add(bid)
                ids.append(bid)
                break
    return ids


def _build_bst_dispatch(
    blocks: list[tuple[int, list[str]]], rng: random.Random, base_indent: str
) -> list[str]:
    sorted_blocks = sorted(blocks, key=lambda b: b[0])
    return _build_bst_recursive(
        sorted_blocks, 0, len(sorted_blocks) - 1, rng, base_indent
    )


def _build_bst_recursive(
    blocks: list[tuple[int, list[str]]],
    left: int,
    right: int,
    rng: random.Random,
    indent: str,
) -> list[str]:
    if left > right:
        return []
    length = right - left + 1
    if length == 1:
        return _indent_lines(blocks[left][1], indent)
    if length <= 4:
        return _build_elseif_chain(blocks, left, right, rng, indent)
    mid = left + (length + 1) // 2
    bound = (blocks[mid - 1][0] + blocks[mid][0]) // 2
    left_lines = _build_bst_recursive(blocks, left, mid - 1, rng, indent + "    ")
    right_lines = _build_bst_recursive(blocks, mid, right, rng, indent + "    ")
    style = rng.randrange(3)
    lines: list[str] = []
    if style == 0:
        lines.append(f"{indent}if _pos < {bound} then")
    elif style == 1:
        lines.append(f"{indent}if {bound} > _pos then")
    else:
        lines.append(f"{indent}if _pos > {bound} then")
        left_lines, right_lines = right_lines, left_lines
    lines.extend(left_lines)
    lines.append(f"{indent}else")
    lines.extend(right_lines)
    lines.append(f"{indent}end")
    return lines


def _build_elseif_chain(
    blocks: list[tuple[int, list[str]]],
    left: int,
    right: int,
    rng: random.Random,
    indent: str,
) -> list[str]:
    lines: list[str] = []
    for i in range(left, right + 1):
        bid = blocks[i][0]
        if i < right:
            bound = (bid + blocks[i + 1][0]) // 2
        else:
            bound = bid + 1
        style = rng.randrange(2)
        keyword = "if" if i == left else "elseif"
        if i < right:
            if style == 0:
                lines.append(f"{indent}{keyword} _pos < {bound} then")
            else:
                lines.append(f"{indent}{keyword} {bound} > _pos then")
        else:
            lines.append(f"{indent}else")
        lines.extend(_indent_lines(blocks[i][1], indent + "    "))
    lines.append(f"{indent}end")
    return lines


_RETURN_OPS = {24, 34, 35}
_JUMP_OPS = {17, 18, 19, 20, 21, 36}
_SEQ_OPS = {
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    22,
    23,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    37,
    38,
}


def _cff_run_frame(source: str, rng: random.Random) -> str:
    rf_pat = re.compile(r"(    local function run_frame\(frame\)\n)")
    rf_m = rf_pat.search(source)
    if not rf_m:
        return source
    rf_header_end = rf_m.end()

    while_pat = re.compile(r"        while true do\n")
    while_m = while_pat.search(source, rf_header_end)
    if not while_m:
        return source
    while_start = while_m.start()
    while_header_end = while_m.end()

    pre_while = source[rf_header_end:while_start]

    chain_start_pat = re.compile(r"            if op == 0 then\n")
    chain_start_m = chain_start_pat.search(source, while_header_end)
    if not chain_start_m:
        return source
    chain_start = chain_start_m.start()

    fetch_code = source[while_header_end:chain_start]

    idx = source.find("invalid inner opcode", chain_start)
    if idx < 0:
        return source
    after_error = source.find("\n", idx)
    if after_error < 0:
        return source
    if_end = source.find("\n", after_error + 1)
    if if_end < 0:
        return source
    chain_end = if_end + 1
    while_end_line = source.find("\n", chain_end)
    if while_end_line < 0:
        return source
    post_chain = source[while_end_line + 1 :]

    handlers = _extract_opcode_handlers(source[chain_start:chain_end])
    if len(handlers) < 10:
        return source

    block_ids = _generate_block_ids(len(handlers), rng)

    blocks: list[tuple[int, list[str]]] = []
    for (op_info, body), bid in zip(handlers, block_ids):
        body_lines_raw: list[str] = []
        for bl in body.split("\n"):
            if bl.strip():
                body_lines_raw.append(bl)
        body_lines = _dedent_lines(body_lines_raw, 12)
        blocks.append((bid, body_lines))

    rng.shuffle(blocks)

    op_to_id: dict[int, int] = {}
    for (op_info, _), bid in zip(handlers, block_ids):
        if isinstance(op_info, int):
            op_to_id[op_info] = bid
        else:
            for o in op_info:
                op_to_id[o] = bid

    dispatch_table_entries: list[str] = []
    for op_val in sorted(op_to_id.keys()):
        dispatch_table_entries.append(f"[{op_val}]={op_to_id[op_val]}")
    dispatch_table = "local _opd = {" + ",".join(dispatch_table_entries) + "}"

    fetch_lines_raw: list[str] = []
    for fl in fetch_code.split("\n"):
        if fl.strip():
            fetch_lines_raw.append(fl)
    fetch_lines = _dedent_lines(fetch_lines_raw, 12)
    fetch_lines.append("local _pos = _opd[op]")

    dispatch_lines = _build_bst_dispatch(blocks, rng, "            ")

    new_while_body = f"        {dispatch_table}\n"
    new_while_body += "        while true do\n"
    for fl in _indent_lines(fetch_lines, "            "):
        new_while_body += fl + "\n"
    for dl in dispatch_lines:
        new_while_body += dl + "\n"
    new_while_body += "        end\n"

    new_rf = pre_while + new_while_body + post_chain
    return source[:rf_header_end] + new_rf


def _extract_opcode_handlers(chain: str) -> list[tuple[int | tuple[int, ...], str]]:
    lines = chain.split("\n")
    handlers = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(
            r"\s*(?:if|elseif) op == (\d+)(?: or op == (\d+))? then(.*)$", line
        )
        if not m:
            i += 1
            continue
        op1 = int(m.group(1))
        op2 = int(m.group(2)) if m.group(2) else None
        current_op = (op1, op2) if op2 is not None else op1
        inline_body = m.group(3).strip()
        if inline_body:
            handlers.append((current_op, inline_body))
            i += 1
            continue
        body_lines = []
        i += 1
        while i < len(lines):
            stripped = lines[i].lstrip()
            if re.match(r"elseif op == \d+", stripped):
                break
            if stripped.startswith("else") and not stripped.startswith("elseif"):
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                if "invalid inner opcode" in next_line:
                    break
            if "invalid inner opcode" in stripped:
                break
            body_lines.append(lines[i])
            i += 1
        body = "\n".join(body_lines).rstrip()
        handlers.append((current_op, body))
    return handlers


def _find_function_end(lines: list[str], start: int) -> int:
    depth = 0
    j = start
    while j < len(lines):
        stripped = lines[j].lstrip()
        tokens = stripped.split()
        for token in tokens:
            if token in ("if", "while", "for", "function", "do", "repeat"):
                depth += 1
            if (
                token == "end"
                or token.startswith("end,")
                or token.startswith("end)")
                or token == "end;"
            ):
                depth -= 1
        if j > start and depth <= 0:
            return j + 1
        j += 1
    return len(lines)


def _shuffle_functions(source: str, rng: random.Random) -> str:
    lines = source.split("\n")
    func_ranges: list[tuple[int, int]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)local function (\w+)\(", lines[i])
        if not m:
            i += 1
            continue
        indent = m.group(1)
        name = m.group(2)
        if name == "__vm_run" or len(indent) != 4:
            i += 1
            continue
        start = i
        end = _find_function_end(lines, start)
        func_ranges.append((start, end))
        i = end

    if len(func_ranges) < 3:
        return source

    func_texts = []
    for start, end in func_ranges:
        func_texts.append("\n".join(lines[start:end]))

    shuffled_indices = list(range(len(func_texts)))
    rng.shuffle(shuffled_indices)
    shuffled_texts = [func_texts[i] for i in shuffled_indices]

    non_func_parts: list[str] = []
    pos = 0
    for start, end in func_ranges:
        if pos < start:
            non_func_parts.append("\n".join(lines[pos:start]))
        pos = end
    if pos < len(lines):
        non_func_parts.append("\n".join(lines[pos:]))

    result = non_func_parts[0] if non_func_parts else ""
    fi = 0
    for start, end in func_ranges:
        if fi < len(shuffled_texts):
            result += "\n" + shuffled_texts[fi]
            fi += 1
        else:
            result += "\n" + func_texts[fi - len(shuffled_texts)]
    for nfp in non_func_parts[1:]:
        result += "\n" + nfp

    return result


def _extract_constants(source: str, rng: random.Random) -> str:
    vm_run_start = source.find("local function __vm_run(")
    if vm_run_start < 0:
        return source

    top_source = source[:vm_run_start]
    vm_source = source[vm_run_start:]

    pattern = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
    matches = list(pattern.finditer(vm_source))
    if not matches:
        return source

    constants: list[str] = []
    const_map: dict[str, int] = {}
    for match in matches:
        inner = match.group(1)
        if len(inner) < 4:
            continue
        if inner.startswith("LVM") or inner.startswith("__"):
            continue
        if any(ord(ch) > 127 for ch in inner):
            continue
        if any(not (32 <= ord(ch) < 127) for ch in inner):
            continue
        if inner in _RESERVED_STRINGS:
            continue
        if inner not in const_map:
            const_map[inner] = len(constants)
            constants.append(inner)

    if len(constants) < 5:
        return source

    rng.shuffle(constants)
    key = rng.randint(1, 255)
    encoded_entries: list[str] = []
    for c in constants:
        enc = []
        for ch in c:
            enc.append(str((ord(ch) + key) % 256))
        encoded_entries.append("{" + ",".join(enc) + "}")

    arr_name = "_c" + "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=3))
    arr_init = f"    local {arr_name} = {{\n"
    chunk_size = 8
    for i in range(0, len(encoded_entries), chunk_size):
        chunk = encoded_entries[i : i + chunk_size]
        arr_init += (
            "        "
            + ",".join(f"[{i+j+1}]={chunk[j]}" for j in range(len(chunk)))
            + ",\n"
        )
    arr_init += "    }\n"

    decode_func = f'    local function _dc(t,k) local r="" for i=1,#t do r=r..__vm_string.char((t[i]-k)%256) end return r end\n'

    reverse_map: dict[int, int] = {}
    for new_idx, c in enumerate(constants):
        if c in const_map:
            reverse_map[const_map[c]] = new_idx

    replacements: list[tuple[int, int, str]] = []
    for match in matches:
        inner = match.group(1)
        if inner in const_map:
            new_idx = reverse_map[const_map[inner]]
            replacements.append(
                (match.start(), match.end(), f"_dc({arr_name}[{new_idx+1}],{key})")
            )

    if not replacements:
        return source

    parts: list[str] = []
    pos = 0
    for start, end, new_str in replacements:
        parts.append(vm_source[pos:start])
        parts.append(new_str)
        pos = end
    parts.append(vm_source[pos:])

    result = top_source + "".join(parts)

    insert_pat = re.compile(r"(    local __vm_string = __vm_G\.string\n)")
    insert_m = insert_pat.search(result)
    if not insert_m:
        return source
    insert_pos = insert_m.end()
    result = result[:insert_pos] + decode_func + arr_init + result[insert_pos:]
    return result


_OPAQUE_TEMPLATES_ALWAYS_TRUE = [
    lambda rng: f"({rng.randint(2, 100)} * {rng.randint(2, 100)} ~= 0)",
    lambda rng: f"({rng.randint(1, 50)} + {rng.randint(1, 50)} > 0)",
    lambda rng: f"(type(nil) ~= {repr(rng.choice(['number', 'string', 'table', 'function']))})",
]

_OPAQUE_TEMPLATES_ALWAYS_FALSE = [
    lambda rng: f"({rng.randint(2, 100)} * {rng.randint(2, 100)} == 0)",
    lambda rng: f"({rng.randint(1, 50)} + {rng.randint(1, 50)} < 0)",
    lambda rng: f"(type(nil) == {repr(rng.choice(['number', 'string', 'table', 'function']))})",
]


def _inject_opaque_predicates(source: str, rng: random.Random) -> str:
    lines = source.split("\n")
    insert_positions: list[int] = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if len(indent) == 4 and stripped.startswith("local function ") and i > 5:
            insert_positions.append(i)

    if len(insert_positions) < 3:
        return source

    chosen = rng.sample(insert_positions, min(4, len(insert_positions)))
    result_lines = list(lines)
    offset = 0
    for pos in sorted(chosen):
        true_cond = rng.choice(_OPAQUE_TEMPLATES_ALWAYS_TRUE)(rng)
        false_cond = rng.choice(_OPAQUE_TEMPLATES_ALWAYS_FALSE)(rng)
        junk_var = "_o" + "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=3))
        block = [
            "    do",
            f"        local {junk_var} = {true_cond} and {rng.randint(100, 999)} or nil",
            f"        if {false_cond} then {junk_var} = {junk_var} and {junk_var} + 1 end",
            "    end",
        ]
        for j, bl in enumerate(block):
            result_lines.insert(pos + offset + j, bl)
        offset += len(block)

    return "\n".join(result_lines)


def _compress_source(source: str, rng: random.Random) -> str:
    lines = source.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        if not stripped:
            i += 1
            continue

        if stripped.startswith("--"):
            if indent:
                i += 1
                continue
            result.append(line)
            i += 1
            continue

        if re.match(r"^if .+ then\s*$", stripped) and i + 2 < len(lines):
            body = lines[i + 1].lstrip()
            end_line = lines[i + 2].lstrip() if i + 2 < len(lines) else ""
            if (
                end_line == "end"
                and not body.startswith("if ")
                and not body.startswith("for ")
                and not body.startswith("while ")
                and not body.startswith("local function")
                and ";" not in body
            ):
                result.append(indent + stripped.rstrip() + " " + body + " end")
                i += 3
                continue

        if re.match(r"^for .+ do\s*$", stripped) and i + 2 < len(lines):
            body = lines[i + 1].lstrip()
            end_line = lines[i + 2].lstrip() if i + 2 < len(lines) else ""
            if (
                end_line == "end"
                and not body.startswith("if ")
                and not body.startswith("for ")
                and not body.startswith("while ")
                and not body.startswith("local function")
                and ";" not in body
            ):
                result.append(indent + stripped.rstrip() + " " + body + " end")
                i += 3
                continue

        if re.match(r"^while .+ do\s*$", stripped) and i + 2 < len(lines):
            body = lines[i + 1].lstrip()
            end_line = lines[i + 2].lstrip() if i + 2 < len(lines) else ""
            if (
                end_line == "end"
                and not body.startswith("if ")
                and not body.startswith("for ")
                and not body.startswith("while ")
                and not body.startswith("local function")
                and ";" not in body
            ):
                result.append(indent + stripped.rstrip() + " " + body + " end")
                i += 3
                continue

        result.append(line)
        i += 1

    return "\n".join(result)
