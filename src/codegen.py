import llvmlite.ir as ir
import llvmlite.binding as llvm
# pyrefly: ignore [missing-import]
import src.ast as ast
from typing import Dict, Any, Optional, List, Tuple

class CodeGenerator:
    def __init__(self, target_triple: str = "x86_64-unknown-none-elf"):
        self.target_triple = target_triple
        self.module = ir.Module(name="os_module")
        self.module.triple = target_triple

        self.builder: ir.IRBuilder = None

        # Local variable stack pointers (alloca'd)
        self.variables: Dict[str, ir.Value] = {}

        # Global function registry
        self.functions: Dict[str, ir.Function] = {}

        # Struct type registry: name -> ir.LiteralStructType
        self.struct_types: Dict[str, ir.LiteralStructType] = {}
        # Struct field order: name -> [field_name, ...]
        self.struct_fields: Dict[str, List[str]] = {}

        # Enum variant registry: name -> {variant: int_value}
        self.enum_variants: Dict[str, Dict[str, int]] = {}

        # Global string counter (for unique names)
        self._str_counter = 0

        # Initialize LLVM for all cross-compilation targets
        try:
            llvm.initialize_all_targets()
            llvm.initialize_all_asmprinters()
            llvm.initialize_all_asmparsers()
        except Exception:
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            llvm.initialize_native_asmparser()

    # ==========================================
    # Type Resolution
    # ==========================================

    def get_llvm_type(self, type_name: str) -> ir.Type:
        if type_name in ("int", "bool"):
            return ir.IntType(64)
        elif type_name == "u8":
            return ir.IntType(8)
        elif type_name == "u16":
            return ir.IntType(16)
        elif type_name == "u32":
            return ir.IntType(32)
        elif type_name == "str":
            return ir.PointerType(ir.IntType(8))  # char*
        elif type_name == "void":
            return ir.VoidType()
        elif type_name == "ptr":
            return ir.PointerType(ir.IntType(8))  # void*
        elif type_name.startswith("ptr[") and type_name.endswith("]"):
            inner = type_name[4:-1]
            return ir.PointerType(self.get_llvm_type(inner))
        elif type_name.startswith("[") and ";" in type_name:
            # Array type: [T; N]
            inner_part = type_name[1:type_name.index(";")].strip()
            size_part  = type_name[type_name.index(";")+1:-1].strip()
            return ir.ArrayType(self.get_llvm_type(inner_part), int(size_part))
        elif type_name in self.struct_types:
            return self.struct_types[type_name]
        elif type_name in self.enum_variants:
            return ir.IntType(32)  # Enums are i32
        else:
            return ir.IntType(64)  # Safe default

    # ==========================================
    # Visitor Dispatch
    # ==========================================

    def generate(self, node: ast.ASTNode):
        method_name = f'generate_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_generate)
        return visitor(node)

    def generic_generate(self, node: ast.ASTNode):
        raise NotImplementedError(f"No generate_{type(node).__name__} in CodeGenerator")

    # ==========================================
    # Program
    # ==========================================

    def generate_Program(self, node: ast.Program):
        for stmt in node.statements:
            self.generate(stmt)

    # ==========================================
    # Declarations
    # ==========================================

    def generate_StructDeclaration(self, node: ast.StructDeclaration):
        """Create an LLVM struct type and register its field names.
        If is_hwmap is True, the struct is marked as packed (no padding)."""
        field_types = [self.get_llvm_type(f[1]) for f in node.fields]
        field_names = [f[0].name for f in node.fields]
        is_packed = node.is_hwmap or getattr(node, 'is_packed', False)
        struct_type = ir.LiteralStructType(field_types, packed=is_packed)
        self.struct_types[node.name.name] = struct_type
        self.struct_fields[node.name.name] = field_names

    def generate_EnumDeclaration(self, node: ast.EnumDeclaration):
        """Map each enum variant to an integer constant."""
        variants = {}
        for i, variant in enumerate(node.variants):
            variants[variant] = i
        self.enum_variants[node.name.name] = variants

    # ==========================================
    # Phase 8: C Interoperability Codegen
    # ==========================================

    def generate_ExternDeclaration(self, node: ast.ExternDeclaration):
        """
        Emit a LLVM 'declare' for a C external function.
        This creates the function prototype without a body, which
        the linker will resolve to the actual C library function.

        Example output IR:
            declare i64 @malloc(i64 %0)
            declare void @free(i8* %0)
            declare i32 @printf(i8*, ...)
        """
        ret_type    = self.get_llvm_type(node.return_type or "void")
        param_types = [self.get_llvm_type(p[1]) for p in node.parameters]

        func_type = ir.FunctionType(ret_type, param_types, var_arg=node.is_variadic)

        # If already declared (e.g. in a block), reuse it
        if node.name.name in self.functions:
            return

        func = ir.Function(self.module, func_type, name=node.name.name)
        # No body → this is a 'declare', not a 'define'
        self.functions[node.name.name] = func

    def generate_ExternBlock(self, node: ast.ExternBlock):
        """Generate extern declarations for all functions in the block."""
        for decl in node.declarations:
            self.generate_ExternDeclaration(decl)


    def generate_FunctionDeclaration(self, node: ast.FunctionDeclaration):
        # Resolve return + param types
        ret_type    = self.get_llvm_type(node.return_type or "void")
        param_types = [self.get_llvm_type(p[1]) for p in node.parameters]

        func_type = ir.FunctionType(ret_type, param_types)
        func      = ir.Function(self.module, func_type, name=node.name.name)

        # ── Calling convention ─────────────────────────────────────────
        if node.is_interrupt and ("x86" in self.module.triple or "i386" in self.module.triple or "i686" in self.module.triple):
            func.calling_convention = 'x86_intrcc'
            # NOTE: x86_intrcc does not allow ptr params without byval.
            # Real interrupt handlers access the frame via the stack directly.
            # Our language enforces no-ptr-params on @interrupt functions at the
            # semantic level (Phase 9 enforces this rule).

        # ── Phase 9: LLVM function attributes ─────────────────────────
        # @noreturn → LLVM noreturn attribute (optimizer knows it never returns)
        if node.is_noreturn:
            func.attributes.add('noreturn')

        # @naked → no stack frame prologue/epilogue (used in bootloaders/ISRs)
        if node.is_naked:
            func.attributes.add('naked')

        # @syscall → mark as OS ABI entry point
        if node.is_syscall:
            func.linkage = 'external'   # syscall handlers must be exported

        # @driver → weak linkage so platform code can override
        if node.is_driver:
            func.linkage = 'weak_odr'

        self.functions[node.name.name] = func
        
        # Emit LEX extension metadata if this is a hook/override
        if getattr(node, 'is_override', False):
            self._emit_osext_entry(6, target=node.override_target, fn_ptr=func)
        elif getattr(node, 'is_hook', False):
            htype = 7 if node.hook_type == "before" else 8
            self._emit_osext_entry(htype, target=node.hook_target, fn_ptr=func)
        elif getattr(node, 'is_new', False):
            self._emit_osext_entry(9, target=node.name.name, fn_ptr=func)

        block         = func.append_basic_block(name="entry")
        self.builder  = ir.IRBuilder(block)
        self.variables = {}

        if getattr(node, 'is_guard', False):
            canary = self.builder.alloca(ir.IntType(64), name="__stack_canary")
            self.builder.store(ir.Constant(ir.IntType(64), 0xDEADBEEFCAFE), canary)

        # Stack-allocate parameters
        for i, param in enumerate(node.parameters):
            param_name = param[0].name
            param_val  = func.args[i]
            param_val.name = param_name
            ptr = self.builder.alloca(param_val.type, name=param_name)
            self.builder.store(param_val, ptr)
            self.variables[param_name] = ptr

        # Generate function body
        for stmt in node.body.statements:
            self.generate(stmt)

        # Implicit terminator
        if not self.builder.block.is_terminated:
            if node.is_noreturn:
                # @noreturn: emit `unreachable` so LLVM knows this path is dead
                self.builder.unreachable()
            elif isinstance(ret_type, ir.VoidType):
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(ret_type, 0))

        return func

    # ==========================================
    # Phase 9: OS Intrinsic Codegen
    # ==========================================

    def generate_OsIntrinsicCall(self, node: ast.OsIntrinsicCall):
        """
        Each OS intrinsic maps to an LLVM inline assembly or intrinsic call.
        We use LLVM's module-level asm (via inline asm) for single instructions.
        """
        args = [self.generate(a) for a in node.arguments]
        i64  = ir.IntType(64)
        i32  = ir.IntType(32)
        i16  = ir.IntType(16)
        i8   = ir.IntType(8)
        void = ir.VoidType()

        # Helper: emit inline asm with given constraint string
        def asm(asm_str: str, constraints: str, ret_type, arg_types, side_effects=True):
            fn_type = ir.FunctionType(ret_type, arg_types)
            asm_fn  = ir.InlineAsm(fn_type, asm_str, constraints,
                                   side_effect=side_effects)
            return self.builder.call(asm_fn, args)

        n = node.name

        if n == "halt":
            # hlt — halt the CPU until next interrupt
            fn_type = ir.FunctionType(void, [])
            asm_fn  = ir.InlineAsm(fn_type, "hlt", "", side_effect=True)
            self.builder.call(asm_fn, [])
            return None  # void intrinsic — no value

        elif n == "cli":
            fn_type = ir.FunctionType(void, [])
            asm_fn  = ir.InlineAsm(fn_type, "cli", "", side_effect=True)
            self.builder.call(asm_fn, [])

        elif n == "sti":
            fn_type = ir.FunctionType(void, [])
            asm_fn  = ir.InlineAsm(fn_type, "sti", "", side_effect=True)
            self.builder.call(asm_fn, [])

        elif n == "memory_barrier":
            fn_type = ir.FunctionType(void, [])
            asm_fn  = ir.InlineAsm(fn_type, "mfence", "", side_effect=True)
            self.builder.call(asm_fn, [])

        elif n == "rdtsc":
            # rdtsc: reads 64-bit timestamp. EDX:EAX → merge into i64
            fn_type  = ir.FunctionType(i64, [])
            asm_fn   = ir.InlineAsm(fn_type, "rdtsc; shlq $$32,%rdx; orq %rdx,%rax",
                                    "={rax},~{rdx},~{dirflag},~{fpsr},~{flags}",
                                    side_effect=True)
            return self.builder.call(asm_fn, [])

        elif n == "cpuid":
            # cpuid(leaf) → returns eax (simplified)
            a0 = args[0] if args else ir.Constant(i32, 0)
            # Cast to i32 if needed
            if a0.type != i32:
                a0 = self.builder.trunc(a0, i32) if a0.type.width > 32 else self.builder.zext(a0, i32)
            fn_type = ir.FunctionType(i32, [i32])
            asm_fn  = ir.InlineAsm(fn_type, "cpuid",
                                   "={eax},{eax},~{ebx},~{ecx},~{edx}",
                                   side_effect=True)
            result = self.builder.call(asm_fn, [a0])
            return self.builder.zext(result, i64)

        elif n in ("outb", "outw", "outl"):
            port = args[0]
            val  = args[1]
            if port.type != i16:
                port = self.builder.trunc(port, i16) if port.type.width > 16 else self.builder.zext(port, i16)
            
            if n == "outb":
                if val.type != i8:
                    val = self.builder.trunc(val, i8) if val.type.width > 8 else self.builder.zext(val, i8)
                fn_type = ir.FunctionType(void, [i16, i8])
                asm_fn  = ir.InlineAsm(fn_type, "outb %al,%dx", "{dx},{al},~{dirflag},~{fpsr},~{flags}", side_effect=True)
            elif n == "outw":
                if val.type != i16:
                    val = self.builder.trunc(val, i16) if val.type.width > 16 else self.builder.zext(val, i16)
                fn_type = ir.FunctionType(void, [i16, i16])
                asm_fn  = ir.InlineAsm(fn_type, "outw %ax,%dx", "{dx},{ax},~{dirflag},~{fpsr},~{flags}", side_effect=True)
            elif n == "outl":
                if val.type != i32:
                    val = self.builder.trunc(val, i32) if val.type.width > 32 else self.builder.zext(val, i32)
                fn_type = ir.FunctionType(void, [i16, i32])
                asm_fn  = ir.InlineAsm(fn_type, "outl %eax,%dx", "{dx},{eax},~{dirflag},~{fpsr},~{flags}", side_effect=True)
            
            self.builder.call(asm_fn, [port, val])

        elif n in ("inb", "inw", "inl"):
            port = args[0]
            if port.type != i16:
                port = self.builder.trunc(port, i16) if port.type.width > 16 else self.builder.zext(port, i16)
            
            if n == "inb":
                fn_type = ir.FunctionType(i8, [i16])
                asm_fn  = ir.InlineAsm(fn_type, "inb %dx,%al", "={al},{dx},~{dirflag},~{fpsr},~{flags}", side_effect=True)
            elif n == "inw":
                fn_type = ir.FunctionType(i16, [i16])
                asm_fn  = ir.InlineAsm(fn_type, "inw %dx,%ax", "={ax},{dx},~{dirflag},~{fpsr},~{flags}", side_effect=True)
            elif n == "inl":
                fn_type = ir.FunctionType(i32, [i16])
                asm_fn  = ir.InlineAsm(fn_type, "inl %dx,%eax", "={eax},{dx},~{dirflag},~{fpsr},~{flags}", side_effect=True)

            result = self.builder.call(asm_fn, [port])
            return self.builder.zext(result, i64)

        elif n == "volatile_load":
            ptr = args[0]
            # Emit inline asm to act as a volatile load
            # LLVM inline asm for this: mov $1, $0
            fn_type = ir.FunctionType(i64, [ptr.type])
            asm_fn = ir.InlineAsm(fn_type, "mov $1, $0", "=r,*m", side_effect=True)
            return self.builder.call(asm_fn, [ptr])

        elif n == "volatile_store":
            ptr = args[0]
            val = args[1]
            if val.type != i64:
                val = self.builder.zext(val, i64) if val.type.width < 64 else self.builder.trunc(val, i64)
            fn_type = ir.FunctionType(void, [ptr.type, i64])
            asm_fn = ir.InlineAsm(fn_type, "mov $1, $0", "=*m,r", side_effect=True)
            self.builder.call(asm_fn, [ptr, val])
            return None

        elif n == "atomic_cmpxchg":
            ptr = args[0]
            expected = args[1]
            new_val = args[2]
            if expected.type != i64: expected = self.builder.zext(expected, i64) if expected.type.width < 64 else self.builder.trunc(expected, i64)
            if new_val.type != i64: new_val = self.builder.zext(new_val, i64) if new_val.type.width < 64 else self.builder.trunc(new_val, i64)
            # LLVM cmpxchg returns {i64, i1}, we extract value 0
            res = self.builder.cmpxchg(ptr, expected, new_val, "seq_cst", "seq_cst")
            return self.builder.extract_value(res, 0)

        elif n == "atomic_xchg":
            ptr = args[0]
            val = args[1]
            if val.type != i64: val = self.builder.zext(val, i64) if val.type.width < 64 else self.builder.trunc(val, i64)
            return self.builder.atomic_rmw("xchg", ptr, val, "seq_cst")

        elif n == "atomic_add":
            ptr = args[0]
            val = args[1]
            if val.type != i64: val = self.builder.zext(val, i64) if val.type.width < 64 else self.builder.trunc(val, i64)
            return self.builder.atomic_rmw("add", ptr, val, "seq_cst")

        elif n == "atomic_sub":
            ptr = args[0]
            val = args[1]
            if val.type != i64: val = self.builder.zext(val, i64) if val.type.width < 64 else self.builder.trunc(val, i64)
            return self.builder.atomic_rmw("sub", ptr, val, "seq_cst")

        elif n == "vga_write":
            x, y, ch, color = args[0], args[1], args[2], args[3]
            x_64 = self.builder.zext(x, i64) if x.type.width < 64 else self.builder.trunc(x, i64)
            y_64 = self.builder.zext(y, i64) if y.type.width < 64 else self.builder.trunc(y, i64)
            ch_8 = self.builder.trunc(ch, i8) if ch.type.width > 8 else (self.builder.zext(ch, i8) if ch.type.width < 8 else ch)
            col_8 = self.builder.trunc(color, i8) if color.type.width > 8 else (self.builder.zext(color, i8) if color.type.width < 8 else color)

            offset = self.builder.mul(self.builder.add(self.builder.mul(y_64, ir.Constant(i64, 80)), x_64), ir.Constant(i64, 2))
            vga_base = self.builder.inttoptr(ir.Constant(i64, 0xB8000), ir.PointerType(i8))
            ch_ptr = self.builder.gep(vga_base, [offset])
            col_ptr = self.builder.gep(vga_base, [self.builder.add(offset, ir.Constant(i64, 1))])
            self.builder.store(ch_8, ch_ptr)
            self.builder.store(col_8, col_ptr)
            return None

        elif n == "draw_cursor":
            x, y, color = args[0], args[1], args[2]
            x_64 = self.builder.zext(x, i64) if x.type.width < 64 else self.builder.trunc(x, i64)
            y_64 = self.builder.zext(y, i64) if y.type.width < 64 else self.builder.trunc(y, i64)
            col_8 = self.builder.trunc(color, i8) if color.type.width > 8 else (self.builder.zext(color, i8) if color.type.width < 8 else color)

            offset = self.builder.mul(self.builder.add(self.builder.mul(y_64, ir.Constant(i64, 80)), x_64), ir.Constant(i64, 2))
            vga_base = self.builder.inttoptr(ir.Constant(i64, 0xB8000), ir.PointerType(i8))
            ch_ptr = self.builder.gep(vga_base, [offset])
            col_ptr = self.builder.gep(vga_base, [self.builder.add(offset, ir.Constant(i64, 1))])
            self.builder.store(ir.Constant(i8, 219), ch_ptr)
            self.builder.store(col_8, col_ptr)
            return None

        elif n == "draw_pixel":
            x, y, color = args[0], args[1], args[2]
            x_64 = self.builder.zext(x, i64) if x.type.width < 64 else self.builder.trunc(x, i64)
            y_64 = self.builder.zext(y, i64) if y.type.width < 64 else self.builder.trunc(y, i64)
            col_32 = self.builder.trunc(color, i32) if color.type.width > 32 else (self.builder.zext(color, i32) if color.type.width < 32 else color)

            offset = self.builder.mul(self.builder.add(self.builder.mul(y_64, ir.Constant(i64, 1024)), x_64), ir.Constant(i64, 4))
            lfb_base = self.builder.inttoptr(ir.Constant(i64, 0xFD000000), ir.PointerType(i32))
            pix_ptr = self.builder.gep(lfb_base, [offset])
            self.builder.store(col_32, pix_ptr)
            return None

        elif n == "task_yield":
            fn_type = ir.FunctionType(ir.VoidType(), [])
            asm_fn = ir.InlineAsm(fn_type, "int $$0x81", "", side_effect=True)
            self.builder.call(asm_fn, [])
            return None

        elif n == "kpanic":
            vga_base = self.builder.inttoptr(ir.Constant(i64, 0xB8000), ir.PointerType(ir.IntType(8)))
            self.builder.store(ir.Constant(ir.IntType(8), 80), vga_base)
            col_ptr = self.builder.gep(vga_base, [ir.Constant(i64, 1)])
            self.builder.store(ir.Constant(ir.IntType(8), 0x4F), col_ptr)
            fn_type = ir.FunctionType(ir.VoidType(), [])
            asm_fn = ir.InlineAsm(fn_type, "hlt", "", side_effect=True)
            self.builder.call(asm_fn, [])
            return None

        elif n == "kmalloc":
            size = args[0] if args else ir.Constant(i64, 32)
            return self.builder.inttoptr(ir.Constant(i64, 0x00200000), ir.PointerType(ir.IntType(8)))

        elif n == "kfree":
            return None

        return ir.Constant(i64, 0)

    def generate_ImportStatement(self, node: ast.ImportStatement):
        pass  # Handled at link time

    def generate_AsmBlock(self, node: ast.AsmBlock):
        """Phase 10: Emit inline assembly."""
        constraints = []
        llvm_args = []
        arg_types = []
        ret_type = ir.VoidType()
        
        # Build constraints for inputs and outputs.
        # We assume standard register mapping "r" for all arguments in this toy language.
        for io_type, expr in node.args:
            val = self.generate(expr)
            if io_type == "out":
                constraints.append("=r")
                ret_type = val.type # Simplified: assumes single output or matching return type
            else:
                constraints.append("r")
                llvm_args.append(val)
                arg_types.append(val.type)

        # Standard OS clobbers: memory, flags
        # Join constraints. The output constraint (if any) must come first in LLVM.
        # But we'll just join them in the order they appear.
        constraint_str = ",".join(constraints) + ",~{memory},~{dirflag},~{fpsr},~{flags}"
        print(f"DEBUG: constraint_str='{constraint_str}'")
        
        fn_type = ir.FunctionType(ret_type, arg_types)
        asm_fn = ir.InlineAsm(fn_type, node.assembly_string, constraint_str, side_effect=True)
        result = self.builder.call(asm_fn, llvm_args)
        
        # If there's an 'out' argument, it should be an assignment target.
        # However, for our simple implementation, if an 'out' param is used,
        # we try to store the result into it if it was a pointer.
        # In a fully robust compiler we'd resolve it as an l-value.
        return result

    # ==========================================
    # Statements
    # ==========================================

    def generate_Block(self, node: ast.Block):
        for stmt in node.statements:
            self.generate(stmt)

    def generate_ReturnStatement(self, node: ast.ReturnStatement):
        if node.value:
            val = self.generate(node.value)
            # Auto-cast return value to match function's return type
            func = self.builder.function
            ret_type = func.type.pointee.return_type
            if val.type != ret_type:
                if isinstance(val.type, ir.IntType) and isinstance(ret_type, ir.IntType):
                    if val.type.width > ret_type.width:
                        val = self.builder.trunc(val, ret_type)
                    else:
                        val = self.builder.zext(val, ret_type)
                elif isinstance(val.type, ir.PointerType) and isinstance(ret_type, ir.IntType):
                    val = self.builder.ptrtoint(val, ret_type)
                elif isinstance(val.type, ir.IntType) and isinstance(ret_type, ir.PointerType):
                    val = self.builder.inttoptr(val, ret_type)
                else:
                    val = self.builder.bitcast(val, ret_type)
            self.builder.ret(val)
        else:
            self.builder.ret_void()

    def generate_VariableDeclaration(self, node: ast.VariableDeclaration):
        val = None
        if node.initializer:
            val = self.generate(node.initializer)

        # If the initializer already produced an alloca (array/struct literal),
        # register it directly rather than creating a double-pointer.
        if val is not None and isinstance(val.type, ir.PointerType):
            inner = val.type.pointee
            if isinstance(inner, (ir.ArrayType, ir.LiteralStructType)):
                # val IS the alloca — just register it
                self.variables[node.name.name] = val
                return

        # Determine the LLVM type
        if node.type_annotation:
            llvm_type = self.get_llvm_type(node.type_annotation)
        elif val is not None:
            llvm_type = val.type
        else:
            llvm_type = self.get_llvm_type("int")

        # Handle top-level global variables
        if self.builder is None or self.builder.block is None:
            gv = ir.GlobalVariable(self.module, llvm_type, name=node.name.name)
            if val is not None and isinstance(val, ir.Constant):
                gv.initializer = val
            else:
                gv.initializer = ir.Constant(llvm_type, 0)
            self.variables[node.name.name] = gv
            return

        ptr = self.builder.alloca(llvm_type, name=node.name.name)
        self.variables[node.name.name] = ptr

        if val is not None:
            # Auto-cast initializer to match the declared type
            if val.type != llvm_type:
                if isinstance(val.type, ir.IntType) and isinstance(llvm_type, ir.IntType):
                    if val.type.width > llvm_type.width:
                        val = self.builder.trunc(val, llvm_type)
                    else:
                        val = self.builder.zext(val, llvm_type)
                elif isinstance(val.type, ir.PointerType) and isinstance(llvm_type, ir.IntType):
                    val = self.builder.ptrtoint(val, llvm_type)
                elif isinstance(val.type, ir.IntType) and isinstance(llvm_type, ir.PointerType):
                    val = self.builder.inttoptr(val, llvm_type)
                else:
                    val = self.builder.bitcast(val, llvm_type)
            self.builder.store(val, ptr)

    def generate_Assignment(self, node: ast.Assignment):
        val = self.generate(node.value)

        if isinstance(node.target, ast.Identifier):
            ptr = self.variables[node.target.name]
            # Type-coerce if sizes differ (e.g. assign i64 into i8 slot)
            ptr_elem_type = ptr.type.pointee
            if val.type != ptr_elem_type:
                if isinstance(val.type, ir.IntType) and isinstance(ptr_elem_type, ir.IntType):
                    if val.type.width > ptr_elem_type.width:
                        val = self.builder.trunc(val, ptr_elem_type)
                    else:
                        val = self.builder.zext(val, ptr_elem_type)
            self.builder.store(val, ptr)

        elif isinstance(node.target, ast.PointerDereference):
            ptr = self.generate(node.target.pointer_expr)
            
            target_type_str = getattr(node.target, 'target_type', 'int')
            llvm_target_type = self.get_llvm_type(target_type_str)
            
            # Type-coerce the value if sizes differ
            if val.type != llvm_target_type:
                if isinstance(val.type, ir.IntType) and isinstance(llvm_target_type, ir.IntType):
                    if val.type.width > llvm_target_type.width:
                        val = self.builder.trunc(val, llvm_target_type)
                    else:
                        val = self.builder.zext(val, llvm_target_type)
                        
            if isinstance(ptr.type, ir.IntType):
                # Cast the int pointer to the target type of the pointer, not the generic value type
                ptr = self.builder.inttoptr(ptr, ir.PointerType(llvm_target_type))
            self.builder.store(val, ptr)

        elif isinstance(node.target, ast.ArrayIndex):
            arr_ptr = self._resolve_ptr(node.target.array)
            idx     = self.generate(node.target.index)
            zero    = ir.Constant(ir.IntType(32), 0)
            idx32   = self.builder.trunc(idx, ir.IntType(32)) if isinstance(idx.type, ir.IntType) and idx.type.width == 64 else idx
            elem_ptr = self.builder.gep(arr_ptr, [zero, idx32], inbounds=True)
            
            ptr_elem_type = elem_ptr.type.pointee
            if val.type != ptr_elem_type:
                if isinstance(val.type, ir.IntType) and isinstance(ptr_elem_type, ir.IntType):
                    if val.type.width > ptr_elem_type.width:
                        val = self.builder.trunc(val, ptr_elem_type)
                    else:
                        val = self.builder.zext(val, ptr_elem_type)
            
            self.builder.store(val, elem_ptr)

        elif isinstance(node.target, ast.MemberAccess):
            struct_ptr = self._resolve_ptr(node.target.object)
            struct_name = self._get_struct_name_from_ptr(struct_ptr)
            if struct_name:
                field_names = self.struct_fields[struct_name]
                field_idx   = field_names.index(node.target.property.name)
                zero        = ir.Constant(ir.IntType(32), 0)
                idx         = ir.Constant(ir.IntType(32), field_idx)
                field_ptr   = self.builder.gep(struct_ptr, [zero, idx], inbounds=True)
                
                ptr_elem_type = field_ptr.type.pointee
                if val.type != ptr_elem_type:
                    if isinstance(val.type, ir.IntType) and isinstance(ptr_elem_type, ir.IntType):
                        if val.type.width > ptr_elem_type.width:
                            val = self.builder.trunc(val, ptr_elem_type)
                        else:
                            val = self.builder.zext(val, ptr_elem_type)
                            
                self.builder.store(val, field_ptr)

        return val

    def generate_IfStatement(self, node: ast.IfStatement):
        """Generate if/elif/else as a chain of conditional branches."""
        func     = self.builder.function
        cond_val = self.generate(node.condition)

        # LLVM requires i1 for branches
        if not isinstance(cond_val.type, ir.IntType) or cond_val.type.width != 1:
            cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(cond_val.type, 0))

        # Create blocks
        then_bb  = func.append_basic_block("if.then")
        merge_bb = func.append_basic_block("if.merge")

        # Elif chain / else
        if node.elif_branches or node.else_block:
            else_bb = func.append_basic_block("if.else")
        else:
            else_bb = merge_bb

        self.builder.cbranch(cond_val, then_bb, else_bb)

        # then block
        self.builder.position_at_end(then_bb)
        for stmt in node.then_block.statements:
            self.generate(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        # elif chain
        current_else = else_bb
        for i, (elif_cond, elif_block) in enumerate(node.elif_branches):
            if current_else is not merge_bb:
                self.builder.position_at_end(current_else)
                ec = self.generate(elif_cond)
                if not isinstance(ec.type, ir.IntType) or ec.type.width != 1:
                    ec = self.builder.icmp_signed('!=', ec, ir.Constant(ec.type, 0))
                elif_then_bb = func.append_basic_block(f"elif.then.{i}")
                if i + 1 < len(node.elif_branches):
                    next_else = func.append_basic_block(f"elif.else.{i}")
                elif node.else_block:
                    next_else = func.append_basic_block("else")
                else:
                    next_else = merge_bb
                self.builder.cbranch(ec, elif_then_bb, next_else)
                self.builder.position_at_end(elif_then_bb)
                for stmt in elif_block.statements:
                    self.generate(stmt)
                if not self.builder.block.is_terminated:
                    self.builder.branch(merge_bb)
                current_else = next_else

        # else block
        if node.else_block and current_else is not merge_bb:
            self.builder.position_at_end(current_else)
            for stmt in node.else_block.statements:
                self.generate(stmt)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        self.builder.position_at_end(merge_bb)

    def generate_MatchStatement(self, node: ast.MatchStatement):
        """Generate match statement as an LLVM switch."""
        func = self.builder.function
        target_val = self.generate(node.target)

        merge_bb = func.append_basic_block("match.merge")
        default_bb = func.append_basic_block("match.default")

        # Find wildcard if any
        wildcard_case = None
        for case in node.cases:
            if isinstance(case.pattern, ast.Identifier) and case.pattern.name == '_':
                wildcard_case = case
                break

        switch_inst = self.builder.switch(target_val, default_bb)

        for case in node.cases:
            if case is wildcard_case:
                continue

            case_bb = func.append_basic_block("match.case")
            
            # case.pattern is an EnumVariant. evaluate it to get the constant value.
            case_val = self.generate(case.pattern)
            switch_inst.add_case(case_val, case_bb)

            # Generate case body
            self.builder.position_at_end(case_bb)
            for stmt in case.body.statements:
                self.generate(stmt)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        # Generate default block body (either the wildcard body, or just branch to merge)
        self.builder.position_at_end(default_bb)
        if wildcard_case:
            for stmt in wildcard_case.body.statements:
                self.generate(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        self.builder.position_at_end(merge_bb)

    def generate_WhileStatement(self, node: ast.WhileStatement):
        """Generate while loop as cond_bb → body_bb → cond_bb loop."""
        func    = self.builder.function
        cond_bb = func.append_basic_block("while.cond")
        body_bb = func.append_basic_block("while.body")
        end_bb  = func.append_basic_block("while.end")

        self.builder.branch(cond_bb)

        # Condition block
        self.builder.position_at_end(cond_bb)
        cond_val = self.generate(node.condition)
        if not isinstance(cond_val.type, ir.IntType) or cond_val.type.width != 1:
            cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(cond_val.type, 0))
        self.builder.cbranch(cond_val, body_bb, end_bb)

        # Body block
        self.builder.position_at_end(body_bb)
        for stmt in node.body.statements:
            self.generate(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)

        self.builder.position_at_end(end_bb)

    def generate_LockBlock(self, node: ast.LockBlock):
        # Concurrency semantics — body is generated normally (actual locking at runtime via stdlib)
        self.generate(node.body)

    def generate_UnsafeBlock(self, node: ast.UnsafeBlock):
        """Generate code for unsafe block. In LLVM IR this is transparent."""
        self.generate(node.body)

    def generate_PointerDereference(self, node: ast.PointerDereference):
        """Generate load from a pointer."""
        ptr = self.generate(node.pointer_expr)
        
        # Determine the target type from the AST node (set during semantic analysis)
        target_type_str = getattr(node, 'target_type', 'int')
        llvm_target_type = self.get_llvm_type(target_type_str)
        
        if isinstance(ptr.type, ir.IntType):
            ptr = self.builder.inttoptr(ptr, ir.PointerType(llvm_target_type))
        return self.builder.load(ptr)

    def generate_AddressOf(self, node: ast.AddressOf):
        """Generate address-of operation."""
        if isinstance(node.target, ast.Identifier):
            name = node.target.name
            if name in self.variables:
                return self.variables[name]
            raise Exception(f"Undefined variable in address-of: {name}")
        raise Exception("AddressOf target must be an identifier in current implementation")

    # ==========================================
    # Expressions
    # ==========================================

    def generate_NumberLiteral(self, node: ast.NumberLiteral):
        return ir.Constant(ir.IntType(64), int(node.value))

    def generate_BoolLiteral(self, node: ast.BoolLiteral):
        return ir.Constant(ir.IntType(64), 1 if node.value else 0)

    def create_global_string(self, val: str):
        text = val.replace('\\n', '\n').replace('\\t', '\t') + '\0'
        byte_arr = bytearray(text, 'utf8')
        c_str_ty = ir.ArrayType(ir.IntType(8), len(byte_arr))
        name = f".str.{self._str_counter}"
        self._str_counter += 1

        global_str = ir.GlobalVariable(self.module, c_str_ty, name=name)
        global_str.linkage = "internal"
        global_str.global_constant = True
        global_str.initializer = ir.Constant(c_str_ty, byte_arr)
        if self.builder and self.builder.block:
            return self.builder.bitcast(global_str, ir.PointerType(ir.IntType(8)))
        return ir.Constant.bitcast(global_str, ir.PointerType(ir.IntType(8)))

    def generate_StringLiteral(self, node: ast.StringLiteral):
        return self.create_global_string(node.value)

    def generate_Identifier(self, node: ast.Identifier):
        if node.name == "pass":
            return ir.Constant(ir.IntType(64), 0)
        if node.name in self.variables:
            ptr = self.variables[node.name]
            return self.builder.load(ptr, name=node.name + "_val")
        elif node.name in self.module.globals:
            return self.builder.load(self.module.globals[node.name], name=node.name + "_val")
        return self.create_global_string(node.name)

    def generate_BinaryOp(self, node: ast.BinaryOp):
        left  = self.generate(node.left)
        right = self.generate(node.right)

        # Size-normalise int operands so LLVM types match
        if isinstance(left.type, ir.IntType) and isinstance(right.type, ir.IntType):
            if left.type.width != right.type.width:
                target_width = max(left.type.width, right.type.width)
                target_t = ir.IntType(target_width)
                if left.type.width < target_width:
                    left  = self.builder.zext(left, target_t)
                else:
                    right = self.builder.zext(right, target_t)

        op = node.operator
        if op == '+':  return self.builder.add(left, right,  name="add")
        if op == '-':  return self.builder.sub(left, right,  name="sub")
        if op == '*':  return self.builder.mul(left, right,  name="mul")
        if op == '/':  return self.builder.sdiv(left, right, name="div")
        if op == '&':  return self.builder.and_(left, right, name="and")
        if op == '|':  return self.builder.or_(left, right,  name="or")
        if op == '^':  return self.builder.xor(left, right,  name="xor")
        if op == '<<': return self.builder.shl(left, right,  name="shl")
        if op == '>>': return self.builder.ashr(left, right, name="shr")
        if op == '<':  return self.builder.icmp_signed('<',  left, right, name="lt")
        if op == '>':  return self.builder.icmp_signed('>',  left, right, name="gt")
        if op == '==': return self.builder.icmp_signed('==', left, right, name="eq")
        if op == '!=': return self.builder.icmp_signed('!=', left, right, name="neq")
        raise NotImplementedError(f"Operator '{op}' not implemented in IR")

    def generate_FunctionCall(self, node: ast.FunctionCall):
        # Hardware intrinsics: hw.outb / hw.inb
        if isinstance(node.callee, ast.MemberAccess):
            obj = node.callee.object
            if isinstance(obj, ast.Identifier) and obj.name == "hw":
                prop = node.callee.property.name
                if prop == "outb":
                    port = self.generate(node.arguments[0])
                    val  = self.generate(node.arguments[1])
                    outb_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(16), ir.IntType(8)])
                    asm_obj = ir.InlineAsm(outb_ty, "outb $1, $0", "N{dx},{al}", side_effect=True)
                    return self.builder.call(asm_obj, [
                        self.builder.trunc(port, ir.IntType(16)),
                        self.builder.trunc(val,  ir.IntType(8)),
                    ])
                if prop == "inb":
                    port   = self.generate(node.arguments[0])
                    inb_ty = ir.FunctionType(ir.IntType(8), [ir.IntType(16)])
                    asm_obj = ir.InlineAsm(inb_ty, "inb $1, $0", "={al},N{dx}", side_effect=True)
                    return self.builder.call(asm_obj, [self.builder.trunc(port, ir.IntType(16))])

            # Generic member call (library methods, etc.)
            self.generate(node.callee)
            args = [self.generate(a) for a in node.arguments]
            return ir.Constant(ir.IntType(64), 0)

        # Standard function call
        if isinstance(node.callee, ast.Identifier):
            name = node.callee.name
            if name not in self.functions:
                raise Exception(f"Undefined function: '{name}'")
            func = self.functions[name]
            args = [self.generate(a) for a in node.arguments]
            # Coerce arg types if needed
            coerced = []
            for arg, param_type in zip(args, func.args):
                if arg.type != param_type.type:
                    if isinstance(arg.type, ir.IntType) and isinstance(param_type.type, ir.IntType):
                        if arg.type.width > param_type.type.width:
                            arg = self.builder.trunc(arg, param_type.type)
                        else:
                            arg = self.builder.zext(arg, param_type.type)
                    elif isinstance(arg.type, ir.PointerType) and isinstance(param_type.type, ir.IntType):
                        arg = self.builder.ptrtoint(arg, param_type.type)
                    elif isinstance(arg.type, ir.IntType) and isinstance(param_type.type, ir.PointerType):
                        arg = self.builder.inttoptr(arg, param_type.type)
                    else:
                        arg = self.builder.bitcast(arg, param_type.type)
                coerced.append(arg)
            return self.builder.call(func, coerced)

        return ir.Constant(ir.IntType(64), 0)

    def generate_MemberAccess(self, node: ast.MemberAccess):
        """Load a struct field or resolve an enum variant."""
        # Enum variant: Status.OK → constant integer
        if isinstance(node.object, ast.Identifier) and node.object.name in self.enum_variants:
            variants = self.enum_variants[node.object.name]
            if node.property.name in variants:
                return ir.Constant(ir.IntType(32), variants[node.property.name])

        # Struct field load
        if isinstance(node.object, ast.Identifier) and node.object.name in self.variables:
            ptr = self.variables[node.object.name]
            # Determine struct type name from ptr
            struct_name = self._get_struct_name_from_ptr(ptr)
            if struct_name and struct_name in self.struct_fields:
                field_names = self.struct_fields[struct_name]
                if node.property.name in field_names:
                    field_idx = field_names.index(node.property.name)
                    zero      = ir.Constant(ir.IntType(32), 0)
                    idx       = ir.Constant(ir.IntType(32), field_idx)
                    field_ptr = self.builder.gep(ptr, [zero, idx], inbounds=True)
                    return self.builder.load(field_ptr)

        # hw namespace — no-op value
        return ir.Constant(ir.IntType(64), 0)



    def generate_Cast(self, node: ast.Cast):
        val         = self.generate(node.expr)
        target_type = self.get_llvm_type(node.target_type)

        if val.type == target_type:
            return val
        if isinstance(val.type, ir.PointerType) and isinstance(target_type, ir.IntType):
            return self.builder.ptrtoint(val, target_type)
        if isinstance(val.type, ir.IntType) and isinstance(target_type, ir.PointerType):
            return self.builder.inttoptr(val, target_type)
        if isinstance(val.type, ir.IntType) and isinstance(target_type, ir.IntType):
            if val.type.width > target_type.width:
                return self.builder.trunc(val, target_type)
            else:
                return self.builder.zext(val, target_type)
        return self.builder.bitcast(val, target_type)

    def generate_SizeOf(self, node: ast.SizeOf):
        target_type = self.get_llvm_type(node.target_type)
        null_ptr    = ir.Constant(ir.PointerType(target_type), None)
        size_ptr    = self.builder.gep(null_ptr, [ir.Constant(ir.IntType(32), 1)])
        return self.builder.ptrtoint(size_ptr, ir.IntType(64))

    # ==========================================
    # Phase 7: Array and Struct Literals
    # ==========================================

    def generate_ArrayLiteral(self, node: ast.ArrayLiteral):
        """Allocate an array on the stack, fill with element values, return pointer."""
        if not node.elements:
            arr_type = ir.ArrayType(ir.IntType(64), 0)
            return self.builder.alloca(arr_type)

        elements = [self.generate(e) for e in node.elements]
        arr_type = ir.ArrayType(elements[0].type, len(elements))
        ptr      = self.builder.alloca(arr_type)

        zero = ir.Constant(ir.IntType(32), 0)
        for i, val in enumerate(elements):
            idx      = ir.Constant(ir.IntType(32), i)
            elem_ptr = self.builder.gep(ptr, [zero, idx], inbounds=True)
            self.builder.store(val, elem_ptr)

        return ptr

    def generate_ArrayIndex(self, node: ast.ArrayIndex):
        """Load an element from an array alloca ( [N x T]* )."""
        arr_ptr = self._resolve_ptr(node.array)
        idx     = self.generate(node.index)
        # Normalise index to i32
        if isinstance(idx.type, ir.IntType) and idx.type.width != 32:
            idx = self.builder.trunc(idx, ir.IntType(32)) if idx.type.width > 32 else self.builder.zext(idx, ir.IntType(32))
        zero     = ir.Constant(ir.IntType(32), 0)
        # arr_ptr is [N x T]* — GEP with [0, i] gives T*
        elem_ptr = self.builder.gep(arr_ptr, [zero, idx], inbounds=True)
        return self.builder.load(elem_ptr)

    def generate_StructLiteral(self, node: ast.StructLiteral):
        """Stack-allocate a struct and fill in each field."""
        struct_type = self.struct_types[node.struct_name]
        field_names = self.struct_fields[node.struct_name]
        ptr         = self.builder.alloca(struct_type, name=node.struct_name + "_lit")

        field_map = {name: val for (name, val) in node.fields}
        zero      = ir.Constant(ir.IntType(32), 0)

        for i, fname in enumerate(field_names):
            if fname in field_map:
                val  = self.generate(field_map[fname])
                idx  = ir.Constant(ir.IntType(32), i)
                # Struct GEP: ptr is { T0, T1, ... }* — use [0, field_idx]
                fptr = self.builder.gep(ptr, [zero, idx], inbounds=True)
                # Coerce element type if needed
                expected_type = struct_type.elements[i]
                if val.type != expected_type and isinstance(val.type, ir.IntType) and isinstance(expected_type, ir.IntType):
                    val = self.builder.trunc(val, expected_type) if val.type.width > expected_type.width else self.builder.zext(val, expected_type)
                self.builder.store(val, fptr)

        return ptr

    def generate_EnumVariant(self, node: ast.EnumVariant):
        variants = self.enum_variants[node.enum_name]
        return ir.Constant(ir.IntType(32), variants[node.variant])

    # ==========================================
    # Helpers
    # ==========================================

    def _resolve_ptr(self, node: ast.ASTNode) -> ir.Value:
        """Return the raw alloca pointer without loading the value."""
        if isinstance(node, ast.Identifier) and node.name in self.variables:
            return self.variables[node.name]
        # For other expressions, generate and hope it's already a pointer
        return self.generate(node)

    def _get_struct_name_from_ptr(self, ptr: ir.Value) -> Optional[str]:
        """Reverse-lookup the struct name from its LLVM type."""
        try:
            pointee = ptr.type.pointee
            for name, st in self.struct_types.items():
                if st == pointee:
                    return name
        except Exception:
            pass
        return None

    def _emit_osext_entry(self, entry_type: int, target: str = "", fn_ptr: ir.Value = None,
                          meta_name: str = "", meta_version: str = "", meta_author: str = ""):
        # Struct: {i32, i32, [32 x i8], i8*, [32 x i8], [16 x i8], [32 x i8]}
        arr32 = ir.ArrayType(ir.IntType(8), 32)
        arr16 = ir.ArrayType(ir.IntType(8), 16)
        struct_ty = ir.LiteralStructType([
            ir.IntType(32), ir.IntType(32), arr32, ir.PointerType(ir.IntType(8)),
            arr32, arr16, arr32
        ])
        
        def pad_str(s: str, length: int) -> list:
            b = s.encode('utf8')
            b = b[:length-1] + b'\0'
            b += b'\0' * (length - len(b))
            return [ir.Constant(ir.IntType(8), c) for c in b]

        c_target = ir.Constant(arr32, pad_str(target, 32))
        c_name = ir.Constant(arr32, pad_str(meta_name, 32))
        c_ver = ir.Constant(arr16, pad_str(meta_version, 16))
        c_auth = ir.Constant(arr32, pad_str(meta_author, 32))
        
        c_magic = ir.Constant(ir.IntType(32), 0x4C455800)
        c_type = ir.Constant(ir.IntType(32), entry_type)
        
        if fn_ptr is not None:
            c_fn = fn_ptr
            # Cast to i8* if needed
            if c_fn.type != ir.PointerType(ir.IntType(8)):
                c_fn = ir.Constant.bitcast(c_fn, ir.PointerType(ir.IntType(8)))
        else:
            c_fn = ir.Constant(ir.PointerType(ir.IntType(8)), None)
            
        init_val = ir.Constant(struct_ty, [c_magic, c_type, c_target, c_fn, c_name, c_ver, c_auth])
        
        gv = ir.GlobalVariable(self.module, struct_ty, name=f"__osext_entry_{self._str_counter}")
        self._str_counter += 1
        gv.section = ".osext_meta"
        gv.initializer = init_val
        # Needs to be "appending" or "weak" to avoid internal symbols getting optimized out?
        # Let's use "linkonce_odr" or "internal" with used attribute, or just "weak"
        gv.linkage = "weak"

    def generate_ExtensionMarkerStatement(self, node: ast.ExtensionMarkerStatement):
        types = {"extend": 1, "app": 2, "standalone": 3, "driver": 4, "service": 5}
        t = types.get(node.marker_type, 0)
        self._emit_osext_entry(t, target=node.target_module or "")

    def generate_ExtensionMetaStatement(self, node: ast.ExtensionMetaStatement):
        self._emit_osext_entry(10, meta_name=node.name, meta_version=node.version, meta_author=node.author)

    # ==========================================
    # OsGUI Codegen Handlers
    # ==========================================

    def generate_GuiAppDeclaration(self, node: ast.GuiAppDeclaration):
        app_name = node.name.name
        # Emit global layout descriptor variable
        i8_ptr = ir.PointerType(ir.IntType(8))
        c_name = self.create_global_string(app_name)
        gv = ir.GlobalVariable(self.module, i8_ptr, name=f"__guiapp_{app_name}")
        gv.initializer = c_name
        if node.body:
            self.generate(node.body)

    def generate_GuiWindowDeclaration(self, node: ast.GuiWindowDeclaration):
        win_name = node.name.name
        i8_ptr = ir.PointerType(ir.IntType(8))
        c_name = self.create_global_string(win_name)
        gv = ir.GlobalVariable(self.module, i8_ptr, name=f"__guiwin_{win_name}")
        gv.initializer = c_name
        if node.body:
            self.generate(node.body)

    def generate_GuiLayoutElement(self, node: ast.GuiLayoutElement):
        elem_name = f"{node.element_type}_{node.name.name}"
        i8_ptr = ir.PointerType(ir.IntType(8))
        c_name = self.create_global_string(elem_name)
        gv = ir.GlobalVariable(self.module, i8_ptr, name=f"__guielem_{self._str_counter}")
        self._str_counter += 1
        gv.initializer = c_name
        if node.body:
            self.generate(node.body)

    # ==========================================
    # OS Heaven Codegen Handlers
    # ==========================================

    def generate_ProcessDeclaration(self, node: ast.ProcessDeclaration):
        proc_name = node.name.name
        i8_ptr = ir.PointerType(ir.IntType(8))
        c_name = self.create_global_string(proc_name)
        gv = ir.GlobalVariable(self.module, i8_ptr, name=f"__process_{proc_name}")
        gv.initializer = c_name
        if node.body:
            self.generate(node.body)

    def generate_PacketDeclaration(self, node: ast.PacketDeclaration):
        field_types = []
        for fname, ftype in node.fields:
            field_types.append(self.get_llvm_type(ftype))
        st = ir.LiteralStructType(field_types, packed=True)
        self.struct_types[node.name.name] = st
        self.struct_fields[node.name.name] = [f[0] for f in node.fields]

    def generate_VfsMountDeclaration(self, node: ast.VfsMountDeclaration):
        vfs_name = node.name.name
        i8_ptr = ir.PointerType(ir.IntType(8))
        c_name = self.create_global_string(vfs_name)
        gv = ir.GlobalVariable(self.module, i8_ptr, name=f"__vfs_{vfs_name}")
        gv.initializer = c_name

    def generate_PanicStatement(self, node: ast.PanicStatement):
        vga_base = self.builder.inttoptr(ir.Constant(ir.IntType(64), 0xB8000), ir.PointerType(ir.IntType(8)))
        self.builder.store(ir.Constant(ir.IntType(8), 75), vga_base)
        col_ptr = self.builder.gep(vga_base, [ir.Constant(ir.IntType(64), 1)])
        self.builder.store(ir.Constant(ir.IntType(8), 0x4F), col_ptr)
        fn_type = ir.FunctionType(ir.VoidType(), [])
        asm_fn = ir.InlineAsm(fn_type, "hlt", "", side_effect=True)
        self.builder.call(asm_fn, [])

    # ==========================================
    # Output
    # ==========================================

    def get_ir(self) -> str:
        return str(self.module)

    def save_object_file(self, filename: str, target_triple: str = "x86_64-unknown-none-elf"):
        self.module.triple = target_triple
        target         = llvm.Target.from_triple(target_triple)
        target_machine = target.create_target_machine(reloc='pic', codemodel='default')
        backing_mod    = llvm.parse_assembly(str(self.module))
        backing_mod.verify()
        obj_code       = target_machine.emit_object(backing_mod)
        with open(filename, 'wb') as f:
            f.write(obj_code)
