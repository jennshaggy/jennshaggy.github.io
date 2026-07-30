#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from pathlib import Path


ROM_OFFSET = 0xE80
ROM_SIZE = 0x131E
MASK32 = 0xFFFFFFFF


NAMES = {
    0x00: "halt",
    0x11: "mov",
    0x29: "rol",
    0x2A: "ror",
    0x2B: "shl",
    0x2C: "shr",
    0x3A: "li",
    0x52: "xor",
    0x53: "and",
    0x54: "or",
    0x6B: "mul",
    0x7C: "add",
    0x7D: "sub",
    0x80: "addi",
    0x90: "cmp",
    0xA0: "jmp",
    0xA1: "jz",
    0xA2: "jnz",
    0xC4: "load",
    0xC5: "store",
    0xC6: "rom",
    0xE0: "in",
    0xE1: "out",
}


def u32(value: int) -> int:
    return value & MASK32


def s32(value: int) -> int:
    value &= MASK32
    return value if value < 0x80000000 else value - 0x100000000


def ror32(value: int, count: int) -> int:
    count &= 31
    value &= MASK32
    if count == 0:
        return value
    return ((value >> count) | (value << (32 - count))) & MASK32


def rol32(value: int, count: int) -> int:
    return ror32(value, -count)


def fields(raw: bytes) -> tuple[int, int, int, int, int, int]:
    b0, b1, b2, opcode = raw
    imm = b0 | (b1 << 8)
    simm = struct.unpack("<h", raw[:2])[0]
    dst = b2 >> 4
    src1 = b2 & 0xF
    src2 = b0 & 0xF
    return opcode, imm, simm, dst, src1, src2


def render(pc: int, raw: bytes) -> str:
    opcode, imm, simm, dst, src1, src2 = fields(raw)
    name = NAMES.get(opcode, f"bad_{opcode:02x}")
    if opcode == 0x00:
        operands = ""
    elif opcode == 0x11:
        operands = f"r{dst}, r{src1}"
    elif opcode in (0x29, 0x2A, 0x2B, 0x2C):
        operands = f"r{dst}, r{src1}, {imm & 31}"
    elif opcode == 0x3A:
        operands = f"r{dst}, 0x{imm:04x}"
    elif opcode in (0x52, 0x53, 0x54, 0x6B, 0x7C, 0x7D):
        operands = f"r{dst}, r{src1}, r{src2}"
    elif opcode == 0x80:
        operands = f"r{dst}, r{src1}, 0x{imm:04x}"
    elif opcode == 0x90:
        operands = f"r{src1}, r{src2}"
    elif opcode in (0xA0, 0xA1, 0xA2):
        operands = f"{pc + 4 + simm:#06x} ({simm:+d})"
    elif opcode in (0xC4, 0xC6):
        operands = f"r{dst}, [r{src1} + 0x{imm:04x}]"
    elif opcode == 0xC5:
        operands = f"[r{src1} + 0x{imm:04x}], r{dst}"
    elif opcode == 0xE0:
        operands = f"r{dst}"
    elif opcode == 0xE1:
        operands = f"r{src1}"
    else:
        operands = f"raw={raw.hex()}"
    return f"{pc:04x}: {raw.hex(' '):11s}  {name:5s} {operands}".rstrip()


def linear_rows(rom: bytes) -> list[int]:
    """Recover the 32x32 byte-XOR matrix from the verified linear-layer code."""
    regs = [0] * 16
    memory = {index: 1 << index for index in range(32)}
    for pc in range(0x70, 0x1018, 4):
        raw = rom[pc : pc + 4]
        opcode, imm, _simm, dst, src1, src2 = fields(raw)
        if opcode == 0xC4:
            if src1 != 0:
                raise RuntimeError(f"unexpected indexed load in linear layer at {pc:#x}")
            regs[dst] = memory.get(imm, 0)
        elif opcode == 0x52:
            regs[dst] = regs[src1] ^ regs[src2]
        elif opcode == 0xC5:
            if src1 != 0:
                raise RuntimeError(f"unexpected indexed store in linear layer at {pc:#x}")
            memory[imm] = regs[dst]
        else:
            raise RuntimeError(
                f"unexpected opcode {opcode:#x} in linear layer at {pc:#x}"
            )
    return [memory[0x80 + index] for index in range(32)]


def invert_linear(rows: list[int], output: bytes) -> bytes:
    if len(rows) != 32 or len(output) != 32:
        raise ValueError("linear layer must be 32 by 32")
    augmented = [[rows[index], output[index]] for index in range(32)]
    pivot_row_for_column: dict[int, int] = {}
    row = 0
    for column in range(32):
        pivot = next(
            (candidate for candidate in range(row, 32)
             if (augmented[candidate][0] >> column) & 1),
            None,
        )
        if pivot is None:
            continue
        augmented[row], augmented[pivot] = augmented[pivot], augmented[row]
        for other in range(32):
            if other != row and ((augmented[other][0] >> column) & 1):
                augmented[other][0] ^= augmented[row][0]
                augmented[other][1] ^= augmented[row][1]
        pivot_row_for_column[column] = row
        row += 1
    if row != 32:
        raise RuntimeError(f"linear matrix is not invertible (rank {row})")
    return bytes(
        augmented[pivot_row_for_column[column]][1] for column in range(32)
    )


