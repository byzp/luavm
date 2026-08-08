-- Virtual Machine Protection for LUA 5.1, https://github.com/byzp/luavm
-- LUAVM generated file: DO NOT EDIT!
local __VM_HEADER_KEY = @@HEADER_KEY@@
local __VM_SOURCE = @@SOURCE@@
local __VM_PAGES = @@PAGES@@
local function __vm_run(__vm_pages, __vm_source, ...)
    local __vm_G, __vm_env
    if getfenv then __vm_G, __vm_env = _G, getfenv(1) else __vm_G, __vm_env = GLOBAL, GLOBAL.getfenv(1) end
    local _G2 = __vm_env
    local __vm_select, __vm_unpack_fn, __vm_string = __vm_G.select, __vm_G.unpack, __vm_G.string
    local __vm_math, __vm_tonumber, __vm_error, __vm_tostring, __vm_table, __vm_type = __vm_G.math, __vm_G.tonumber, __vm_G.error, __vm_G.tostring, __vm_G.table, __vm_G.type
    local __vm_pcall, __vm_getmetatable, __vm_setmetatable, __vm_rawget, __vm_rawset = __vm_G.pcall, __vm_G.getmetatable, __vm_G.setmetatable, __vm_G.rawget, __vm_G.rawset
    local __vm_next, __vm_ipairs, __vm_pairs, __vm_getfenv, __vm_setfenv = __vm_G.next, __vm_G.ipairs, __vm_G.pairs, __vm_G.getfenv, __vm_G.setfenv
    local function __vm_pack(...)
        local n = __vm_select("#", ...)
        local t = { n = n }
        for i = 1, n do t[i] = __vm_select(i, ...) end
        return t
    end
    local function __vm_unpack(t, n)
        if n == 0 then return end
        return __vm_unpack_fn(t, 1, n)
    end
    local function __vm_b64decode(parts)
        local alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        local encoded, out, buffer, bits = __vm_table.concat(parts), {}, 0, 0
        for i = 1, #encoded do
            local ch = encoded:sub(i, i)
            if ch ~= "=" then
                local index = alphabet:find(ch, 1, true)
                if not index then __vm_error("LVM: invalid base64 payload", 0) end
                buffer = buffer * 64 + index - 1
                bits = bits + 6
                if bits >= 8 then
                    bits = bits - 8
                    local divisor = 2 ^ bits
                    out[#out + 1] = __vm_string.char(__vm_math.floor(buffer / divisor) % 256)
                    buffer = buffer % divisor
                end
            end
        end
        return __vm_table.concat(out)
    end
    local function __vm_xor(a, b)
        local r, m = 0, 1
        for _ = 1, 32 do
            if a % 2 ~= b % 2 then r = r + m end
            m = m * 2; a = __vm_math.floor(a / 2); b = __vm_math.floor(b / 2)
        end
        return r
    end
    local function __vm_decode_payload(parts)
        local encoded = __vm_b64decode(parts)
        local header_raw = {}
        for i = 1, 90 do header_raw[i] = __vm_string.char(__vm_xor(__vm_string.byte(encoded, i), __VM_HEADER_KEY[((i - 1) % 90) + 1]) % 256) end
        local header_str = __vm_table.concat(header_raw)
        if __vm_string.sub(header_str, 1, 4) ~= "LVMH" then __vm_error("LVM: header authentication failed for " .. __vm_source, 0) end
        local _vm_seed = __vm_string.byte(header_str, 5) * 16777216 + __vm_string.byte(header_str, 6) * 65536 + __vm_string.byte(header_str, 7) * 256 + __vm_string.byte(header_str, 8)
        local _vm_op_perm = {}
        for i = 1, 39 do local off = 7 + i * 2; _vm_op_perm[i] = __vm_string.byte(header_str, off) * 256 + __vm_string.byte(header_str, off + 1) end
        local _vm_checksum = __vm_string.byte(header_str, 87) * 16777216 + __vm_string.byte(header_str, 88) * 65536 + __vm_string.byte(header_str, 89) * 256 + __vm_string.byte(header_str, 90)
        local decoded, prng_a = {}, __vm_xor(_vm_checksum, _vm_seed) % 2147483647
        local prng_b = (_vm_checksum * 48271 + prng_a * 69621) % 2147483647
        if prng_a == 0 then prng_a = 1 end; if prng_b == 0 then prng_b = 1 end
        for i = 91, #encoded do
            prng_a = (prng_a * 16807) % 2147483647; prng_b = (prng_b * 48271) % 2147483647
            local key_byte = (__vm_math.floor(prng_a / 16777216) + __vm_math.floor(prng_b / 16777216)) % 256
            decoded[i - 90] = __vm_string.char(__vm_xor(__vm_string.byte(encoded, i), key_byte) % 256)
        end
        local result, checksum = __vm_table.concat(decoded), 0
        for i = 1, #result do checksum = (checksum + __vm_string.byte(result, i)) % 4294967296 end
        if checksum ~= _vm_checksum then __vm_error("LVM: payload authentication failed for " .. __vm_source, 0) end
        return result, _vm_seed, _vm_op_perm, _vm_checksum
    end
    local _string, _tonumber, _math, _error, _tostring, _type = _G2.string or __vm_string, _G2.tonumber or __vm_tonumber, _G2.math or __vm_math, _G2.error or __vm_error, _G2.tostring or __vm_tostring, _G2.type or __vm_type
    local _pcall, _getmetatable, _setmetatable, _rawget, _rawset = _G2.pcall or __vm_pcall, _G2.getmetatable or __vm_getmetatable, _G2.setmetatable or __vm_setmetatable, _G2.rawget or __vm_rawget, _G2.rawset or __vm_rawset
    local _next, _ipairs, _pairs, _select, _unpack, _table = _G2.next or __vm_next, _G2.ipairs or __vm_ipairs, _G2.pairs or __vm_pairs, _G2.select or __vm_select, _G2.unpack or __vm_unpack_fn, _G2.table or __vm_table
    local _getfenv, _setfenv = _G2.getfenv or __vm_getfenv, _G2.setfenv or __vm_setfenv
    local _G2_mt, _G2_mt_decl = _getmetatable(_G2), {}
    if _G2_mt then
        local k, v = _next(_G2_mt)
        while k do
            if k == "__declared" then _G2_mt_decl = v; break end
            k, v = _next(_G2_mt, k)
        end
    end
    local _G_ref, _G_decl = _rawget(_G2, "GLOBAL"), {}
    if _G_ref then
        local _G_mt = _getmetatable(_G_ref)
        if _G_mt then
            local k, v = _next(_G_mt)
            while k do
                if k == "__declared" then _G_decl = v; break end
                k, v = _next(_G_mt, k)
            end
        end
    end
    local function _auto_declare(object, key)
        if _G_decl and object == _G_ref then _G_decl[key] = true
        elseif _G2_mt_decl and object == _G2 then _G2_mt_decl[key] = true end
    end
    local closure_states, call_closure, _vm_call_ref, _vm_metamethods, _orig_setmetatable = _setmetatable({}, { __mode = "k" }), nil, {}, {}, _setmetatable
    _setmetatable = function(tbl, mt)
        if mt and (mt.__index or mt.__newindex) then
            local orig_mt = _getmetatable(tbl)
            _vm_metamethods[tbl] = orig_mt
            local new_mt = {}
            if orig_mt then for ok, ov in _pairs(orig_mt) do new_mt[ok] = ov end end
            if mt.__index then
                local orig_index = mt.__index
                new_mt.__index = function(t, k)
                    local state = closure_states[orig_index]
                    if state then local vals = _vm_call_ref[1](state, { n = 2, [1] = t, [2] = k }); return vals and vals[1] end
                    return orig_index(t, k)
                end
            else new_mt.__index = mt.__index end
            if mt.__newindex then
                local orig_newindex = mt.__newindex
                new_mt.__newindex = function(t, k, v)
                    local state = closure_states[orig_newindex]
                    if state then _vm_call_ref[1](state, { n = 3, [1] = t, [2] = k, [3] = v }); return end
                    orig_newindex(t, k, v)
                end
            else new_mt.__newindex = mt.__newindex end
            for mk, mv in _pairs(mt) do if mk ~= "__index" and mk ~= "__newindex" then new_mt[mk] = mv end end
            return _orig_setmetatable(tbl, new_mt)
        end
        return _orig_setmetatable(tbl, mt)
    end
    if _G2 ~= __vm_G then _G2.setmetatable, __vm_env.setmetatable = _setmetatable, _setmetatable end
    local bytes, _vm_seed, _vm_op_perm, _vm_checksum = __vm_decode_payload(__vm_pages)
    local position = 1
    local function need(count)
        if position + count - 1 > #bytes then _error("LVM: truncated bytecode in " .. __vm_source, 0) end
    end
    local function u8() need(1); local value = _string.byte(bytes, position); position = position + 1; return value end
    local function u16() need(2); local a, b = _string.byte(bytes, position, position + 1); position = position + 2; return a * 256 + b end
    local function u32() need(4); local a, b, c, d = _string.byte(bytes, position, position + 3); position = position + 4; return ((a * 256 + b) * 256 + c) * 256 + d end
    local function text() local length = u32(); need(length); local value = bytes:sub(position, position + length - 1); position = position + length; return value end
    if bytes:sub(1, 4) ~= "LVM1" then _error("LVM: invalid bytecode magic in " .. __vm_source, 0) end
    position = 5
    local version = u8()
    if version ~= 4 then _error("LVM: unsupported bytecode version " .. _tostring(version) .. " in " .. __vm_source, 0) end
    local op_decode, prototype_count = {}, u16()
    for canonical_op, raw_op in _ipairs(_vm_op_perm) do op_decode[raw_op] = canonical_op - 1 end
    local prototypes = {}
    for prototype_index = 1, prototype_count do
        text()
        local proto = { params = u16(), vararg = u8() == 1, upvalues = {}, locals = {}, constants = {}, code = {} }
        local upvalue_count = u16()
        for i = 1, upvalue_count do proto.upvalues[i] = { u8(), u16() } end
        local local_count = u16()
        for i = 1, local_count do proto.locals[i] = { "", u16() } end
        local constant_count = u16()
        for i = 1, constant_count do
            local tag = u8()
            if tag == 0 then proto.constants[i] = nil
            elseif tag == 1 then proto.constants[i] = u8() == 1
            elseif tag == 2 then proto.constants[i] = _tonumber(text())
            elseif tag == 3 then proto.constants[i] = text()
            else _error("LVM: invalid constant tag", 0) end
        end
        local instruction_count = u32()
        proto.constant_count = constant_count
        for i = 1, instruction_count do
            local raw_op = u8(); local a, b, c, line = u16(), u16(), u16(), u16()
            proto.code[i] = { op_decode[raw_op] or raw_op, a, b, c, line }
        end
        local dispatch_entry_count = u16()
        proto._db = {}
        if dispatch_entry_count > 0 then
            local dk_a, dk_b = __vm_xor(_vm_seed, 1515870810) % 2147483647, __vm_xor(_vm_seed, 1010580540) % 2147483647
            if dk_a == 0 then dk_a = 1 end; if dk_b == 0 then dk_b = 1 end
            for i = 1, dispatch_entry_count do
                dk_a = (dk_a * 16807) % 2147483647; dk_b = (dk_b * 48271) % 2147483647
                local dk_byte = (_math.floor(dk_a / 16777216) + _math.floor(dk_b / 16777216)) % 256
                local dk_key = (dk_byte * 256 + dk_byte) % 65536
                proto._db[u16()] = __vm_xor(u16(), dk_key) % 65536
            end
        end
        prototypes[prototype_index] = proto
    end
    if position <= #bytes then _error("LVM: trailing bytecode data in " .. __vm_source, 0) end
    local jump_ops = { [17] = true, [18] = true, [19] = true, [20] = true, [21] = true }
    for prototype_index, proto in _ipairs(prototypes) do
        for instruction_index, instruction in _ipairs(proto.code) do
            local op, a, b, c = instruction[1], instruction[2], instruction[3], instruction[4]
            if op > 38 then _error("LVM: unknown opcode in prototype " .. _tostring(prototype_index), 0) end
            if jump_ops[op] and a > #proto.code then _error("LVM: jump target out of range in prototype " .. _tostring(prototype_index), 0) end
            if (op == 1 or op == 6 or op == 7) and a >= proto.constant_count then _error("LVM: constant reference out of range", 0) end
            if (op == 23 or op == 35) and c >= proto.constant_count then _error("LVM: method name reference out of range", 0) end
            if op == 25 and not prototypes[a + 1] then _error("LVM: closure reference out of range", 0) end
            if op == 27 and a ~= 1 and a ~= 65535 then _error("LVM: invalid vararg count", 0) end
        end
    end
    local function truth(value) return value ~= nil and value ~= false end
    local function binary(op, l, r)
        if op == 1 then return l + r elseif op == 2 then return l - r elseif op == 3 then return l * r elseif op == 4 then return l / r
        elseif op == 5 then return l % r elseif op == 6 then return l ^ r elseif op == 7 then return l .. r elseif op == 8 then return l == r
        elseif op == 9 then return l ~= r elseif op == 10 then return l < r elseif op == 11 then return l <= r elseif op == 12 then return l > r
        elseif op == 13 then return l >= r else _error("LVM: invalid binary operation", 0) end
    end
    local function unary(op, v)
        if op == 1 then return -v elseif op == 2 then return not truth(v) elseif op == 3 then return #v else _error("LVM: invalid unary operation", 0) end
    end
    local call_closure, call_marker, active_frames = nil, {}, {}
    local native_debug = __vm_env.debug
    local native_debug_getinfo, native_debug_getlocal, native_debug_setlocal = native_debug and native_debug.getinfo, native_debug and native_debug.getlocal, native_debug and native_debug.setlocal
    local native_debug_getupvalue, native_debug_setupvalue, native_debug_sethook, native_debug_gethook, native_debug_traceback = native_debug and native_debug.getupvalue, native_debug and native_debug.setupvalue, native_debug and native_debug.sethook, native_debug and native_debug.gethook, native_debug and native_debug.traceback
    local native_getfenv, native_setfenv, native_pcall, native_xpcall = __vm_env.getfenv, __vm_env.setfenv, __vm_env.pcall, __vm_env.xpcall
    local native_string_dump, native_loadstring, native_loadfile = __vm_env.string and __vm_env.string.dump, __vm_env.loadstring, __vm_env.loadfile
    local vm_hook, vm_hook_mask, vm_hook_count, vm_hook_ticks, vm_hook_running = nil, "", 0, 0, false
    local function load_cell(cell) return cell.frame and cell.frame.locals[cell.slot] or cell.value end
    local function store_cell(cell, value)
        if cell.frame then cell.frame.locals[cell.slot] = value else cell.value = value end
    end
    local function get_cell(frame, slot)
        local cell = frame.cells[slot]; if not cell then cell = { frame = frame, slot = slot + 1 }; frame.cells[slot] = cell end; return cell
    end
    local function close_frame(frame)
        for _, cell in _pairs(frame.cells) do cell.value = frame.locals[cell.slot]; cell.frame = nil end
    end
    local function make_closure(prototype_id, parent_frame)
        local proto = prototypes[prototype_id + 1]
        if not proto then _error("LVM: invalid closure prototype", 0) end
        local state = { proto = proto, env = parent_frame and parent_frame.env or __vm_env, up = {} }
        if parent_frame then
            for i, descriptor in _ipairs(proto.upvalues) do
                if descriptor[1] == 0 then state.up[i] = get_cell(parent_frame, descriptor[2])
                else state.up[i] = parent_frame.up[descriptor[2] + 1] end
            end
        end
        local proxy
        proxy = function(...)
            if native_getfenv then local proxy_env = native_getfenv(proxy); if proxy_env ~= nil then state.env = proxy_env end end
            local args = __vm_pack(...)
            local values, count = call_closure(state, args, proxy)
            return __vm_unpack(values, count)
        end
        closure_states[proxy] = state
        return proxy
    end
    local function vm_frame_info(frame, function_value, what)
        return { source = __vm_source, short_src = __vm_source, what = "Lua", currentline = frame.current_line or -1, linedefined = 0, lastlinedefined = 0, name = frame.proto.name, namewhat = frame.proto.name ~= "" and "local" or "", nups = #frame.up, nparams = frame.proto.params, isvararg = frame.proto.vararg, func = function_value }
    end
    local function debug_getinfo(arguments)
        if not native_debug_getinfo then return nil end
        local subject, what = arguments[1], arguments[2]
        if _type(subject) == "number" then
            local level = _math.floor(subject)
            if level == 0 then return native_debug_getinfo(1, what) end
            if level >= 1 and level <= #active_frames then return vm_frame_info(active_frames[#active_frames - level + 1].frame, active_frames[#active_frames - level + 1].function_value, what) end
            local native_level = level - #active_frames + 4
            if native_level >= 1 then return native_debug_getinfo(native_level, what) end
            return nil
        end
        local state = closure_states[subject]
        if state then return vm_frame_info({ proto = state.proto, current_line = -1, up = state.up }, subject, what) end
        return native_debug_getinfo(subject, what)
    end
    local function frame_for_level(level)
        level = _math.floor(_tonumber(level) or 0)
        if level <= 0 then return active_frames[#active_frames] end
        return active_frames[#active_frames - level + 1]
    end
    local native_debug_level = function(level) return level - #active_frames + 4 end
    local function debug_getlocal(arguments)
        local level, index = _tonumber(arguments[1]), _tonumber(arguments[2])
        if level and index then
            level, index = _math.floor(level), _math.floor(index)
            local entry = frame_for_level(level)
            if entry and entry.frame.proto.locals[index] then
                local descriptor = entry.frame.proto.locals[index]
                return { n = 2, [1] = descriptor[1], [2] = entry.frame.locals[descriptor[2] + 1] }, 2
            end
            if entry then return {}, 0 end
            if native_debug_getlocal then
                local native_level = native_debug_level(level)
                if native_level >= 1 then local name, value = native_debug_getlocal(native_level, index); return { n = 2, [1] = name, [2] = value }, name ~= nil and 2 or 0 end
            end
        end
        return {}, 0
    end
    local function debug_setlocal(arguments)
        local level, index = _tonumber(arguments[1]), _tonumber(arguments[2])
        if level and index then
            level, index = _math.floor(level), _math.floor(index)
            local entry = frame_for_level(level)
            if entry and entry.frame.proto.locals[index] then
                local descriptor, slot = entry.frame.proto.locals[index], entry.frame.proto.locals[index][2]
                local cell = entry.frame.cells[slot]
                if cell then store_cell(cell, arguments[3]) else entry.frame.locals[slot + 1] = arguments[3] end
                return { n = 1, [1] = descriptor[1] }, 1
            end
            if entry then return {}, 0 end
            if native_debug_setlocal then
                local native_level = native_debug_level(level)
                if native_level >= 1 then local name = native_debug_setlocal(native_level, index, arguments[3]); return { n = 1, [1] = name }, name ~= nil and 1 or 0 end
            end
        end
        return {}, 0
    end
    local function debug_getupvalue(arguments)
        local subject = arguments[1]; local index = _math.floor(_tonumber(arguments[2]) or 0)
        local state = closure_states[subject]
        if state and index >= 1 and state.up[index] then return { n = 2, [1] = "", [2] = load_cell(state.up[index]) }, 2 end
        if state then return {}, 0 end
        if native_debug_getupvalue then local name, value = native_debug_getupvalue(subject, index); return { n = 2, [1] = name, [2] = value }, name ~= nil and 2 or 0 end
        return {}, 0
    end
    local function debug_setupvalue(arguments)
        local subject = arguments[1]; local index = _math.floor(_tonumber(arguments[2]) or 0)
        local state = closure_states[subject]
        if state and index >= 1 and state.up[index] then store_cell(state.up[index], arguments[3]); return { n = 1, [1] = "" }, 1 end
        if state then return {}, 0 end
        if native_debug_setupvalue then local name = native_debug_setupvalue(subject, index, arguments[3]); return { n = 1, [1] = name }, name ~= nil and 1 or 0 end
        return {}, 0
    end
    local function debug_sethook(arguments)
        local hook = arguments[1]
        if hook == nil then vm_hook, vm_hook_mask, vm_hook_count, vm_hook_ticks = nil, "", 0, 0; return {}, 0 end
        if _type(hook) ~= "function" then _error("bad argument #1 to 'sethook' (function expected)", 0) end
        vm_hook, vm_hook_mask, vm_hook_count, vm_hook_ticks = hook, arguments[2] or "", _math.max(0, _math.floor(_tonumber(arguments[3]) or 0)), 0
        return {}, 0
    end
    local function debug_gethook()
        if vm_hook == nil then return {}, 0 end
        return { n = 3, [1] = vm_hook, [2] = vm_hook_mask, [3] = vm_hook_count }, 3
    end
    local function dump_vm_closure(state)
        local out = { "LVM-DUMP2", state.proto.name }
        for _, instruction in _ipairs(state.proto.code) do
            out[#out + 1] = _string.char(instruction[1] % 256, _math.floor(instruction[2] / 256) % 256, instruction[2] % 256, _math.floor(instruction[3] / 256) % 256, instruction[3] % 256, _math.floor(instruction[4] / 256) % 256, instruction[4] % 256)
        end
        return _table.concat(out)
    end
    local function vm_getfenv(arguments)
        local subject = arguments[1]
        if subject == nil then local e = frame_for_level(1); return e and e.frame.env or __vm_env end
        if _type(subject) == "number" then local e = frame_for_level(subject); return e and e.frame.env or __vm_env end
        local state = closure_states[subject]; if state then return state.env end
        return native_getfenv(subject)
    end
    local function vm_setfenv(arguments)
        local subject, environment = arguments[1], arguments[2]
        if _type(subject) == "number" then
            local entry = frame_for_level(subject)
            if not entry then _error("bad argument #1 to 'setfenv' (level out of range)", 0) end
            if _type(environment) ~= "table" then _error("bad argument #2 to 'setfenv' (table expected)", 0) end
            entry.frame.env, entry.state.env = environment, environment
            if entry.function_value and native_setfenv then native_setfenv(entry.function_value, environment) end
            return subject
        end
        local state = closure_states[subject]
        if state then
            native_setfenv(subject, environment); state.env = environment
            for _, entry in _ipairs(active_frames) do if entry.state == state then entry.frame.env = environment end end
            return subject
        end
        return native_setfenv(subject, environment)
    end
    local function protected_call(native_function, arguments)
        local depth = #active_frames
        local result = __vm_pack(native_function(__vm_unpack(arguments, arguments.n)))
        if result[1] == false then while #active_frames > depth do active_frames[#active_frames] = nil end end
        return result, result.n
    end
    local __vm_bounce
    local function call_value(function_value, arguments, source_line)
        local target, current_arguments = function_value, arguments
        for _ = 1, 100 do
            if target == _error then
                local message = current_arguments[1]
                if _type(message) == "string" then _error(__vm_source .. ":" .. _tostring(source_line or 0) .. ": " .. message, 0) end
                _error(message, 0)
            end
            if native_debug_getinfo and target == native_debug_getinfo then return { n = 1, [1] = debug_getinfo(current_arguments) }, 1 end
            if native_getfenv and target == native_getfenv then return { n = 1, [1] = vm_getfenv(current_arguments) }, 1 end
            if native_setfenv and target == native_setfenv then return { n = 1, [1] = vm_setfenv(current_arguments) }, 1 end
            if native_debug_getlocal and target == native_debug_getlocal then return debug_getlocal(current_arguments) end
            if native_debug_setlocal and target == native_debug_setlocal then return debug_setlocal(current_arguments) end
            if native_debug_getupvalue and target == native_debug_getupvalue then return debug_getupvalue(current_arguments) end
            if native_debug_setupvalue and target == native_debug_setupvalue then return debug_setupvalue(current_arguments) end
            if native_debug_sethook and target == native_debug_sethook then return debug_sethook(current_arguments) end
            if native_debug_gethook and target == native_debug_gethook then return debug_gethook() end
            if native_string_dump and target == native_string_dump then
                local state = closure_states[current_arguments[1]]
                if state then return { n = 1, [1] = dump_vm_closure(state) }, 1 end
                local result = __vm_pack(native_string_dump(__vm_unpack(current_arguments, current_arguments.n))); return result, result.n
            end
            if native_loadstring and target == native_loadstring then
                local result = __vm_pack(native_loadstring(__vm_unpack(current_arguments, current_arguments.n)))
                if result[1] and native_setfenv then local entry = frame_for_level(0); if entry and entry.frame.env then native_setfenv(result[1], entry.frame.env) end end
                return result, result.n
            end
            if native_loadfile and target == native_loadfile then
                local result = __vm_pack(native_loadfile(__vm_unpack(current_arguments, current_arguments.n)))
                if result[1] and native_setfenv then local entry = frame_for_level(0); if entry and entry.frame.env then native_setfenv(result[1], entry.frame.env) end end
                return result, result.n
            end
            if native_pcall and target == native_pcall then return protected_call(native_pcall, current_arguments) end
            if native_xpcall and target == native_xpcall then return protected_call(native_xpcall, current_arguments) end
            if _type(target) == "function" then
                local state = closure_states[target]
                if state then return call_closure(state, current_arguments, target) end
                local result = __vm_pack(target(__vm_unpack(current_arguments, current_arguments.n))); return result, result.n
            end
            local metatable = _getmetatable(target); local metamethod = metatable and metatable.__call
            if metamethod == nil then _error("attempt to call a " .. _type(target) .. " value", 0) end
            local next_arguments = { n = current_arguments.n + 1 }; next_arguments[1] = target
            for i = 1, current_arguments.n do next_arguments[i + 1] = current_arguments[i] end
            target, current_arguments = metamethod, next_arguments
        end
        _error("LVM: __call metamethod chain too long", 0)
    end
    local function hook_event(event, frame, line)
        if vm_hook == nil or vm_hook_running then return end
        local mask_code = event == "line" and "l" or event == "call" and "c" or event == "return" and "r"
        if event ~= "count" and _string.find(vm_hook_mask, mask_code, 1, true) == nil then return end
        vm_hook_running = true
        local protected = native_pcall or _pcall
        local ok, error_value = protected(function() call_value(vm_hook, { n = 2, [1] = event, [2] = line }, line or 0) end)
        vm_hook_running = false
        if not ok then _error(error_value, 0) end
    end
    local function hook_instruction(frame, line)
        if vm_hook == nil or vm_hook_running then return end
        if _string.find(vm_hook_mask, "l", 1, true) ~= nil and frame.last_hook_line ~= line then frame.last_hook_line = line; hook_event("line", frame, line) end
        if vm_hook_count > 0 then vm_hook_ticks = vm_hook_ticks + 1; if vm_hook_ticks >= vm_hook_count then vm_hook_ticks = 0; hook_event("count", frame, line) end end
    end
    local function initialize_frame(frame, state, arguments, function_value)
        frame.proto, frame.state, frame.env, frame.up = state.proto, state, state.env, state.up
        frame.locals, frame.stack, frame.cells, frame.pc = {}, {}, {}, 1
        frame.varargs, frame.function_value = { n = 0 }, function_value
        for i = 1, state.proto.params do frame.locals[i] = arguments[i] end
        if state.proto.vararg then
            frame.varargs.n = _math.max(0, arguments.n - state.proto.params)
            for i = 1, frame.varargs.n do frame.varargs[i] = arguments[state.proto.params + i] end
        end
    end
    local function resolve_vm_target(function_value, arguments)
        local target, current_arguments = function_value, arguments
        for _ = 1, 100 do
            local state = closure_states[target]
            if state then return state, current_arguments, target end
            local metatable = _getmetatable(target); local metamethod = metatable and metatable.__call
            if metamethod == nil then return nil end
            local next_arguments = { n = current_arguments.n + 1 }; next_arguments[1] = target
            for i = 1, current_arguments.n do next_arguments[i + 1] = current_arguments[i] end
            target, current_arguments = metamethod, next_arguments
        end
        _error("LVM: __call metamethod chain too long", 0)
    end
    local function run_frame(frame)
        local proto, code, stack, top, dispatch_id = frame.proto, frame.proto.code, frame.stack, 0, 0
        local function push(value) top = top + 1; stack[top] = value end
        local function pop() local value = stack[top]; stack[top] = nil; top = top - 1; return value end
        local function adjust(count)
            while top > count do stack[top] = nil; top = top - 1 end
            while top < count do top = top + 1; stack[top] = nil end
        end
        active_frames[#active_frames + 1] = { frame = frame, state = frame.state, function_value = frame.function_value }
        if code[1] then hook_event("call", frame, code[1][5]) end
        while true do
            local instruction = code[frame.pc]
            if not instruction then hook_event("return", frame, frame.current_line); close_frame(frame); active_frames[#active_frames] = nil; return {}, 0 end
            frame.pc = frame.pc + 1
            local op, a, b, c, line = instruction[1], instruction[2], instruction[3], instruction[4], instruction[5]
            frame.current_line = line
            hook_instruction(frame, line)
            if op == 0 then
            elseif op == 1 then push(proto.constants[a + 1])
            elseif op == 2 then push(frame.locals[a + 1])
            elseif op == 3 then frame.locals[a + 1] = pop()
            elseif op == 4 then push(load_cell(frame.up[a + 1]))
            elseif op == 5 then store_cell(frame.up[a + 1], pop())
            elseif op == 6 then
                local _k = proto.constants[a + 1]
                local _v = _rawget(frame.env, _k)
                if _v == nil and _G_ref then _v = _rawget(_G_ref, _k) end
                if _v == nil then
                    local _mt = _getmetatable(frame.env)
                    if _mt then
                        local _idx = _mt.__index
                        if _idx then
                            if _type(_idx) == "function" then
                                __vm_bounce = function() return _idx(frame.env, _k) end
                                _v = __vm_bounce()
                            else _v = _idx[_k] end
                        end
                    end
                end
                push(_v)
            elseif op == 7 then
                local _k = proto.constants[a + 1]
                _auto_declare(frame.env, _k); _rawset(frame.env, _k, pop())
            elseif op == 8 then push({})
            elseif op == 9 then push(stack[top])
            elseif op == 10 then pop()
            elseif op == 11 then local key = pop(); local object = pop(); push(object[key])
            elseif op == 12 then
                local value, key, object = pop(), pop(), pop()
                if object == _G_ref then _rawset(object, key, value) else _auto_declare(object, key); object[key] = value end
            elseif op == 13 then
                local value, key, object = pop(), pop(), pop()
                if object == _G_ref then _rawset(object, key, value) else _auto_declare(object, key); object[key] = value end
            elseif op == 14 then
                local value, object, key = pop(), frame.locals[a + 1], frame.locals[b + 1]
                if object == _G_ref then _rawset(object, key, value) else _auto_declare(object, key); object[key] = value end
            elseif op == 15 then local right, left = pop(), pop(); push(binary(a, left, right))
            elseif op == 16 then push(unary(a, pop()))
            elseif op == 17 then frame.pc = a + 1
            elseif op == 18 then if not truth(pop()) then frame.pc = a + 1 end
            elseif op == 19 then if truth(pop()) then frame.pc = a + 1 end
            elseif op == 20 then if not truth(stack[top]) then frame.pc = a + 1 end
            elseif op == 21 then if truth(stack[top]) then frame.pc = a + 1 end
            elseif op == 22 then
                local arguments, function_value = {}, nil
                if a == 65535 then
                    local marker = top
                    while marker >= 1 and stack[marker] ~= call_marker do marker = marker - 1 end
                    if marker < 1 or marker == top then _error(__vm_source .. ":" .. _tostring(line) .. ": malformed variable-argument call", 0) end
                    function_value = stack[marker + 1]; arguments.n = top - marker - 1
                    for i = 1, arguments.n do arguments[i] = stack[marker + 1 + i] end
                    for i = marker, top do stack[i] = nil end; top = marker - 1
                else
                    arguments.n = a
                    for i = a, 1, -1 do arguments[i] = pop() end
                    function_value = pop()
                end
                local values, count = call_value(function_value, arguments, line)
                if b == 65535 then for i = 1, count do push(values[i]) end
                elseif b == 1 then push(values[1])
                elseif b ~= 0 then for i = 1, b do push(values[i]) end end
            elseif op == 23 then
                local arguments, object = {}, nil
                if a == 65535 then
                    local marker = top
                    while marker >= 1 and stack[marker] ~= call_marker do marker = marker - 1 end
                    if marker < 1 or marker == top then _error(__vm_source .. ":" .. _tostring(line) .. ": malformed variable-argument method call", 0) end
                    object = stack[marker + 1]; local argument_count = top - marker - 1
                    arguments.n, arguments[1] = argument_count + 1, object
                    for i = 1, argument_count do arguments[i + 1] = stack[marker + 1 + i] end
                    for i = marker, top do stack[i] = nil end; top = marker - 1
                else
                    arguments.n = a + 1
                    for i = a, 1, -1 do arguments[i + 1] = pop() end
                    object = pop()
                end
                local key = proto.constants[c + 1]
                local function_value = object[key]
                arguments[1] = object
                local values, count = call_value(function_value, arguments, line)
                if b == 65535 then for i = 1, count do push(values[i]) end
                elseif b == 1 then push(values[1])
                elseif b ~= 0 then for i = 1, b do push(values[i]) end end
            elseif op == 24 then
                local values, count = {}, a == 65535 and top or a
                for i = 1, count do values[i] = stack[i] end
                hook_event("return", frame, line); close_frame(frame); active_frames[#active_frames] = nil; return values, count
            elseif op == 25 then push(make_closure(a, frame))
            elseif op == 26 then adjust(a)
            elseif op == 27 then
                if a == 65535 then for i = 1, frame.varargs.n do push(frame.varargs[i]) end
                else push(frame.varargs[a]) end
            elseif op == 28 then
                local index, limit, step = frame.locals[a + 1], frame.locals[b + 1], frame.locals[c + 1]
                if _type(index) == "string" then index = _tonumber(index) end
                if _type(limit) == "string" then limit = _tonumber(limit) end
                if _type(step) == "string" then step = _tonumber(step) end
                if _type(index) ~= "number" then _error("'for' initial value must be a number", 0) end
                if _type(limit) ~= "number" then _error("'for' limit must be a number", 0) end
                if _type(step) ~= "number" then _error("'for' step must be a number", 0) end
                frame.locals[a + 1], frame.locals[b + 1], frame.locals[c + 1] = index, limit, step
                local cell = frame.cells[a]
                if cell then cell.value = frame.locals[cell.slot]; cell.frame = nil; frame.cells[a] = nil end
                push(step ~= 0 and ((step >= 0 and index <= limit) or (step < 0 and index >= limit)) or false)
            elseif op == 29 then
                local cell = frame.cells[a]
                if cell then cell.value = frame.locals[cell.slot]; cell.frame = nil; frame.cells[a] = nil end
                frame.locals[a + 1] = frame.locals[a + 1] + frame.locals[b + 1]
            elseif op == 30 then
                local scratch = (a * 1103515245 + 12345) % 2147483648
                if scratch == -1 then _error("unreachable", 0) end
            elseif op == 31 then push(call_marker)
            elseif op == 32 then
                for slot = a, a + b - 1 do
                    local cell = frame.cells[slot]
                    if cell then cell.value = frame.locals[cell.slot]; cell.frame = nil; frame.cells[slot] = nil end
                end
            elseif op == 33 then
                local marker = top
                while marker >= 1 and stack[marker] ~= call_marker do marker = marker - 1 end
                if marker < 2 then _error(__vm_source .. ":" .. _tostring(line) .. ": malformed table field", 0) end
                local object, count = stack[marker - 1], top - marker
                for i = 1, count do object[a + i - 1] = stack[marker + i] end
                for i = marker, top do stack[i] = nil end; top = marker - 1
            elseif op == 34 or op == 35 then
                local arguments, function_value, is_method = {}, nil, op == 35
                if a == 65535 then
                    local marker = top
                    while marker >= 1 and stack[marker] ~= call_marker do marker = marker - 1 end
                    if marker < 1 or marker == top then _error(__vm_source .. ":" .. _tostring(line) .. ": malformed tail call", 0) end
                    function_value = stack[marker + 1]; arguments.n = top - marker - 1
                    for i = 1, arguments.n do arguments[i] = stack[marker + 1 + i] end
                    if is_method then
                        arguments.n = arguments.n + 1
                        for i = arguments.n, 2, -1 do arguments[i] = arguments[i - 1] end
                        local object, key = stack[marker + 1], proto.constants[c + 1]
                        function_value, arguments[1] = object[key], object
                    end
                    for i = marker, top do stack[i] = nil end; top = marker - 1
                else
                    local explicit_count = a
                    if is_method then
                        arguments.n = explicit_count + 1
                        for i = explicit_count, 1, -1 do arguments[i + 1] = pop() end
                        local object, key = pop(), proto.constants[c + 1]
                        function_value, arguments[1] = object[key], object
                    else
                        arguments.n = explicit_count
                        for i = explicit_count, 1, -1 do arguments[i] = pop() end
                        function_value = pop()
                    end
                end
                local target_state, target_arguments, target_function = resolve_vm_target(function_value, arguments)
                if target_state then
                    close_frame(frame); initialize_frame(frame, target_state, target_arguments, target_function)
                    proto, code, stack, top = frame.proto, frame.proto.code, frame.stack, 0
                    active_frames[#active_frames] = { frame = frame, state = frame.state, function_value = frame.function_value }
                    if code[1] then hook_event("call", frame, code[1][5]) end
                else
                    local values, count = call_value(function_value, arguments, line)
                    hook_event("return", frame, line); close_frame(frame); active_frames[#active_frames] = nil; return values, count
                end
            elseif op == 36 then
                if dispatch_id >= 1 and dispatch_id <= #proto._db then frame.pc = proto._db[dispatch_id] end
            elseif op == 37 then dispatch_id = a
            elseif op == 38 then
                if truth(pop()) then dispatch_id = b else dispatch_id = c end
            else
                _error(__vm_source .. ":" .. _tostring(line) .. ": invalid inner opcode " .. _tostring(op), 0)
            end
        end
    end
    call_closure = function(state, arguments, function_value)
        local frame = { proto = state.proto, state = state, env = state.env, up = state.up, locals = {}, stack = {}, cells = {}, pc = 1, varargs = { n = 0 }, function_value = function_value }
        initialize_frame(frame, state, arguments, function_value)
        return run_frame(frame)
    end
    _vm_call_ref[1] = call_closure
    local root_state = { proto = prototypes[1], env = __vm_env, up = {} }
    local __vm_argc, __vm_argv = __vm_select("#", ...), {}
    for __vm_i = 1, __vm_argc do __vm_argv[__vm_i] = __vm_select(__vm_i, ...) end
    local root_arguments = { n = __vm_argc }
    for i = 1, __vm_argc do root_arguments[i] = __vm_argv[i] end
    local values, count = call_closure(root_state, root_arguments)
    return __vm_unpack(values, count)
end
return __vm_run(__VM_PAGES, __VM_SOURCE)
