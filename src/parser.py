from src.token import Token, TokenType
from typing import List, Optional
import src.ast as ast

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def match(self, *types: TokenType) -> bool:
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        raise ParseError(f"Line {self.peek().line}, Col {self.peek().column}: {message} (got '{self.peek().lexeme}')")

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            pass

    # ==========================================
    # Top-level Parsing
    # ==========================================

    def parse(self) -> ast.Program:
        statements = []
        while not self.is_at_end():
            if self.match(TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                continue
            statements.append(self.parse_statement())
        return ast.Program(statements=statements)

    def parse_statement(self) -> ast.ASTNode:
        # Decorator / annotation: handles stacked decorators, e.g. @unsafe @noreturn fn
        if self.match(TokenType.AT):
            if self.match(TokenType.UNSAFE):
                tag_name = "unsafe"
            else:
                tag = self.consume(TokenType.IDENTIFIER, "Expect tag after '@'.")
                tag_name = tag.lexeme

            # -- @unsafe --
            if tag_name == "unsafe":
                self.skip_newlines()
                if self.match(TokenType.FN):
                    return self.parse_function_declaration(is_unsafe=True)

            # -- @interrupt(n) --
            elif tag_name == "interrupt":
                self.consume(TokenType.LPAREN, "Expect '(' after interrupt tag.")
                num = self.consume(TokenType.NUMBER, "Expect interrupt number.")
                self.consume(TokenType.RPAREN, "Expect ')' after interrupt number.")
                self.skip_newlines()
                self.consume(TokenType.FN, "Expect 'fn' after interrupt decorator.")
                return self.parse_function_declaration(
                    is_interrupt=True,
                    interrupt_number=int(float(num.lexeme)),
                    is_unsafe=True,   # interrupts are always unsafe
                )

            # -- @entry --
            elif tag_name == "entry":
                self.skip_newlines()
                self.consume(TokenType.FN, "Expect 'fn' after @entry.")
                return self.parse_function_declaration(is_unsafe=True)

            # -- @syscall(n) --
            elif tag_name == "syscall":
                self.consume(TokenType.LPAREN, "Expect '(' after @syscall.")
                num = self.consume(TokenType.NUMBER, "Expect syscall number.")
                self.consume(TokenType.RPAREN, "Expect ')' after syscall number.")
                self.skip_newlines()
                self.consume(TokenType.FN, "Expect 'fn' after @syscall(n).")
                return self.parse_function_declaration(
                    is_unsafe=True,
                    is_syscall=True,
                    syscall_number=int(float(num.lexeme)),
                )

            # -- @driver --
            elif tag_name == "driver":
                self.skip_newlines()
                self.consume(TokenType.FN, "Expect 'fn' after @driver.")
                return self.parse_function_declaration(
                    is_unsafe=True,
                    is_driver=True,
                )

            # -- @noreturn --
            elif tag_name == "noreturn":
                self.skip_newlines()
                self.consume(TokenType.FN, "Expect 'fn' after @noreturn.")
                return self.parse_function_declaration(is_noreturn=True)

            # -- @naked --
            elif tag_name == "naked":
                self.skip_newlines()
                self.consume(TokenType.FN, "Expect 'fn' after @naked.")
                return self.parse_function_declaration(
                    is_unsafe=True,
                    is_naked=True,
                )

            # -- @packed --
            elif tag_name == "packed":
                self.skip_newlines()
                if self.match(TokenType.STRUCT):
                    return self.parse_struct_declaration(is_hwmap=False, is_packed=True)
                elif self.match(TokenType.HWMAP):
                    return self.parse_struct_declaration(is_hwmap=True, is_packed=True)
                else:
                    raise ParseError(f"Line {self.peek().line}: Expect 'struct' or 'hwmap' after @packed.")

            else:
                raise ParseError(f"Line {tag.line}: Unknown decorator @{tag.lexeme}")

        if self.match(TokenType.FN):
            return self.parse_function_declaration()

        if self.match(TokenType.STRUCT):
            return self.parse_struct_declaration(is_hwmap=False)

        if self.match(TokenType.HWMAP):
            return self.parse_struct_declaration(is_hwmap=True)

        if self.match(TokenType.ENUM):
            return self.parse_enum_declaration()

        if self.match(TokenType.EXTERN):
            return self.parse_extern_statement()

        if self.match(TokenType.IMPORT):
            return self.parse_import_statement()

        if self.match(TokenType.RETURN):
            return self.parse_return_statement()

        if self.match(TokenType.IF):
            return self.parse_if_statement()

        if self.match(TokenType.WHILE):
            return self.parse_while_statement()

        if self.match(TokenType.LOCK):
            return self.parse_lock_block()

        # `shared let` or `let`
        if self.check(TokenType.SHARED):
            self.advance()
            self.consume(TokenType.LET, "Expect 'let' after 'shared'.")
            return self.parse_variable_declaration(is_shared=True)

        if self.match(TokenType.LET):
            return self.parse_variable_declaration(is_shared=False)

        if self.match(TokenType.UNSAFE):
            body = self.parse_block()
            return ast.UnsafeBlock(body=body)

        if self.match(TokenType.MATCH):
            return self.parse_match_statement()

        # Expression statement
        expr = self.parse_expression()
        if not self.is_at_end() and self.peek().type not in (TokenType.DEDENT, TokenType.EOF):
            self.match(TokenType.NEWLINE)
        return expr

    def parse_block(self) -> ast.Block:
        self.consume(TokenType.COLON, "Expect ':' before block.")
        
        if not self.check(TokenType.NEWLINE):
            stmt = self.parse_statement()
            return ast.Block(statements=[stmt])

        self.consume(TokenType.NEWLINE, "Expect newline after ':'.")
        self.consume(TokenType.INDENT, "Expect indentation for block.")

        statements = []
        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            statements.append(self.parse_statement())

        self.consume(TokenType.DEDENT, "Expect dedent after block.")
        return ast.Block(statements=statements)

    # ==========================================
    # Declaration Parsing
    # ==========================================

    def parse_function_declaration(
        self,
        is_unsafe: bool = False,
        is_interrupt: bool = False,
        interrupt_number: Optional[int] = None,
        is_syscall: bool = False,
        syscall_number: Optional[int] = None,
        is_driver: bool = False,
        is_noreturn: bool = False,
        is_naked: bool = False,
    ) -> ast.FunctionDeclaration:
        name = self.consume(TokenType.IDENTIFIER, "Expect function name.")
        self.consume(TokenType.LPAREN, "Expect '(' after function name.")

        parameters = []
        if not self.check(TokenType.RPAREN):
            while True:
                param_name = self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                self.consume(TokenType.COLON, "Expect ':' after parameter name.")
                type_str = self.parse_type_string()
                parameters.append((ast.Identifier(name=param_name.lexeme), type_str))
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RPAREN, "Expect ')' after parameters.")

        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type_string()

        body = self.parse_block()

        return ast.FunctionDeclaration(
            name=ast.Identifier(name=name.lexeme),
            parameters=parameters,
            return_type=return_type,
            body=body,
            is_unsafe=is_unsafe,
            is_interrupt=is_interrupt,
            interrupt_number=interrupt_number,
            is_syscall=is_syscall,
            syscall_number=syscall_number,
            is_driver=is_driver,
            is_noreturn=is_noreturn,
            is_naked=is_naked,
        )

    def parse_struct_declaration(self, is_hwmap: bool, is_packed: bool = False) -> ast.StructDeclaration:
        name = self.consume(TokenType.IDENTIFIER, "Expect struct/hwmap name.")
        self.consume(TokenType.COLON, "Expect ':' after struct name.")
        self.consume(TokenType.NEWLINE, "Expect newline after ':'.")
        self.consume(TokenType.INDENT, "Expect indentation for struct body.")

        fields = []
        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            field_name = self.consume(TokenType.IDENTIFIER, "Expect field name.")
            self.consume(TokenType.COLON, "Expect ':' after field name.")
            type_str = self.parse_type_string()
            fields.append((ast.Identifier(name=field_name.lexeme), type_str))
            self.match(TokenType.NEWLINE)

        self.consume(TokenType.DEDENT, "Expect dedent after struct body.")
        return ast.StructDeclaration(name=ast.Identifier(name=name.lexeme), fields=fields, is_hwmap=is_hwmap, is_packed=is_packed)

    def parse_enum_declaration(self) -> ast.EnumDeclaration:
        """Parse: enum Status { OK, ERROR, PENDING }"""
        name = self.consume(TokenType.IDENTIFIER, "Expect enum name.")
        self.consume(TokenType.LBRACE, "Expect '{' after enum name.")
        self.skip_newlines()

        variants = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            self.skip_newlines()
            if self.check(TokenType.RBRACE):
                break
            variant = self.consume(TokenType.IDENTIFIER, "Expect variant name.")
            variants.append(variant.lexeme)
            self.match(TokenType.COMMA)
            self.skip_newlines()

        self.consume(TokenType.RBRACE, "Expect '}' after enum variants.")
        if not self.is_at_end():
            self.match(TokenType.NEWLINE)
        return ast.EnumDeclaration(name=ast.Identifier(name=name.lexeme), variants=variants)

    def parse_extern_statement(self) -> ast.ASTNode:
        """
        Supports two syntaxes:

        Single declaration:
            extern "C" fn malloc(size: int) -> ptr

        Block declaration:
            extern "C":
                fn malloc(size: int) -> ptr
                fn free(p: ptr)
        """
        # Consume the ABI string (e.g. "C")
        abi_tok = self.consume(TokenType.STRING, "Expect ABI string after 'extern' (e.g. \"C\").")
        abi = abi_tok.lexeme  # e.g. "C"

        # Block form: extern "C":
        if self.match(TokenType.COLON):
            self.consume(TokenType.NEWLINE, "Expect newline after 'extern \"C\":'.")
            self.consume(TokenType.INDENT, "Expect indented block for extern declarations.")
            decls = []
            while not self.check(TokenType.DEDENT) and not self.is_at_end():
                if self.match(TokenType.NEWLINE):
                    continue
                self.consume(TokenType.FN, "Expect 'fn' inside extern block.")
                decls.append(self._parse_extern_fn_signature(abi))
            self.consume(TokenType.DEDENT, "Expect dedent after extern block.")
            return ast.ExternBlock(abi=abi, declarations=decls)

        # Single form: extern "C" fn name(...)
        self.consume(TokenType.FN, "Expect 'fn' after extern ABI string.")
        decl = self._parse_extern_fn_signature(abi)
        return decl

    def _parse_extern_fn_signature(self, abi: str) -> ast.ExternDeclaration:
        """Parse: fn name(param: type, ...) -> ret_type"""
        name = self.consume(TokenType.IDENTIFIER, "Expect function name.")
        self.consume(TokenType.LPAREN, "Expect '(' after extern function name.")

        parameters  = []
        is_variadic = False

        if not self.check(TokenType.RPAREN):
            while True:
                # Variadic marker: ...
                if self.match(TokenType.VARARG):
                    is_variadic = True
                    break
                param_name = self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                self.consume(TokenType.COLON, "Expect ':' after parameter name.")
                type_str = self.parse_type_string()
                parameters.append((ast.Identifier(name=param_name.lexeme), type_str))
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RPAREN, "Expect ')' after parameters.")

        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type_string()

        # Optional newline after signature
        self.match(TokenType.NEWLINE)

        return ast.ExternDeclaration(
            name=ast.Identifier(name=name.lexeme),
            parameters=parameters,
            return_type=return_type,
            is_variadic=is_variadic,
            abi=abi,
        )

    def parse_import_statement(self) -> ast.ImportStatement:
        module_name = ""
        while not self.is_at_end() and not self.check(TokenType.NEWLINE):
            module_name += self.advance().lexeme
        self.match(TokenType.NEWLINE)
        return ast.ImportStatement(module_name=module_name.strip())

    def parse_return_statement(self) -> ast.ReturnStatement:
        value = None
        if not self.check(TokenType.NEWLINE) and not self.is_at_end():
            value = self.parse_expression()
        self.match(TokenType.NEWLINE)
        return ast.ReturnStatement(value=value)

    def parse_variable_declaration(self, is_shared: bool) -> ast.VariableDeclaration:
        is_mut = self.match(TokenType.MUT)
        name_token = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        name = ast.Identifier(name=name_token.lexeme)

        type_annotation = None
        if self.match(TokenType.COLON):
            type_annotation = self.parse_type_string()

        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.parse_expression()

        if not self.is_at_end() and self.peek().type not in (TokenType.DEDENT, TokenType.EOF):
            self.match(TokenType.NEWLINE)

        return ast.VariableDeclaration(
            name=name,
            is_mut=is_mut,
            type_annotation=type_annotation,
            initializer=initializer,
            is_shared=is_shared
        )

    def parse_if_statement(self) -> ast.IfStatement:
        condition = self.parse_expression()
        then_block = self.parse_block()

        elif_branches = []
        while self.match(TokenType.ELIF):
            elif_cond = self.parse_expression()
            elif_block = self.parse_block()
            elif_branches.append((elif_cond, elif_block))

        else_block = None
        if self.match(TokenType.ELSE):
            else_block = self.parse_block()

        return ast.IfStatement(condition=condition, then_block=then_block, elif_branches=elif_branches, else_block=else_block)

    def parse_match_statement(self) -> ast.MatchStatement:
        target = self.parse_expression()
        self.consume(TokenType.COLON, "Expect ':' after match target.")
        self.consume(TokenType.NEWLINE, "Expect newline after match target.")
        self.consume(TokenType.INDENT, "Expect indentation for match cases.")
        
        cases = []
        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            
            # parse pattern
            # it could be EnumVariant like Status.OK or Identifier like '_'
            if self.check(TokenType.IDENTIFIER):
                first_id = self.consume(TokenType.IDENTIFIER, "Expect pattern identifier.").lexeme
                if self.match(TokenType.DOT):
                    variant_id = self.consume(TokenType.IDENTIFIER, "Expect variant name after '.'.").lexeme
                    pattern = ast.EnumVariant(enum_name=first_id, variant=variant_id)
                else:
                    pattern = ast.Identifier(name=first_id)
            else:
                raise ParseError(f"Line {self.peek().line}: Expect pattern identifier or '_' in match case.")
                
            self.consume(TokenType.FAT_ARROW, "Expect '=>' after match pattern.")
            
            # Now we parse a block or a single statement for the case body
            # Wait, match cases usually look like:
            # OK => { block }
            # But let's support a simple block starting with colon, or a single statement
            # To be consistent with python: 
            # Status.OK =>:
            #     ...
            # Oh wait, we just added FAT_ARROW. Let's make it so you can write:
            # Status.OK => statement
            # Or if it's multiple lines, maybe require a block?
            # Actually, let's just parse a statement. If it's a block, we parse a block.
            if self.check(TokenType.COLON):
                body = self.parse_block()
            else:
                stmt = self.parse_statement()
                body = ast.Block(statements=[stmt])
                
            cases.append(ast.MatchCase(pattern=pattern, body=body))
            
        self.consume(TokenType.DEDENT, "Expect dedent after match cases.")
        return ast.MatchStatement(target=target, cases=cases)

    def parse_while_statement(self) -> ast.WhileStatement:
        condition = self.parse_expression()
        body = self.parse_block()
        return ast.WhileStatement(condition=condition, body=body)

    def parse_lock_block(self) -> ast.LockBlock:
        target = self.consume(TokenType.IDENTIFIER, "Expect variable name to lock.")
        body = self.parse_block()
        return ast.LockBlock(target=ast.Identifier(name=target.lexeme), body=body)

    # ==========================================
    # Type String Parsing
    # ==========================================

    def parse_type_string(self) -> str:
        """
        Parse a type annotation and return it as a string.
        Handles: int, u8, str, bool, void, ptr, ptr[u8],
                 [u8; 16] (array types), and plain identifiers (struct/enum names).
        """
        if self.match(TokenType.STAR):
            # *mut T or *const T
            is_mut = False
            if self.match(TokenType.MUT):
                is_mut = True
            elif self.check(TokenType.IDENTIFIER) and self.peek().lexeme == "const":
                self.advance()
            else:
                pass # default to const if neither
            inner = self.parse_type_string()
            return f"*mut {inner}" if is_mut else f"*const {inner}"

        # Array type: [ElementType; Size]
        if self.match(TokenType.LBRACKET):
            elem_type = self.parse_type_string()
            self.consume(TokenType.SEMICOLON, "Expect ';' in array type '[T; N]'.")
            size_tok = self.consume(TokenType.NUMBER, "Expect array size.")
            self.consume(TokenType.RBRACKET, "Expect ']' after array size.")
            return f"[{elem_type}; {int(float(size_tok.lexeme))}]"

        # Pointer type: ptr or ptr[T]
        if self.match(TokenType.PTR):
            if self.match(TokenType.LBRACKET):
                inner = self.parse_type_string()
                self.consume(TokenType.RBRACKET, "Expect ']' after pointer inner type.")
                return f"ptr[{inner}]"
            return "ptr"

        # Named types: int, u8, str, bool, void, or struct/enum name
        tok = self.advance()
        return tok.lexeme

    # ==========================================
    # Expression Parsing (Pratt-style precedence)
    # ==========================================

    def parse_expression(self) -> ast.ASTNode:
        return self.parse_assignment()

    def parse_assignment(self) -> ast.ASTNode:
        expr = self.parse_comparison()
        if self.match(TokenType.ASSIGN):
            value = self.parse_assignment()
            return ast.Assignment(target=expr, value=value)
        return expr

    def parse_comparison(self) -> ast.ASTNode:
        expr = self.parse_bitwise_or()
        while self.match(TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT):
            operator = self.previous().lexeme
            right = self.parse_bitwise_or()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_bitwise_or(self) -> ast.ASTNode:
        expr = self.parse_bitwise_xor()
        while self.match(TokenType.PIPE):
            operator = self.previous().lexeme
            right = self.parse_bitwise_xor()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_bitwise_xor(self) -> ast.ASTNode:
        expr = self.parse_bitwise_and()
        while self.match(TokenType.CARET):
            operator = self.previous().lexeme
            right = self.parse_bitwise_and()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_bitwise_and(self) -> ast.ASTNode:
        expr = self.parse_shift()
        while self.match(TokenType.AMPERSAND):
            operator = self.previous().lexeme
            right = self.parse_shift()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_shift(self) -> ast.ASTNode:
        expr = self.parse_math()
        while self.match(TokenType.LSHIFT, TokenType.RSHIFT):
            operator = self.previous().lexeme
            right = self.parse_math()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_math(self) -> ast.ASTNode:
        expr = self.parse_term()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous().lexeme
            right = self.parse_term()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_term(self) -> ast.ASTNode:
        expr = self.parse_unary()
        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous().lexeme
            right = self.parse_unary()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def parse_unary(self) -> ast.ASTNode:
        if self.match(TokenType.STAR):
            expr = self.parse_unary()
            return ast.PointerDereference(pointer_expr=expr)
        if self.match(TokenType.AMPERSAND):
            expr = self.parse_unary()
            return ast.AddressOf(target=expr)
        
        # Future: handle unary - and ! here
        return self.parse_postfix()

    def parse_postfix(self) -> ast.ASTNode:
        """Handle postfix operations: calls, member access, indexing, casting."""
        expr = self.parse_primary()

        while True:
            if self.match(TokenType.LPAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = ast.MemberAccess(object=expr, property=ast.Identifier(name=name.lexeme))
            elif self.match(TokenType.LBRACKET):
                # Array index: arr[i]
                index = self.parse_expression()
                self.consume(TokenType.RBRACKET, "Expect ']' after index.")
                expr = ast.ArrayIndex(array=expr, index=index)
            elif self.match(TokenType.AS):
                type_str = self.parse_type_string()
                expr = ast.Cast(expr=expr, target_type=type_str)
            else:
                break

        return expr

    def finish_call(self, callee: ast.ASTNode) -> ast.ASTNode:
        arguments = []
        if not self.check(TokenType.RPAREN):
            while True:
                arguments.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expect ')' after arguments.")
        return ast.FunctionCall(callee=callee, arguments=arguments)

    def parse_primary(self) -> ast.ASTNode:
        # sizeof(Type)
        if self.match(TokenType.SIZEOF):
            self.consume(TokenType.LPAREN, "Expect '(' after sizeof.")
            type_str = self.parse_type_string()
            self.consume(TokenType.RPAREN, "Expect ')' after type in sizeof.")
            return ast.SizeOf(target_type=type_str)

        # Boolean literals
        if self.match(TokenType.TRUE):
            return ast.BoolLiteral(value=True)
        if self.match(TokenType.FALSE):
            return ast.BoolLiteral(value=False)

        if self.match(TokenType.NUMBER):
            tok = self.previous()
            # Handle hex (0x...) and binary (0b...) literals
            if tok.lexeme.startswith('0x') or tok.lexeme.startswith('0X'):
                return ast.NumberLiteral(value=float(int(tok.lexeme, 16)))
            elif tok.lexeme.startswith('0b') or tok.lexeme.startswith('0B'):
                return ast.NumberLiteral(value=float(int(tok.lexeme, 2)))
            return ast.NumberLiteral(value=float(tok.lexeme))

        if self.match(TokenType.STRING):
            return ast.StringLiteral(value=self.previous().lexeme)

        # Array literal: [elem, elem, ...]
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    elements.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACKET, "Expect ']' after array elements.")
            return ast.ArrayLiteral(elements=elements)

        if self.match(TokenType.IDENTIFIER):
            name = self.previous().lexeme

            # ── Phase 9: OS intrinsic calls ──────────────────────────────
            OS_INTRINSICS = {"halt", "cli", "sti", "rdtsc", "cpuid",
                              "outb", "outw", "outl", "inb", "inw", "inl",
                              "memory_barrier", "volatile_load", "volatile_store",
                              "atomic_cmpxchg", "atomic_xchg", "atomic_add", "atomic_sub"}
            if name in OS_INTRINSICS and self.check(TokenType.LPAREN):
                self.advance()  # consume '('
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arguments.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.consume(TokenType.RPAREN, "Expect ')' after intrinsic arguments.")
                return ast.OsIntrinsicCall(name=name, arguments=arguments)

            # Struct literal: MyStruct { field: val, ... }
            if self.check(TokenType.LBRACE):
                self.advance()  # consume '{'
                self.skip_newlines()
                fields = []
                while not self.check(TokenType.RBRACE) and not self.is_at_end():
                    self.skip_newlines()
                    if self.check(TokenType.RBRACE):
                        break
                    field_name = self.consume(TokenType.IDENTIFIER, "Expect field name.")
                    self.consume(TokenType.COLON, "Expect ':' after field name.")
                    field_val = self.parse_expression()
                    fields.append((field_name.lexeme, field_val))
                    self.match(TokenType.COMMA)
                    self.skip_newlines()
                self.consume(TokenType.RBRACE, "Expect '}' after struct fields.")
                return ast.StructLiteral(struct_name=name, fields=fields)

            # Enum variant access: Status.OK (parsed later via MemberAccess)
            return ast.Identifier(name=name)

        if self.match(TokenType.ASM):
            self.consume(TokenType.LPAREN, "Expect '(' after 'asm'.")
            string_token = self.consume(TokenType.STRING, "Expect assembly string literal.")
            args = []
            if self.match(TokenType.COMMA):
                while not self.check(TokenType.RPAREN) and not self.is_at_end():
                    io_type = self.consume(TokenType.IDENTIFIER, "Expect 'in' or 'out' modifier.")
                    if io_type.lexeme not in ["in", "out"]:
                        raise ParseError(f"Line {io_type.line}: asm modifier must be 'in' or 'out'.")
                    self.consume(TokenType.COLON, "Expect ':' after asm modifier.")
                    expr = self.parse_expression()
                    args.append((io_type.lexeme, expr))
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RPAREN, "Expect ')' after asm block.")
            return ast.AsmBlock(assembly_string=string_token.lexeme, args=args)

        raise ParseError(f"Line {self.peek().line}: Expected expression. Got '{self.peek().lexeme}'")