def solve(rom: bytes) -> tuple[bytes, bytes]:
    sbox = rom[0x10C4:0x11C4]
    keys_blob = rom[0x11C4:0x12E4]
    target = rom[0x12E4:0x1304]
    output_key = rom[0x1304:0x131E]
    if len(set(sbox)) != 256:
        raise RuntimeError("S-box is not a permutation")
    inverse_sbox = [0] * 256
    for index, value in enumerate(sbox):
        inverse_sbox[value] = index
    keys = [keys_blob[offset : offset + 32] for offset in range(0, 0x120, 32)]
    if len(keys) != 9 or any(len(key) != 32 for key in keys):
        raise RuntimeError("unexpected round-key layout")

    rows = linear_rows(rom)
    state = bytes(target)
    for round_number in range(8, 0, -1):
        state = bytes(left ^ right for left, right in zip(state, keys[round_number]))
        state = invert_linear(rows, state)
        state = bytes(inverse_sbox[value] for value in state)
    accepted_input = bytes(left ^ right for left, right in zip(state, keys[0]))
    flag = bytes(
        accepted_input[index] ^ output_key[index]
        for index in range(len(output_key))
    )
    return accepted_input, flag


class VM:
    def __init__(self, rom: bytes, input_data: bytes):
        self.rom = rom
        self.input_data = input_data[:0x1000]
        self.input_pos = 0
        self.regs = [0] * 16
        self.memory = bytearray(0x10000)
        self.zero = False
        self.pc = 0
        self.output = bytearray()
        self.steps = 0

    def reg(self, index: int) -> int:
        return self.regs[index] & MASK32

    def set_reg(self, index: int, value: int) -> None:
        self.regs[index] = value & MASK32

    def run(self, max_steps: int = 10_000_000, trace: bool = False) -> bytes:
        while self.steps < max_steps:
            if not 0 <= self.pc <= len(self.rom) - 4:
                raise RuntimeError(f"PC outside ROM: {self.pc:#x}")
            raw = self.rom[self.pc : self.pc + 4]
            opcode, imm, simm, dst, src1, src2 = fields(raw)
            next_pc = self.pc + 4
            self.steps += 1
            if trace:
                print(render(self.pc, raw))

            if opcode == 0x00:
                return bytes(self.output)
            if opcode == 0x11:
                self.set_reg(dst, self.reg(src1))
            elif opcode == 0x29:
                self.set_reg(dst, rol32(self.reg(src1), imm))
            elif opcode == 0x2A:
                self.set_reg(dst, ror32(self.reg(src1), imm))
            elif opcode == 0x2B:
                self.set_reg(dst, self.reg(src1) << (imm & 31))
            elif opcode == 0x2C:
                self.set_reg(dst, self.reg(src1) >> (imm & 31))
            elif opcode == 0x3A:
                self.set_reg(dst, imm)
            elif opcode == 0x52:
                result = self.reg(src1) ^ self.reg(src2)
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x53:
                result = self.reg(src1) & self.reg(src2)
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x54:
                result = self.reg(src1) | self.reg(src2)
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x6B:
                result = u32(s32(self.reg(src1)) * s32(self.reg(src2)))
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x7C:
                result = u32(s32(self.reg(src1)) + s32(self.reg(src2)))
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x7D:
                result = u32(s32(self.reg(src1)) - s32(self.reg(src2)))
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x80:
                result = u32(self.reg(src1) + imm)
                self.set_reg(dst, result)
                self.zero = result == 0
            elif opcode == 0x90:
                self.zero = s32(self.reg(src1)) == s32(self.reg(src2))
            elif opcode == 0xA0:
                next_pc += simm
            elif opcode == 0xA1:
                if self.zero:
                    next_pc += simm
            elif opcode == 0xA2:
                if not self.zero:
                    next_pc += simm
            elif opcode == 0xC4:
                address = (imm + self.reg(src1)) & 0xFFFF
                self.set_reg(dst, self.memory[address])
            elif opcode == 0xC5:
                address = (imm + self.reg(src1)) & 0xFFFF
                self.memory[address] = self.reg(dst) & 0xFF
            elif opcode == 0xC6:
                address = (imm + self.reg(src1)) % len(self.rom)
                self.set_reg(dst, self.rom[address])
            elif opcode == 0xE0:
                if self.input_pos < len(self.input_data):
                    self.set_reg(dst, self.input_data[self.input_pos])
                    self.input_pos += 1
                    self.zero = False
                else:
                    self.set_reg(dst, 0)
                    self.zero = True
            elif opcode == 0xE1:
                self.output.append(self.reg(src1) & 0xFF)
            else:
                raise RuntimeError(f"bad opcode {opcode:#x} at {self.pc:#x}")
            self.pc = next_pc
        raise RuntimeError(f"step limit reached at PC {self.pc:#x}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--input", default="")
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--disassemble", action="store_true")
    parser.add_argument("--solve", action="store_true")
    args = parser.parse_args()

    blob = args.binary.read_bytes()
    rom = blob[ROM_OFFSET : ROM_OFFSET + ROM_SIZE]
    if len(rom) != ROM_SIZE:
        raise SystemExit("binary is too short for the verified ROM range")

    if args.disassemble:
        for pc in range(0, len(rom) - 3, 4):
            print(render(pc, rom[pc : pc + 4]))
        return
    if args.solve:
        accepted_input, flag = solve(rom)
        print(f"accepted_input_hex={accepted_input.hex()}")
        print(f"flag={flag.decode('utf-8', errors='backslashreplace')}")
        vm = VM(rom, accepted_input)
        output = vm.run()
        print(f"verified_output={output.decode('utf-8', errors='backslashreplace')}")
        print(f"verified_steps={vm.steps}")
        if output != flag:
            raise SystemExit("emulator verification failed")
        return

    input_data = (
        args.input_file.read_bytes()
        if args.input_file is not None
        else args.input.encode()
    )
    vm = VM(rom, input_data)
    output = vm.run(trace=args.trace)
    print(output.decode("utf-8", errors="backslashreplace"), end="")
    print(f"\n[steps={vm.steps} input={vm.input_pos} pc={vm.pc:#x}]")


if __name__ == "__main__":
    main()
