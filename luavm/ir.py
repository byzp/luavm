from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .lexer import CompileError


@dataclass
class Instruction:
    op: str
    a: int = 0
    b: int = 0
    c: int = 0
    line: int = 0


@dataclass
class Prototype:
    name: str
    params: list[str]
    vararg: bool
    upvalues: list[tuple[int, int]]
    constants: list[Any]
    code: list[Instruction]
    local_names: list[tuple[str, int]] = field(default_factory=list)
    upvalue_names: list[str] = field(default_factory=list)
    dispatch_table: dict[int, int] = field(default_factory=dict)


OPS = [
    "NOP",
    "CONST",
    "LOAD_LOCAL",
    "STORE_LOCAL",
    "LOAD_UP",
    "STORE_UP",
    "LOAD_GLOBAL",
    "STORE_GLOBAL",
    "NEW_TABLE",
    "DUP",
    "POP",
    "GET_TABLE",
    "SET_TABLE",
    "SET_TABLE_KEEP",
    "STORE_TABLE_REF",
    "BINARY",
    "UNARY",
    "JUMP",
    "JUMP_IF_FALSE",
    "JUMP_IF_TRUE",
    "JUMP_IF_FALSE_KEEP",
    "JUMP_IF_TRUE_KEEP",
    "CALL",
    "CALL_METHOD",
    "RETURN",
    "MAKE_CLOSURE",
    "ADJUST",
    "LOAD_VARARG",
    "FOR_CHECK",
    "FOR_STEP",
    "NOISE",
    "CALL_MARK",
    "LOOP_BIND",
    "SET_TABLE_MULTI",
    "TAILCALL",
    "TAILCALL_METHOD",
    "DISPATCH",
    "SET_DISPATCH",
    "BRANCH_DISPATCH",
]
OP_IDS = {name: index for index, name in enumerate(OPS)}
MULTI_VALUE = 0xFFFF

BINARY_IDS = {
    "+": 1,
    "-": 2,
    "*": 3,
    "/": 4,
    "%": 5,
    "^": 6,
    "..": 7,
    "==": 8,
    "~=": 9,
    "<": 10,
    "<=": 11,
    ">": 12,
    ">=": 13,
}
UNARY_IDS = {"-": 1, "not": 2, "#": 3}


class CompileContext:
    def __init__(
        self,
        compiler: "ProgramCompiler",
        proto: Prototype,
        parent: Optional["CompileContext"] = None,
    ) -> None:
        self.compiler = compiler
        self.proto = proto
        self.parent = parent
        self.scopes: list[dict[str, int]] = [{}]
        self.next_slot = 0
        self.break_stack: list[list[int]] = []

    def emit(self, op: str, a: int = 0, b: int = 0, c: int = 0, line: int = 0) -> int:
        if op not in OP_IDS:
            raise CompileError(f"internal error: unknown opcode {op}")
        self.proto.code.append(Instruction(op, a, b, c, line))
        return len(self.proto.code) - 1

    def patch(
        self,
        index: int,
        a: Optional[int] = None,
        b: Optional[int] = None,
        c: Optional[int] = None,
    ) -> None:
        ins = self.proto.code[index]
        if a is not None:
            ins.a = a
        if b is not None:
            ins.b = b
        if c is not None:
            ins.c = c

    def push_scope(self) -> None:
        self.scopes.append({})

    def pop_scope(self) -> None:
        if len(self.scopes) == 1:
            raise CompileError("internal error: cannot pop function scope")
        self.scopes.pop()

    def reserve(self, count: int = 1) -> int:
        first = self.next_slot
        self.next_slot += count
        return first

    def bind(self, name: str, slot: Optional[int] = None) -> int:
        slot = self.reserve() if slot is None else slot
        self.scopes[-1][name] = slot
        self.proto.local_names.append((name, slot))
        return slot

    def find_local(self, name: str) -> Optional[int]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def capture_for_child(self, name: str) -> Optional[tuple[str, int]]:
        local = self.find_local(name)
        if local is not None:
            return ("local", local)
        if self.parent is not None:
            parent_ref = self.parent.capture_for_child(name)
            if parent_ref is not None:
                if parent_ref[0] == "local":
                    return ("up", self.add_upvalue(0, parent_ref[1], name))
                return ("up", self.add_upvalue(1, parent_ref[1], name))
        return None

    def add_upvalue(self, kind: int, index: int, name: Optional[str] = None) -> int:
        descriptor = (kind, index)
        try:
            position = self.proto.upvalues.index(descriptor)
            if name and position < len(self.proto.upvalue_names):
                self.proto.upvalue_names[position] = name
            return position
        except ValueError:
            self.proto.upvalues.append(descriptor)
            self.proto.upvalue_names.append(
                name or ("upvalue" + str(len(self.proto.upvalues)))
            )
            return len(self.proto.upvalues) - 1

    def resolve(self, name: str) -> tuple[str, Any]:
        local = self.find_local(name)
        if local is not None:
            return ("local", local)
        if self.parent is not None:
            parent_ref = self.parent.capture_for_child(name)
            if parent_ref is not None:
                if parent_ref[0] == "local":
                    return ("up", self.add_upvalue(0, parent_ref[1], name))
                return ("up", self.add_upvalue(1, parent_ref[1], name))
        return ("global", name)


