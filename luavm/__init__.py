"""Single-file custom Lua VM prototype."""

from .compiler import CompileError, compile_file, compile_tree
from .emit import emit_lua
from .ir import Prototype, compile_source

__all__ = ["CompileError", "compile_file", "compile_source", "compile_tree", "emit_lua"]
