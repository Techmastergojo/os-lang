from typing import Dict, Optional, Any, List
import src.ast as ast

class SemanticError(Exception):
    pass

class Symbol:
    def __init__(self, name: str, type_name: str, is_mut: bool = False,
                 is_shared: bool = False, param_types: Optional[List[str]] = None,
                 return_type: Optional[str] = None):
        self.name = name
        self.type_name = type_name
        self.is_mut = is_mut
        self.is_shared = is_shared
        self.param_types = param_types or []
        self.return_type = return_type or "void"

class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.symbols: Dict[str, Symbol] = {}
        self.parent = parent

    def define(self, symbol: Symbol):
        if symbol.name in self.symbols:
            raise SemanticError(f"Duplicate symbol '{symbol.name}' in current scope.")
        self.symbols[symbol.name] = symbol

    def resolve(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        return None

class SemanticAnalyzer:
    # ── OS intrinsics registry ────────────────────────────────────────────
    OS_INTRINSICS: Dict[str, tuple] = {
        "halt":           ([], "void"),
        "cli":            ([], "void"),
        "sti":            ([], "void"),
        "rdtsc":          ([], "u64"),
        "memory_barrier": ([], "void"),
        "cpuid":          (["u32"], "u32"),     # returns EAX (simplified)
        "outb":           (["u16", "u8"],  "void"),
        "outw":           (["u16", "u16"], "void"),
        "outl":           (["u16", "u32"], "void"),
        "inb":            (["u16"], "u8"),
        "inw":            (["u16"], "u16"),
        "inl":            (["u16"], "u32"),
        "volatile_load":  (["ptr"], "u64"),
        "volatile_store": (["ptr", "u64"], "void"),
        "atomic_cmpxchg": (["ptr", "u64", "u64"], "u64"),
        "atomic_xchg":    (["ptr", "u64"], "u64"),
        "atomic_add":     (["ptr", "u64"], "u64"),
        "atomic_sub":     (["ptr", "u64"], "u64"),
    }

    def __init__(self):
        self.current_scope = SymbolTable()
        self.in_unsafe_block = False
        self.locked_variables = set()
        # Registry of declared structs: name -> {field: type}
        self.structs: Dict[str, Dict[str, str]] = {}
        # Registry of declared enums: name -> [variant, ...]
        self.enums: Dict[str, List[str]] = {}

        # Pre-define built-in hardware accessor
        self.current_scope.define(Symbol("hw", "hwmap", False, False))

        # ── Phase 9: pre-register built-in OS structs ────────────────────
        self.structs["InterruptFrame"] = {
            "ip":     "u64",   # instruction pointer at time of interrupt
            "cs":     "u64",   # code segment
            "flags":  "u64",   # CPU flags (RFLAGS)
            "sp":     "u64",   # stack pointer
            "ss":     "u64",   # stack segment
        }
        self.structs["CpuState"] = {
            "rax": "u64", "rbx": "u64", "rcx": "u64", "rdx": "u64",
            "rsi": "u64", "rdi": "u64", "rbp": "u64", "rsp": "u64",
            "r8":  "u64", "r9":  "u64", "r10": "u64", "r11": "u64",
            "r12": "u64", "r13": "u64", "r14": "u64", "r15": "u64",
        }

        # ── Phase 9: pre-define OS hardware constants ─────────────────────
        hw_constants = {
            "PORT_PIC1_CMD":  0x20, "PORT_PIC1_DATA": 0x21,
            "PORT_PIC2_CMD":  0xA0, "PORT_PIC2_DATA": 0xA1,
            "PORT_PS2_DATA":  0x60, "PORT_PS2_CMD":   0x64,
            "PORT_UART_COM1": 0x3F8,
            "PORT_VGA_CTRL":  0x3D4, "PORT_VGA_DATA": 0x3D5,
            "IRQ_TIMER": 0, "IRQ_KEYBOARD": 1, "IRQ_UART1": 4,
        }
        for const_name, _ in hw_constants.items():
            self.current_scope.define(Symbol(const_name, "int", False, False))

    def enter_scope(self):
        self.current_scope = SymbolTable(parent=self.current_scope)

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def analyze(self, node: ast.ASTNode) -> str:
        """Dispatch to the correct analyze_* method."""
        method_name = f'analyze_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_analyze)
        return visitor(node)

    def generic_analyze(self, node: ast.ASTNode) -> str:
        raise NotImplementedError(f"No analyze_{type(node).__name__} method in SemanticAnalyzer")

    # ==========================================
    # Core Visitors
    # ==========================================

    def analyze_Program(self, node: ast.Program) -> str:
        for stmt in node.statements:
            self.analyze(stmt)
        return "void"

    def analyze_Block(self, node: ast.Block) -> str:
        self.enter_scope()
        for stmt in node.statements:
            self.analyze(stmt)
        self.exit_scope()
        return "void"

    # Integer types that are mutually assignable (width-compatible numerics)
    INT_TYPES = {"int", "u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64"}

    def analyze_VariableDeclaration(self, node: ast.VariableDeclaration) -> str:
        inferred_type = "unknown"
        if node.initializer:
            inferred_type = self.analyze(node.initializer)

        final_type = node.type_annotation or inferred_type

        if node.type_annotation and inferred_type not in ("unknown", "void"):
            ann = node.type_annotation
            # Allow any integer-width type to be assigned to any other integer type
            is_numeric_compat = ann in self.INT_TYPES and inferred_type in self.INT_TYPES
            # Allow int literal for pointer / struct / array initialization
            is_ptr_assign    = (ann.startswith("ptr") or ann.startswith("*")) and inferred_type == "int"
            is_struct_assign = ann in self.structs and inferred_type == "int"
            is_array_assign  = ann.startswith("[") and inferred_type.startswith("[")
            is_enum_assign   = ann in self.enums and inferred_type in self.enums

            if (ann != inferred_type and not is_numeric_compat and not is_ptr_assign
                    and not is_struct_assign and not is_array_assign and not is_enum_assign):
                raise SemanticError(
                    f"Type mismatch: Cannot assign '{inferred_type}' to variable of type '{ann}'.")

        symbol = Symbol(node.name.name, final_type, node.is_mut, node.is_shared)
        self.current_scope.define(symbol)
        return "void"

    def analyze_Assignment(self, node: ast.Assignment) -> str:
        if isinstance(node.target, ast.Identifier):
            symbol = self.current_scope.resolve(node.target.name)
            if not symbol:
                raise SemanticError(f"Variable '{node.target.name}' is not defined.")
            if not symbol.is_mut:
                raise SemanticError(
                    f"Cannot reassign to immutable variable '{node.target.name}'. Use 'let mut'.")
            if (symbol.type_name.startswith("ptr") or symbol.type_name.startswith("*")) and not self.in_unsafe_block:
                raise SemanticError(
                    f"Memory safety: Pointer '{node.target.name}' accessed outside @unsafe.")
            val_type = self.analyze(node.value)
            is_ptr = (symbol.type_name.startswith("ptr") or symbol.type_name.startswith("*")) and val_type == "int"
            if symbol.type_name != val_type and symbol.type_name != "unknown" and not is_ptr:
                raise SemanticError(
                    f"Type mismatch: Cannot assign '{val_type}' to '{symbol.type_name}'.")
        elif isinstance(node.target, ast.ArrayIndex):
            # Allow array element assignment
            self.analyze(node.target.array)
            self.analyze(node.target.index)
            self.analyze(node.value)
        elif isinstance(node.target, ast.MemberAccess):
            self.analyze(node.target)
            self.analyze(node.value)
        else:
            self.analyze(node.target)
            self.analyze(node.value)
        return "void"

    def analyze_ReturnStatement(self, node: ast.ReturnStatement) -> str:
        if node.value:
            self.analyze(node.value)
        return "void"

    def analyze_Identifier(self, node: ast.Identifier) -> str:
        symbol = self.current_scope.resolve(node.name)
        if not symbol:
            raise SemanticError(f"Variable '{node.name}' is not defined.")
        if symbol.is_shared and node.name not in self.locked_variables:
            raise SemanticError(
                f"Concurrency error: Shared variable '{node.name}' accessed outside a lock block.")
        if (symbol.type_name.startswith("ptr") or symbol.type_name.startswith("*")) and not self.in_unsafe_block:
            raise SemanticError(
                f"Memory safety: Pointer '{node.name}' accessed outside @unsafe.")
        return symbol.type_name

    def analyze_NumberLiteral(self, node: ast.NumberLiteral) -> str:
        return "int"

    def analyze_BoolLiteral(self, node: ast.BoolLiteral) -> str:
        return "bool"

    def analyze_StringLiteral(self, node: ast.StringLiteral) -> str:
        return "str"

    def analyze_BinaryOp(self, node: ast.BinaryOp) -> str:
        left_type  = self.analyze(node.left)
        right_type = self.analyze(node.right)

        if node.operator in ['<', '>', '==', '!=']:
            # Comparisons: allow int op int → bool
            return "bool"

        if left_type != right_type:
            raise SemanticError(
                f"Type mismatch in binary op: '{left_type}' {node.operator} '{right_type}'.")

        if node.operator in ['&', '|', '^', '<<', '>>']:
            if left_type != "int":
                raise SemanticError(f"Bitwise ops require 'int', got '{left_type}'.")

        return left_type

    def analyze_FunctionDeclaration(self, node: ast.FunctionDeclaration) -> str:
        param_types = [p[1] for p in node.parameters]
        ret_type    = node.return_type or "void"

        sym = Symbol(node.name.name, "fn", param_types=param_types, return_type=ret_type)
        # Store Phase 9 metadata on the symbol for call-site use
        sym.is_syscall  = node.is_syscall
        sym.is_driver   = node.is_driver
        sym.is_noreturn = node.is_noreturn
        sym.is_naked    = node.is_naked
        self.current_scope.define(sym)

        self.enter_scope()
        prev_unsafe = self.in_unsafe_block

        # @syscall, @driver, @naked, @interrupt all imply unsafe context
        if node.is_unsafe or node.is_syscall or node.is_driver or node.is_naked or node.is_interrupt:
            self.in_unsafe_block = True

        # @noreturn validation: return type must be void (no value returned)
        if node.is_noreturn and ret_type != "void":
            raise SemanticError(
                f"@noreturn function '{node.name.name}' must have void return type, got '{ret_type}'.")

        # @interrupt validation: no ptr params allowed (x86_intrcc ABI restriction)
        if node.is_interrupt:
            for p_name, p_type in node.parameters:
                if p_type.startswith("ptr") or p_type.startswith("*"):
                    raise SemanticError(
                        f"@interrupt handler '{node.name.name}': parameter '{p_name.name}' "
                        f"cannot be a ptr (use InterruptFrame via stack or asm block).")

        for param in node.parameters:
            self.current_scope.define(Symbol(param[0].name, param[1]))

        # Analyze body statements directly (avoid double-scoping)
        for stmt in node.body.statements:
            self.analyze(stmt)

        self.in_unsafe_block = prev_unsafe
        self.exit_scope()
        return "void"

    def analyze_OsIntrinsicCall(self, node: ast.OsIntrinsicCall) -> str:
        """
        Validate OS intrinsic calls (halt, cli, sti, rdtsc, outb, inb, …).
        These are safe to call anywhere — they're guaranteed semantics, not
        raw memory ops. outb/inb however still require @unsafe context.
        """
        port_intrinsics = {"outb", "outw", "outl", "inb", "inw", "inl"}
        if node.name in port_intrinsics and not self.in_unsafe_block:
            raise SemanticError(
                f"Memory safety: I/O intrinsic '{node.name}()' must be inside an @unsafe function.")

        spec = self.OS_INTRINSICS.get(node.name)
        if spec is None:
            raise SemanticError(f"Unknown OS intrinsic '{node.name}'.")

        param_types, ret_type = spec
        if len(node.arguments) != len(param_types):
            raise SemanticError(
                f"Intrinsic '{node.name}' expects {len(param_types)} arg(s), got {len(node.arguments)}.")

        for arg in node.arguments:
            self.analyze(arg)

        return ret_type

    def analyze_StructDeclaration(self, node: ast.StructDeclaration) -> str:
        fields = {f[0].name: f[1] for f in node.fields}
        self.structs[node.name.name] = fields
        # Note: We can add an indicator to self.structs if we need to enforce hwmap constraints here
        self.current_scope.define(Symbol(node.name.name, "struct_decl"))
        return "void"

    def analyze_AsmBlock(self, node: ast.AsmBlock) -> str:
        """Phase 10: Inline assembly block validation"""
        if not self.in_unsafe_block:
            raise SemanticError(
                "Memory safety: inline assembly 'asm(...)' must be inside an @unsafe function or block."
            )
        ret_type = "void"
        for io_type, expr in node.args:
            t = self.analyze(expr)
            if io_type == "out":
                ret_type = t
        return ret_type

    def analyze_EnumDeclaration(self, node: ast.EnumDeclaration) -> str:
        """Register enum and its variants."""
        self.enums[node.name.name] = node.variants
        self.current_scope.define(Symbol(node.name.name, "enum_decl"))
        return "void"

    def analyze_IfStatement(self, node: ast.IfStatement) -> str:
        self.analyze(node.condition)
        self.analyze(node.then_block)
        for (cond, blk) in node.elif_branches:
            self.analyze(cond)
            self.analyze(blk)
        if node.else_block:
            self.analyze(node.else_block)
        return "void"

    def analyze_WhileStatement(self, node: ast.WhileStatement) -> str:
        self.analyze(node.condition)
        self.analyze(node.body)
        return "void"

    def analyze_FunctionCall(self, node: ast.FunctionCall) -> str:
        if isinstance(node.callee, ast.Identifier):
            symbol = self.current_scope.resolve(node.callee.name)
            if not symbol:
                raise SemanticError(f"Function '{node.callee.name}' is not defined.")
            if symbol.type_name != "fn":
                raise SemanticError(f"'{node.callee.name}' is not callable.")

            is_variadic = getattr(symbol, 'is_variadic', False)

            # Arity check: variadic functions require at least the named params
            if is_variadic:
                if len(node.arguments) < len(symbol.param_types):
                    raise SemanticError(
                        f"Variadic function '{node.callee.name}' needs at least "
                        f"{len(symbol.param_types)} args, got {len(node.arguments)}.")
            else:
                if len(node.arguments) != len(symbol.param_types):
                    raise SemanticError(
                        f"Function '{node.callee.name}' expects {len(symbol.param_types)} args, "
                        f"got {len(node.arguments)}.")

            # Type-check named parameters; skip extra variadic args
            for i, arg in enumerate(node.arguments[:len(symbol.param_types)]):
                arg_type      = self.analyze(arg)
                expected_type = symbol.param_types[i]
                if arg_type not in (expected_type, "unknown"):
                    raise SemanticError(
                        f"Argument {i+1} to '{node.callee.name}': expected '{expected_type}', got '{arg_type}'.")

            # Analyze extra variadic args (no type constraint)
            for arg in node.arguments[len(symbol.param_types):]:
                self.analyze(arg)

            return symbol.return_type

        elif isinstance(node.callee, ast.MemberAccess):
            self.analyze(node.callee)
            for arg in node.arguments:
                self.analyze(arg)
            return "unknown"

        return "unknown"

    def analyze_MemberAccess(self, node: ast.MemberAccess) -> str:
        obj_type = self.analyze(node.object)

        # hwmap / hardware access — allow anything
        if obj_type in ("hwmap", "unknown"):
            return "unknown"

        # Enum variant access: Status.OK
        if obj_type in self.enums or (
            isinstance(node.object, ast.Identifier) and node.object.name in self.enums
        ):
            enum_name = node.object.name if isinstance(node.object, ast.Identifier) else obj_type
            if enum_name in self.enums:
                if node.property.name not in self.enums[enum_name]:
                    raise SemanticError(
                        f"Enum '{enum_name}' has no variant '{node.property.name}'.")
                return enum_name

        # Struct field access
        if obj_type in self.structs:
            fields = self.structs[obj_type]
            if node.property.name not in fields:
                raise SemanticError(
                    f"Struct '{obj_type}' has no field '{node.property.name}'.")
            return fields[node.property.name]

        raise SemanticError(
            f"Cannot access property '{node.property.name}' on type '{obj_type}'.")

    # ==========================================
    # Phase 7: New Visitors
    # ==========================================

    def analyze_ArrayLiteral(self, node: ast.ArrayLiteral) -> str:
        """Infer array type from first element."""
        if not node.elements:
            return "[unknown; 0]"
        elem_type = self.analyze(node.elements[0])
        for elem in node.elements[1:]:
            t = self.analyze(elem)
            if t != elem_type:
                raise SemanticError(f"Array elements must all be the same type. Got '{t}' and '{elem_type}'.")
        return f"[{elem_type}; {len(node.elements)}]"

    def analyze_ArrayIndex(self, node: ast.ArrayIndex) -> str:
        """Return the element type of the array."""
        arr_type   = self.analyze(node.array)
        index_type = self.analyze(node.index)
        if index_type != "int":
            raise SemanticError(f"Array index must be 'int', got '{index_type}'.")
        # arr_type is like "[u8; 16]" → element type is "u8"
        if arr_type.startswith("[") and ";" in arr_type:
            elem_type = arr_type[1:arr_type.index(";")].strip()
            return elem_type
        return "unknown"

    def analyze_StructLiteral(self, node: ast.StructLiteral) -> str:
        """Validate struct literal field types."""
        if node.struct_name not in self.structs:
            raise SemanticError(f"Undefined struct '{node.struct_name}'.")
        struct_fields = self.structs[node.struct_name]
        provided = {name: self.analyze(val) for (name, val) in node.fields}
        for field_name, field_type in struct_fields.items():
            if field_name not in provided:
                raise SemanticError(f"Struct '{node.struct_name}' missing field '{field_name}'.")
        return node.struct_name

    def analyze_EnumVariant(self, node: ast.EnumVariant) -> str:
        if node.enum_name not in self.enums:
            raise SemanticError(f"Undefined enum '{node.enum_name}'.")
        if node.variant not in self.enums[node.enum_name]:
            raise SemanticError(f"Enum '{node.enum_name}' has no variant '{node.variant}'.")
        return node.enum_name

    # ==========================================
    # Passthrough / Already-handled visitors


    def analyze_Cast(self, node: ast.Cast) -> str:
        self.analyze(node.expr)
        return node.target_type

    def analyze_SizeOf(self, node: ast.SizeOf) -> str:
        # Code generator will validate the type when emitting IR.
        return "int"

    def analyze_ImportStatement(self, node: ast.ImportStatement) -> str:
        return "void"

    def analyze_LockBlock(self, node: ast.LockBlock) -> str:
        target_name = node.target.name
        symbol = self.current_scope.resolve(target_name)
        if not symbol:
            raise SemanticError(f"Variable '{target_name}' is not defined.")
        if not symbol.is_shared:
            raise SemanticError(f"Cannot lock '{target_name}': not marked as shared.")
        self.locked_variables.add(target_name)
        self.analyze(node.body)
        self.locked_variables.remove(target_name)
        return "void"

    def analyze_UnsafeBlock(self, node: ast.UnsafeBlock) -> str:
        prev_unsafe = self.in_unsafe_block
        self.in_unsafe_block = True
        self.analyze(node.body)
        self.in_unsafe_block = prev_unsafe
        return "void"

    def analyze_PointerDereference(self, node: ast.PointerDereference) -> str:
        if not self.in_unsafe_block:
            raise SemanticError("Memory safety: Pointer dereferenced outside unsafe block.")
        ptr_type = self.analyze(node.pointer_expr)
        if not (ptr_type.startswith("ptr") or ptr_type.startswith("*")):
            raise SemanticError(f"Cannot dereference non-pointer type '{ptr_type}'.")
        # For simplicity, if it's *mut T, we can extract T, but int is the fallback
        if ptr_type.startswith("*mut "):
            return ptr_type[5:]
        if ptr_type.startswith("*const "):
            return ptr_type[7:]
        if ptr_type.startswith("ptr["):
            return ptr_type[4:-1]
        return "int"

    def analyze_AddressOf(self, node: ast.AddressOf) -> str:
        if not self.in_unsafe_block:
            raise SemanticError("Memory safety: Address-of taken outside unsafe block.")
        t = self.analyze(node.target)
        return f"*mut {t}"


    # ==========================================
    # Phase 8: C Interoperability Visitors
    # ==========================================

    def analyze_ExternDeclaration(self, node: ast.ExternDeclaration) -> str:
        """
        Register an extern function so it can be called from our language.
        Variadic functions accept any argument count/type after the named params.
        """
        param_types = [p[1] for p in node.parameters]
        ret_type    = node.return_type or "void"
        symbol = Symbol(
            node.name.name,
            "fn",
            param_types=param_types,
            return_type=ret_type,
        )
        # Mark as variadic so the call checker can relax arity enforcement
        symbol.is_variadic   = getattr(symbol, 'is_variadic', False) or node.is_variadic
        symbol.is_extern     = True
        symbol.abi           = node.abi
        self.current_scope.define(symbol)
        return "void"

    def analyze_ExternBlock(self, node: ast.ExternBlock) -> str:
        """Register all functions inside an extern block."""
        for decl in node.declarations:
            self.analyze_ExternDeclaration(decl)
        return "void"
