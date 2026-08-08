from __future__ import annotations

import struct

from .ir import Instruction, OP_IDS, Prototype
from .lexer import CompileError


def _u16(value: int) -> bytes:
    if not 0 <= value <= 0xFFFF:
        raise CompileError(f"value {value} does not fit in u16")
    return struct.pack(">H", value)


def _u32(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise CompileError(f"value {value} does not fit in u32")
    return struct.pack(">I", value)


def _text(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return _u32(len(encoded)) + encoded


def _keystream(seed: int, checksum: int, length: int) -> bytes:
    s1 = seed % 2147483647
    if s1 == 0:
        s1 = 1
    s2 = (checksum * 48271 + seed * 69621) % 2147483647
    if s2 == 0:
        s2 = 1
    out = bytearray(length)
    for i in range(length):
        s1 = (s1 * 16807) % 2147483647
        s2 = (s2 * 48271) % 2147483647
        out[i] = ((s1 >> 24) + (s2 >> 24)) & 0xFF
    return bytes(out)


def _dispatch_keystream(seed: int, entry_count: int) -> bytes:
    s1 = (seed ^ 0x5A5A5A5A) % 2147483647
    if s1 == 0:
        s1 = 1
    s2 = (seed ^ 0x3C3C3C3C) % 2147483647
    if s2 == 0:
        s2 = 1
    out = bytearray(entry_count)
    for i in range(entry_count):
        s1 = (s1 * 16807) % 2147483647
        s2 = (s2 * 48271) % 2147483647
        out[i] = ((s1 >> 24) + (s2 >> 24)) & 0xFF
    return bytes(out)


def serialize_program(
    prototypes: list[Prototype], opcode_perm: list[int] | None = None, seed: int = 0
) -> bytes:
    if not prototypes:
        raise CompileError("program has no root prototype")
    if opcode_perm is None:
        opcode_perm = list(range(39))
    output = bytearray(b"LVM1")
    output.append(4)
    output.extend(_u16(len(prototypes)))
    for proto in prototypes:
        output.extend(_text(""))
        output.extend(_u16(len(proto.params)))
        output.append(1 if proto.vararg else 0)
        output.extend(_u16(len(proto.upvalues)))
        for kind, index in proto.upvalues:
            output.append(kind)
            output.extend(_u16(index))
        output.extend(_u16(len(proto.local_names)))
        for name, slot in proto.local_names:
            output.extend(_u16(slot))
        output.extend(_u16(len(proto.constants)))
        for value in proto.constants:
            if value is None:
                output.append(0)
            elif isinstance(value, bool):
                output.append(1)
                output.append(1 if value else 0)
            elif isinstance(value, (int, float)):
                output.append(2)
                output.extend(_text(repr(value)))
            elif isinstance(value, str):
                output.append(3)
                output.extend(_text(value))
            else:
                raise CompileError(f"unsupported constant type {type(value).__name__}")
        output.extend(_u32(len(proto.code)))
        for instruction in proto.code:
            if (
                not 0 <= instruction.a <= 0xFFFF
                or not 0 <= instruction.b <= 0xFFFF
                or not 0 <= instruction.c <= 0xFFFF
            ):
                raise CompileError(f"instruction operand out of range in {proto.name}")
            if not 0 <= instruction.line <= 0xFFFF:
                raise CompileError(f"source line out of range in {proto.name}")
            raw_op = opcode_perm[OP_IDS[instruction.op]]
            output.extend(
                struct.pack(
                    ">BHHHH",
                    raw_op,
                    instruction.a,
                    instruction.b,
                    instruction.c,
                    instruction.line,
                )
            )
        dispatch_table = proto.dispatch_table
        output.extend(_u16(len(dispatch_table)))
        dk = _dispatch_keystream(seed, len(dispatch_table))
        for idx, (block_id, start_pc) in enumerate(sorted(dispatch_table.items())):
            output.extend(_u16(block_id))
            output.extend(_u16(start_pc ^ ((dk[idx] << 8) | dk[idx])))
    return bytes(output)


HEADER_SIZE = 90
HEADER_MAGIC = b"LVMH"


def _build_header(seed: int, opcode_perm: list[int], checksum: int) -> bytes:
    header = bytearray(HEADER_MAGIC)
    header.extend(_u32(seed))
    for op in opcode_perm:
        header.extend(_u16(op))
    header.extend(_u32(checksum))
    assert len(header) == HEADER_SIZE
    return bytes(header)


def _encrypt_header(header: bytes, header_key: bytes) -> bytes:
    return bytes(
        header[i] ^ header_key[i % len(header_key)] for i in range(len(header))
    )


def _obfuscate_payload(
    payload: bytes, seed: int, opcode_perm: list[int], header_key: bytes
) -> tuple[bytes, int]:
    checksum = sum(payload) % 4294967296
    header = _build_header(seed, opcode_perm, checksum)
    encrypted_header = _encrypt_header(header, header_key)
    prng_seed = (checksum ^ seed) % 2147483647
    if prng_seed == 0:
        prng_seed = 1
    keystream = _keystream(prng_seed, checksum, len(payload))
    encrypted_body = bytes(payload[i] ^ keystream[i] for i in range(len(payload)))
    return encrypted_header + encrypted_body, checksum
