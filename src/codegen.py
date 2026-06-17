import llvmlite.ir as ir
import llvmlite.binding as llvm
import src.ast as ast
from typing import Dict, Any, Optional, List, Tuple

class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="os_module")
        self.module.triple = llvm.get_default_triple()

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

        # Initialize LLVM for native target + inline asm
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
        struct_type = ir.LiteralStructType(field_types, packed=node.is_hwmap)
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
        if node.is_interrupt:
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

        block         = func.append_basic_block(name="entry")
        self.builder  = ir.IRBuilder(block)
        self.variables = {}

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
            # outb(port: u16, value: u8) — x86: outb %al, %dx
            port = args[0]
            val  = args[1]
            if port.type != i16:
                port = self.builder.trunc(port, i16) if port.type.width > 16 else self.builder.zext(port, i16)
            if val.type != i8:
                val = self.builder.trunc(val, i8) if val.type.width > 8 else self.builder.zext(val, i8)
            fn_type = ir.FunctionType(void, [i16, i8])
            # Constraints: two inputs ({dx} = port, {al} = byte), clobber flags
            asm_fn  = ir.InlineAsm(fn_type, "outb %al,%dx", "{dx},{al},~{dirflag},~{fpsr},~{flags}",
                                   side_effect=True)
            self.builder.call(asm_fn, [port, val])

        elif n in ("inb", "inw", "inl"):
            # inb(port: u16) -> u8 — x86: inb %dx, %al
            port = args[0]
            if port.type != i16:
                port = self.builder.trunc(port, i16) if port.type.width > 16 else self.builder.zext(port, i16)
            fn_type = ir.FunctionType(i8, [i16])
            # Constraints: one input ({dx} = port), output in al
            asm_fn  = ir.InlineAsm(fn_type, "inb %dx,%al", "={al},{dx},~{dirflag},~{fpsr},~{flags}",
                                   side_effect=True)
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

    # ==========================================
    # Expressions
    # ==========================================

    def generate_NumberLiteral(self, node: ast.NumberLiteral):
        return ir.Constant(ir.IntType(64), int(node.value))

    def generate_BoolLiteral(self, node: ast.BoolLiteral):
        return ir.Constant(ir.IntType(64), 1 if node.value else 0)

    def generate_StringLiteral(self, node: ast.StringLiteral):
        text      = node.value.replace('\\n', '\n').replace('\\t', '\t') + '\0'
        byte_arr  = bytearray(text, 'utf8')
        c_str_ty  = ir.ArrayType(ir.IntType(8), len(byte_arr))
        name      = f".str.{self._str_counter}"
        self._str_counter += 1

        global_str = ir.GlobalVariable(self.module, c_str_ty, name=name)
        global_str.linkage        = "internal"
        global_str.global_constant = True
        global_str.initializer    = ir.Constant(c_str_ty, byte_arr)
        return self.builder.bitcast(global_str, ir.PointerType(ir.IntType(8)))

    def generate_Identifier(self, node: ast.Identifier):
        if node.name in self.variables:
            ptr = self.variables[node.name]
            return self.builder.load(ptr, name=node.name + "_val")
        raise Exception(f"Undefined variable in IR: '{node.name}'")

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

    # ==========================================
    # Output
    # ==========================================

    def get_ir(self) -> str:
        return str(self.module)

    def save_object_file(self, filename: str):
        target         = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine(reloc='pic', codemodel='default')
        backing_mod    = llvm.parse_assembly(str(self.module))
        backing_mod.verify()
        obj_code       = target_machine.emit_object(backing_mod)
        with open(filename, 'wb') as f:
            f.write(obj_code)
