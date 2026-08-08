from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from luavm.compiler import compile_file, compile_tree
from luavm.lexer import CompileError


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile a Lua file or a mod directory into a self-contained custom VM"
    )
    parser.add_argument("input", help="source Lua file or directory")
    parser.add_argument("output", help="generated Lua file or destination directory")
    parser.add_argument(
        "--seed", type=int, help="deterministic obfuscation seed for tests"
    )
    parser.add_argument(
        "--source-name",
        help="logical source path reported by debug.getinfo (file mode only, defaults to input path)",
    )
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    try:
        if input_path.is_dir():
            compile_tree(args.input, args.output, seed=args.seed)
        else:
            compile_file(
                args.input, args.output, seed=args.seed, source_name=args.source_name
            )
    except (CompileError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
