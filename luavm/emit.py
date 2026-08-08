from __future__ import annotations

import base64
import json
import random
from pathlib import Path
from typing import Optional

from .ir import Prototype
from .lexer import CompileError
from .obfuscate_outer import _obfuscate_outer_vm
from .serialize import _obfuscate_payload, serialize_program
from .transform import (
    _flatten_control_flow,
    _inject_canary_constants,
    _inject_dead_blocks,
    _inject_noise,
    verify_program,
)


def _lua_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def emit_lua(
    prototypes: list[Prototype],
    source_name: str,
    *,
    seed: Optional[int] = None,
    page_size: int = 49152,
) -> str:
    if page_size < 256:
        raise ValueError("page_size must be at least 256")
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    seed_const = rng.randrange(1, 0x7FFFFFFF)
    opcode_perm = list(range(39))
    rng.shuffle(opcode_perm)
    header_key = bytes(rng.randrange(256) for _ in range(90))
    prototypes = _inject_noise(prototypes, rng)
    prototypes = _inject_canary_constants(prototypes, rng)
    prototypes = _inject_dead_blocks(prototypes, rng)
    prototypes = _flatten_control_flow(prototypes, rng)
    verify_program(prototypes)
    payload = serialize_program(prototypes, opcode_perm=opcode_perm, seed=seed_const)
    encrypted, checksum = _obfuscate_payload(
        payload, seed_const, opcode_perm, header_key
    )
    encoded = base64.b64encode(encrypted).decode("ascii")
    pages = [encoded[i : i + page_size] for i in range(0, len(encoded), page_size)] or [
        ""
    ]
    template = (
        Path(__file__).with_name("runtime_template.lua").read_text(encoding="utf-8")
    )
    page_literal = "{" + ",".join(_lua_quote(page) for page in pages) + "}"
    header_key_literal = "{" + ",".join(str(b) for b in header_key) + "}"
    replacements = {
        "@@HEADER_KEY@@": header_key_literal,
        "@@SOURCE@@": _lua_quote(source_name),
        "@@PAGES@@": page_literal,
    }
    for marker, replacement in replacements.items():
        template = template.replace(marker, replacement)
    if "@@" in template:
        raise CompileError("runtime template contains an unreplaced placeholder")
    template = _obfuscate_outer_vm(template, rng)
    return template
