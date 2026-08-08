from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from .emit import emit_lua
from .ir import Prototype, compile_source
from .lexer import CompileError


def compile_file(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    *,
    seed: Optional[int] = None,
    source_name: Optional[str] = None,
) -> None:
    source_path = Path(input_path)
    source = source_path.read_text(encoding="utf-8")
    display_name = source_name if source_name is not None else str(source_path)
    prototypes = compile_source(source, display_name)
    output = emit_lua(prototypes, display_name, seed=seed)
    Path(output_path).write_text(output, encoding="utf-8", newline="\n")


def compile_tree(
    input_root: str | os.PathLike[str],
    output_root: str | os.PathLike[str],
    *,
    seed: Optional[int] = None,
    copy_non_lua: bool = True,
) -> list[Path]:
    source_root = Path(input_root)
    destination_root = Path(output_root)
    if not source_root.is_dir():
        raise OSError(f"input root is not a directory: {source_root}")
    generated: list[Path] = []
    source_files = sorted(path for path in source_root.rglob("*") if path.is_file())
    for index, source_path in enumerate(source_files):
        relative = source_path.relative_to(source_root)
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source_path.suffix.lower() == ".lua" and source_path.name != "modinfo.lua":
            file_seed = None if seed is None else seed + index
            compile_file(
                source_path,
                destination,
                seed=file_seed,
                source_name=relative.as_posix(),
            )
            generated.append(destination)
        elif copy_non_lua:
            shutil.copyfile(source_path, destination)
    return generated
