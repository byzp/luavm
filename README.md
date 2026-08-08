# LUAVM

- Virtual Machine Protection for LUA 5.1, Compatible with Don’t Starve Together
- A two-layer VM. The outer VM handles decoding, verification, and internal scheduling; the inner VM interprets custom instruction sets. It supports single-file encryption and maintains consistent external behavior. It includes flat control flow obfuscation, dead code obfuscation, and opaque predicate obfuscation. Do not use it for performance-intensive applications.

## how to use

```bash
python3 main.py in.lua out.lua
```

```bash
python3 main.py dir outdir
```