class ProgramCompiler:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.prototypes: list[Prototype] = []

    def new_proto(
        self, name: str, params: list[str], vararg: bool
    ) -> tuple[Prototype, CompileContext]:
        proto = Prototype(name, params, vararg, [], [], [])
        self.prototypes.append(proto)
        ctx = CompileContext(self, proto)
        for param in params:
            ctx.bind(param)
        return proto, ctx

    def compile(self, body: list[tuple]) -> list[Prototype]:
        _, ctx = self.new_proto(self.filename, [], True)
        self.compile_block(ctx, body)
        if not ctx.proto.code or ctx.proto.code[-1].op != "RETURN":
            ctx.emit("RETURN", 0, line=body[-1][1] if body else 1)
        return self.prototypes

    def compile_block(self, ctx: CompileContext, body: list[tuple]) -> None:
        for statement in body:
            self.compile_statement(ctx, statement)

    def compile_statement(self, ctx: CompileContext, statement: tuple) -> None:
        kind, line = statement[0], statement[1]
        if kind == "nop":
            ctx.emit("NOP", line=line)
        elif kind == "local":
            _, _, names, values = statement
            slots = [ctx.reserve() for _ in names]
            if values:
                self.compile_value_list(ctx, values, len(names), line)
                for slot in reversed(slots):
                    ctx.emit("STORE_LOCAL", slot, line=line)
            for name, slot in zip(names, slots):
                ctx.bind(name, slot)
        elif kind == "local_function":
            _, _, name, params, vararg, body = statement
            slot = ctx.bind(name)
            proto_id = self.compile_function(ctx, name, params, vararg, body, line)
            ctx.emit("MAKE_CLOSURE", proto_id, line=line)
            ctx.emit("STORE_LOCAL", slot, line=line)
        elif kind == "function":
            _, _, target, params, vararg, body = statement
            self.compile_assignment(
                ctx, [target], [("function_expr", line, params, vararg, body)], line
            )
        elif kind == "assign":
            _, _, targets, values = statement
            self.compile_assignment(ctx, targets, values, line)
        elif kind == "callstmt":
            self.compile_expr(ctx, statement[2], expected=0)
        elif kind == "return":
            values = statement[2]
            if not values:
                ctx.emit("RETURN", 0, line=line)
            elif len(values) == 1 and values[0][0] in {"call", "methodcall"}:
                self.compile_tail_call(ctx, values[0], line)
            else:
                multi = self.compile_return_values(ctx, values, line)
                ctx.emit("RETURN", MULTI_VALUE if multi else len(values), line=line)
        elif kind == "if":
            _, _, branches, else_body = statement
            end_jumps: list[int] = []
            for condition, body in branches:
                self.compile_expr(ctx, condition, expected=1)
                false_jump = ctx.emit("JUMP_IF_FALSE", 0, line=condition[1])
                ctx.push_scope()
                self.compile_block(ctx, body)
                ctx.pop_scope()
                end_jumps.append(ctx.emit("JUMP", 0, line=line))
                ctx.patch(false_jump, a=len(ctx.proto.code))
            if else_body:
                ctx.push_scope()
                self.compile_block(ctx, else_body)
                ctx.pop_scope()
            end = len(ctx.proto.code)
            for jump in end_jumps:
                ctx.patch(jump, a=end)
        elif kind == "while":
            _, _, condition, body = statement
            start = len(ctx.proto.code)
            self.compile_expr(ctx, condition, expected=1)
            exit_jump = ctx.emit("JUMP_IF_FALSE", 0, line=condition[1])
            breaks: list[int] = []
            ctx.break_stack.append(breaks)
            body_start_slot = ctx.next_slot
            ctx.push_scope()
            body_bind = ctx.emit("LOOP_BIND", body_start_slot, 0, line=line)
            self.compile_block(ctx, body)
            ctx.pop_scope()
            ctx.patch(body_bind, b=ctx.next_slot - body_start_slot)
            ctx.break_stack.pop()
            ctx.emit("JUMP", start, line=line)
            exit_target = len(ctx.proto.code)
            ctx.patch(exit_jump, a=exit_target)
            for jump in breaks:
                ctx.patch(jump, a=exit_target)
        elif kind == "repeat":
            _, _, body, condition = statement
            start = len(ctx.proto.code)
            breaks: list[int] = []
            ctx.break_stack.append(breaks)
            body_start_slot = ctx.next_slot
            ctx.push_scope()
            body_bind = ctx.emit("LOOP_BIND", body_start_slot, 0, line=line)
            self.compile_block(ctx, body)
            self.compile_expr(ctx, condition, expected=1)
            ctx.pop_scope()
            ctx.patch(body_bind, b=ctx.next_slot - body_start_slot)
            ctx.break_stack.pop()
            ctx.emit("JUMP_IF_FALSE", start, line=condition[1])
            exit_target = len(ctx.proto.code)
            for jump in breaks:
                ctx.patch(jump, a=exit_target)
        elif kind == "for_num":
            self.compile_numeric_for(ctx, statement)
        elif kind == "for_in":
            self.compile_generic_for(ctx, statement)
        elif kind == "do":
            ctx.push_scope()
            self.compile_block(ctx, statement[2])
            ctx.pop_scope()
        elif kind == "break":
            if not ctx.break_stack:
                raise CompileError(f"{self.filename}:{line}: break outside loop")
            ctx.break_stack[-1].append(ctx.emit("JUMP", 0, line=line))
        else:
            raise CompileError(f"{self.filename}:{line}: unsupported statement {kind}")

    def compile_numeric_for(self, ctx: CompileContext, statement: tuple) -> None:
        _, line, name, start, limit, step, body = statement
        ctx.push_scope()
        index_slot = ctx.reserve()
        limit_slot = ctx.reserve()
        step_slot = ctx.reserve()
        self.compile_expr(ctx, start, expected=1)
        ctx.emit("STORE_LOCAL", index_slot, line=line)
        self.compile_expr(ctx, limit, expected=1)
        ctx.emit("STORE_LOCAL", limit_slot, line=line)
        self.compile_expr(ctx, step, expected=1)
        ctx.emit("STORE_LOCAL", step_slot, line=line)
        ctx.scopes[-1][name] = index_slot
        ctx.proto.local_names.append((name, index_slot))
        start_pc = len(ctx.proto.code)
        ctx.emit("FOR_CHECK", index_slot, limit_slot, step_slot, line=line)
        exit_jump = ctx.emit("JUMP_IF_FALSE", 0, line=line)
        breaks: list[int] = []
        ctx.break_stack.append(breaks)
        body_start_slot = ctx.next_slot
        ctx.push_scope()
        body_bind = ctx.emit("LOOP_BIND", body_start_slot, 0, line=line)
        self.compile_block(ctx, body)
        ctx.pop_scope()
        ctx.patch(body_bind, b=ctx.next_slot - body_start_slot)
        ctx.break_stack.pop()
        ctx.emit("FOR_STEP", index_slot, step_slot, line=line)
        ctx.emit("JUMP", start_pc, line=line)
        exit_target = len(ctx.proto.code)
        ctx.patch(exit_jump, a=exit_target)
        for jump in breaks:
            ctx.patch(jump, a=exit_target)
        ctx.pop_scope()

    def compile_generic_for(self, ctx: CompileContext, statement: tuple) -> None:
        _, line, names, expressions, body = statement
        ctx.push_scope()
        iterator_slot = ctx.reserve()
        state_slot = ctx.reserve()
        control_slot = ctx.reserve()
        value_slots = [ctx.reserve() for _ in names]
        self.compile_value_list(ctx, expressions, 3, line)
        for slot in (control_slot, state_slot, iterator_slot):
            ctx.emit("STORE_LOCAL", slot, line=line)
        for name, slot in zip(names, value_slots):
            ctx.bind(name, slot)
        start_pc = len(ctx.proto.code)
        ctx.emit("LOAD_LOCAL", iterator_slot, line=line)
        ctx.emit("LOAD_LOCAL", state_slot, line=line)
        ctx.emit("LOAD_LOCAL", control_slot, line=line)
        ctx.emit("CALL", 2, MULTI_VALUE, line=line)
        self.emit_adjust(ctx, len(value_slots), line)
        ctx.emit("LOOP_BIND", value_slots[0], len(value_slots), line=line)
        for slot in reversed(value_slots):
            ctx.emit("STORE_LOCAL", slot, line=line)
        ctx.emit("LOAD_LOCAL", value_slots[0], line=line)
        exit_jump = ctx.emit("JUMP_IF_FALSE", 0, line=line)
        ctx.emit("LOAD_LOCAL", value_slots[0], line=line)
        ctx.emit("STORE_LOCAL", control_slot, line=line)
        breaks: list[int] = []
        ctx.break_stack.append(breaks)
        body_start_slot = ctx.next_slot
        ctx.push_scope()
        body_bind = ctx.emit("LOOP_BIND", body_start_slot, 0, line=line)
        self.compile_block(ctx, body)
        ctx.pop_scope()
        ctx.patch(body_bind, b=ctx.next_slot - body_start_slot)
        ctx.break_stack.pop()
        ctx.emit("JUMP", start_pc, line=line)
        exit_target = len(ctx.proto.code)
        ctx.patch(exit_jump, a=exit_target)
        for jump in breaks:
            ctx.patch(jump, a=exit_target)
        ctx.pop_scope()

    def compile_assignment(
        self, ctx: CompileContext, targets: list[tuple], values: list[tuple], line: int
    ) -> None:
        refs: list[tuple] = []
        for target in targets:
            if target[0] == "index":
                table_slot = ctx.reserve()
                key_slot = ctx.reserve()
                self.compile_expr(ctx, target[2], expected=1)
                ctx.emit("STORE_LOCAL", table_slot, line=target[1])
                self.compile_expr(ctx, target[3], expected=1)
                ctx.emit("STORE_LOCAL", key_slot, line=target[1])
                refs.append(("table", table_slot, key_slot))
            elif target[0] == "name":
                refs.append(("name", target[2]))
            else:
                raise CompileError(
                    f"{self.filename}:{target[1]}: invalid assignment target"
                )
        self.compile_value_list(ctx, values, len(targets), line)
        for ref in reversed(refs):
            if ref[0] == "table":
                ctx.emit("STORE_TABLE_REF", ref[1], ref[2], line=line)
            else:
                kind, index = ctx.resolve(ref[1])
                op = {
                    "local": "STORE_LOCAL",
                    "up": "STORE_UP",
                    "global": "STORE_GLOBAL",
                }[kind]
                if kind == "global":
                    index = (
                        ctx.proto.constants.index(ref[1])
                        if ref[1] in ctx.proto.constants
                        else self.add_constant(ctx.proto, ref[1])
                    )
                ctx.emit(op, int(index), line=line)

    def compile_value_list(
        self, ctx: CompileContext, values: list[tuple], count: int, line: int
    ) -> None:
        if not values:
            for _ in range(count):
                ctx.emit("CONST", self.add_constant(ctx.proto, None), line=line)
            return
        for value in values[:-1]:
            self.compile_expr(ctx, value, expected=1)
        last = values[-1]
        self.compile_expr(
            ctx, last, expected=MULTI_VALUE if self.is_multi_value(last) else 1
        )
        self.emit_adjust(ctx, count, line)

    def compile_return_values(
        self, ctx: CompileContext, values: list[tuple], line: int
    ) -> bool:
        for value in values[:-1]:
            self.compile_expr(ctx, value, expected=1)
        last = values[-1]
        multi = self.is_multi_value(last)
        self.compile_expr(ctx, last, expected=MULTI_VALUE if multi else 1)
        return multi

    def compile_tail_call(self, ctx: CompileContext, node: tuple, line: int) -> None:
        kind = node[0]
        if kind == "call":
            arguments = node[3]
            variable_arguments = bool(arguments) and self.is_multi_value(arguments[-1])
            if variable_arguments:
                ctx.emit("CALL_MARK", line=line)
            self.compile_expr(ctx, node[2], expected=1)
            for argument in arguments[:-1] if variable_arguments else arguments:
                self.compile_expr(ctx, argument, expected=1)
            if variable_arguments:
                self.compile_expr(ctx, arguments[-1], expected=MULTI_VALUE)
            ctx.emit(
                "TAILCALL",
                MULTI_VALUE if variable_arguments else len(arguments),
                line=line,
            )
            return
        if kind == "methodcall":
            arguments = node[4]
            variable_arguments = bool(arguments) and self.is_multi_value(arguments[-1])
            if variable_arguments:
                ctx.emit("CALL_MARK", line=line)
            self.compile_expr(ctx, node[2], expected=1)
            for argument in arguments[:-1] if variable_arguments else arguments:
                self.compile_expr(ctx, argument, expected=1)
            if variable_arguments:
                self.compile_expr(ctx, arguments[-1], expected=MULTI_VALUE)
            key = self.add_constant(ctx.proto, node[3])
            ctx.emit(
                "TAILCALL_METHOD",
                MULTI_VALUE if variable_arguments else len(arguments),
                c=key,
                line=line,
            )
            return
        raise CompileError(f"{self.filename}:{line}: invalid tail call")

    @staticmethod
    def is_multi_value(node: tuple) -> bool:
        return node[0] in {"call", "methodcall", "vararg"}

    def emit_adjust(self, ctx: CompileContext, count: int, line: int) -> None:
        ctx.emit("ADJUST", count, line=line)

    def compile_function(
        self,
        parent: CompileContext,
        name: str,
        params: list[str],
        vararg: bool,
        body: list[tuple],
        line: int,
    ) -> int:
        proto = Prototype(name, params, vararg, [], [], [])
        self.prototypes.append(proto)
        ctx = CompileContext(self, proto, parent)
        for param in params:
            ctx.bind(param)
        self.compile_block(ctx, body)
        if not ctx.proto.code or ctx.proto.code[-1].op != "RETURN":
            ctx.emit("RETURN", 0, line=line)
        return self.prototypes.index(proto)

    def compile_expr(self, ctx: CompileContext, node: tuple, expected: int = 1) -> None:
        kind, line = node[0], node[1]
        if kind == "literal":
            ctx.emit("CONST", self.add_constant(ctx.proto, node[2]), line=line)
        elif kind == "paren":
            self.compile_expr(ctx, node[2], expected=1)
        elif kind == "name":
            ref, index = ctx.resolve(node[2])
            op = {"local": "LOAD_LOCAL", "up": "LOAD_UP", "global": "LOAD_GLOBAL"}[ref]
            if ref == "global":
                index = self.add_constant(ctx.proto, index)
            ctx.emit(op, int(index), line=line)
        elif kind == "vararg":
            ctx.emit("LOAD_VARARG", expected, line=line)
        elif kind == "table":
            ctx.emit("NEW_TABLE", line=line)
            fields = node[2]
            for field_index, (key, value, is_list) in enumerate(fields):
                is_tail_multi = (
                    field_index == len(fields) - 1
                    and is_list
                    and self.is_multi_value(value)
                )
                if is_tail_multi:
                    ctx.emit("CALL_MARK", line=line)
                    self.compile_expr(ctx, value, expected=MULTI_VALUE)
                    start_index = key[2]
                    if not 0 <= start_index <= 0xFFFF:
                        raise CompileError(
                            f"{self.filename}:{line}: table array index is too large"
                        )
                    ctx.emit("SET_TABLE_MULTI", start_index, line=line)
                else:
                    ctx.emit("DUP", line=line)
                    self.compile_expr(ctx, key, expected=1)
                    self.compile_expr(ctx, value, expected=1)
                    ctx.emit("SET_TABLE_KEEP", line=line)
        elif kind == "function_expr":
            _, _, params, vararg, body = node
            proto_id = self.compile_function(
                ctx, "<anonymous>", params, vararg, body, line
            )
            ctx.emit("MAKE_CLOSURE", proto_id, line=line)
        elif kind == "index":
            self.compile_expr(ctx, node[2], expected=1)
            self.compile_expr(ctx, node[3], expected=1)
            ctx.emit("GET_TABLE", line=line)
        elif kind == "call":
            variable_arguments = bool(node[3]) and self.is_multi_value(node[3][-1])
            if variable_arguments:
                ctx.emit("CALL_MARK", line=line)
            self.compile_expr(ctx, node[2], expected=1)
            for argument in node[3][:-1] if variable_arguments else node[3]:
                self.compile_expr(ctx, argument, expected=1)
            if variable_arguments:
                self.compile_expr(ctx, node[3][-1], expected=MULTI_VALUE)
            ctx.emit(
                "CALL",
                MULTI_VALUE if variable_arguments else len(node[3]),
                expected,
                line=line,
            )
        elif kind == "methodcall":
            variable_arguments = bool(node[4]) and self.is_multi_value(node[4][-1])
            if variable_arguments:
                ctx.emit("CALL_MARK", line=line)
            self.compile_expr(ctx, node[2], expected=1)
            for argument in node[4][:-1] if variable_arguments else node[4]:
                self.compile_expr(ctx, argument, expected=1)
            if variable_arguments:
                self.compile_expr(ctx, node[4][-1], expected=MULTI_VALUE)
            key = self.add_constant(ctx.proto, node[3])
            ctx.emit(
                "CALL_METHOD",
                MULTI_VALUE if variable_arguments else len(node[4]),
                expected,
                key,
                line=line,
            )
        elif kind == "binop":
            op = node[2]
            if op == "and":
                self.compile_expr(ctx, node[3], expected=1)
                jump = ctx.emit("JUMP_IF_FALSE_KEEP", 0, line=line)
                ctx.emit("POP", line=line)
                self.compile_expr(ctx, node[4], expected=expected)
                ctx.patch(jump, a=len(ctx.proto.code))
            elif op == "or":
                self.compile_expr(ctx, node[3], expected=1)
                jump = ctx.emit("JUMP_IF_TRUE_KEEP", 0, line=line)
                ctx.emit("POP", line=line)
                self.compile_expr(ctx, node[4], expected=expected)
                ctx.patch(jump, a=len(ctx.proto.code))
            else:
                self.compile_expr(ctx, node[3], expected=1)
                self.compile_expr(ctx, node[4], expected=1)
                ctx.emit("BINARY", BINARY_IDS[op], line=line)
        elif kind == "unop":
            self.compile_expr(ctx, node[3], expected=1)
            ctx.emit("UNARY", UNARY_IDS[node[2]], line=line)
        else:
            raise CompileError(f"{self.filename}:{line}: unsupported expression {kind}")

    @staticmethod
    def add_constant(proto: Prototype, value: Any) -> int:
        key = (type(value).__name__, value)
        for index, current in enumerate(proto.constants):
            if (type(current).__name__, current) == key:
                return index
        proto.constants.append(value)
        return len(proto.constants) - 1


def compile_source(source: str, filename: str = "<source>") -> list[Prototype]:
    from .parser import parse_source as _parse_source

    tree = _parse_source(source, filename)
    compiler = ProgramCompiler(filename)
    return compiler.compile(tree)
