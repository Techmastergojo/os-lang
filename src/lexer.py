from src.token import Token, TokenType
from typing import List

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.line = 1
        self.column = 1
        self.current = 0
        self.indent_stack = [0]

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        if self.is_at_end():
            return '\0'
        c = self.source[self.current]
        self.current += 1
        if c == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return c

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
        
    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def lex(self) -> List[Token]:
        tokens = []
        is_at_line_start = True
        
        while not self.is_at_end():
            # Handle indentation at the start of a line
            if is_at_line_start:
                is_at_line_start = False
                space_count = 0
                
                # Count spaces
                while self.peek() == ' ' and not self.is_at_end():
                    self.advance()
                    space_count += 1
                
                # If the line is just empty or a comment, skip it
                if self.peek() == '\n' or self.peek() == '\r' or self.is_at_end():
                    continue
                    
                if space_count > self.indent_stack[-1]:
                    self.indent_stack.append(space_count)
                    tokens.append(Token(TokenType.INDENT, "", self.line, 1))
                elif space_count < self.indent_stack[-1]:
                    while len(self.indent_stack) > 1 and space_count < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        tokens.append(Token(TokenType.DEDENT, "", self.line, 1))
                    
                    if space_count != self.indent_stack[-1]:
                        pass # Indentation error, could throw later
                        
            start_col = self.column
            c = self.advance()
            
            if c in ['\r']:
                continue
                
            if c == '\n':
                tokens.append(Token(TokenType.NEWLINE, "\\n", self.line - 1, start_col))
                is_at_line_start = True
                continue
                
            if c in [' ', '\t']:
                continue
            
            # Single-line comments: skip # ... to end of line
            if c == '#':
                while not self.is_at_end() and self.peek() != '\n':
                    self.advance()
                continue
                
            if c.isalpha() or c == '_':
                lexeme = c
                while (self.peek().isalnum() or self.peek() == '_') and not self.is_at_end():
                    lexeme += self.advance()
                
                # Check keywords
                keywords = {
                    "let":    TokenType.LET,
                    "mut":    TokenType.MUT,
                    "fn":     TokenType.FN,
                    "if":     TokenType.IF,
                    "elif":   TokenType.ELIF,
                    "else":   TokenType.ELSE,
                    "while":  TokenType.WHILE,
                    "return": TokenType.RETURN,
                    "print":  TokenType.PRINT,
                    "import": TokenType.IMPORT,
                    "struct": TokenType.STRUCT,
                    "hwmap":  TokenType.HWMAP,
                    "shared": TokenType.SHARED,
                    "lock":   TokenType.LOCK,
                    "true":   TokenType.TRUE,
                    "false":  TokenType.FALSE,
                    "ptr":    TokenType.PTR,
                    "asm":    TokenType.ASM,
                    "as":     TokenType.AS,
                    "sizeof": TokenType.SIZEOF,
                    "enum":   TokenType.ENUM,   # Phase 7
                    "extern": TokenType.EXTERN, # Phase 8
                    "unsafe": TokenType.UNSAFE, # Phase 9
                    "match":  TokenType.MATCH,  # Phase 10
                    # ---- OsGUI Keywords ----
                    # App / Page / Component
                    "guiapp":    TokenType.GUIAPP,
                    "page":      TokenType.PAGE,
                    "component": TokenType.COMPONENT,
                    "router":    TokenType.ROUTER,
                    "render":    TokenType.RENDER,
                    # Layout Containers
                    "window":    TokenType.WINDOW,
                    "header":    TokenType.HEADER,
                    "footer":    TokenType.FOOTER,
                    "section":   TokenType.SECTION,
                    "container": TokenType.CONTAINER,
                    "main":      TokenType.MAIN,
                    "nav":       TokenType.NAV,
                    "panel":      TokenType.PANEL,
                    "scrollview": TokenType.SCROLLVIEW,
                    "tabs":       TokenType.TABS,
                    "accordion":  TokenType.ACCORDION,
                    "card":       TokenType.CARD,
                    "sidebar":    TokenType.SIDEBAR,
                    "navbar":     TokenType.NAVBAR,
                    "statusbar":  TokenType.STATUSBAR,
                    "toolbar":    TokenType.TOOLBAR,
                    "menubar":    TokenType.MENUBAR,
                    # Basic Elements
                    "label":     TokenType.LABEL,
                    "button":    TokenType.BUTTON,
                    "input":     TokenType.INPUT,
                    "textarea":  TokenType.TEXTAREA,
                    "image":     TokenType.IMAGE,
                    "icon":      TokenType.ICON,
                    "link":      TokenType.LINK,
                    "separator": TokenType.SEPARATOR,
                    "spacer":    TokenType.SPACER,
                    # Form Elements
                    "checkbox":    TokenType.CHECKBOX,
                    "radio":       TokenType.RADIO,
                    "dropdown":    TokenType.DROPDOWN,
                    "slider":      TokenType.SLIDER,
                    "toggle":      TokenType.TOGGLE,
                    "spinbox":     TokenType.SPINBOX,
                    "colorpicker": TokenType.COLORPICKER,
                    "datepicker":  TokenType.DATEPICKER,
                    "filepicker":  TokenType.FILEPICKER,
                    # Data Display
                    "table":       TokenType.TABLE,
                    "list":        TokenType.LIST,
                    "tree":        TokenType.TREE,
                    "chart":       TokenType.CHART,
                    "progressbar": TokenType.PROGRESSBAR,
                    "spinner":     TokenType.SPINNER,
                    "badge":       TokenType.BADGE,
                    "avatar":      TokenType.AVATAR,
                    "tag":         TokenType.TAG,
                    # Drawing / Media
                    "canvas": TokenType.CANVAS,
                    "video":  TokenType.VIDEO,
                    "audio":  TokenType.AUDIO,
                    # Overlays
                    "modal":        TokenType.MODAL,
                    "notification": TokenType.NOTIFICATION,
                    "tooltip":      TokenType.TOOLTIP,
                    "popover":      TokenType.POPOVER,
                    "context_menu": TokenType.CONTEXT_MENU,
                    "alert_dialog": TokenType.ALERT_DIALOG,
                    "drag_zone":    TokenType.DRAG_ZONE,
                    "drop_zone":    TokenType.DROP_ZONE,
                    # Styling
                    "style":       TokenType.STYLE,
                    "theme":       TokenType.THEME,
                    "animation":   TokenType.ANIMATION,
                    "apply_style": TokenType.APPLY_STYLE,
                    "apply_theme": TokenType.APPLY_THEME,
                    "animate_in":  TokenType.ANIMATE_IN,
                    "animate_out": TokenType.ANIMATE_OUT,
                    # State & Binding
                    "state":      TokenType.STATE,
                    "bind_value": TokenType.BIND_VALUE,
                    # Events
                    "on_click":        TokenType.ON_CLICK,
                    "on_double_click": TokenType.ON_DOUBLE_CLICK,
                    "on_right_click":  TokenType.ON_RIGHT_CLICK,
                    "on_hover_enter":  TokenType.ON_HOVER_ENTER,
                    "on_hover_leave":  TokenType.ON_HOVER_LEAVE,
                    "on_focus":        TokenType.ON_FOCUS,
                    "on_blur":         TokenType.ON_BLUR,
                    "on_change":       TokenType.ON_CHANGE,
                    "on_submit":       TokenType.ON_SUBMIT,
                    "on_key_down":     TokenType.ON_KEY_DOWN,
                    "on_mouse_down":   TokenType.ON_MOUSE_DOWN,
                    "on_mouse_move":   TokenType.ON_MOUSE_MOVE,
                    "on_mouse_up":     TokenType.ON_MOUSE_UP,
                    "on_scroll":       TokenType.ON_SCROLL,
                    "on_drop":         TokenType.ON_DROP,
                    "on_ready":        TokenType.ON_READY,
                    "on_resize":       TokenType.ON_RESIZE,
                    # Layout Properties
                    "layout":    TokenType.LAYOUT,
                    "direction": TokenType.DIRECTION,
                    "align":     TokenType.ALIGN,
                    "justify":   TokenType.JUSTIFY,
                    "gap":       TokenType.GAP,
                    "flex":      TokenType.FLEX_PROP,
                    "col":       TokenType.COL,
                    "row":       TokenType.ROW_PROP,
                    "col_span":  TokenType.COL_SPAN,
                    "z_index":   TokenType.Z_INDEX,
                    # Python Lib Access
                    "pylib": TokenType.PYLIB,
                    # Menu Items
                    "menu":    TokenType.MENU,
                    "item":    TokenType.ITEM,
                    "submenu": TokenType.SUBMENU,
                    # OS Heaven Keywords
                    "process":    TokenType.PROCESS,
                    "thread":     TokenType.THREAD,
                    "priority":   TokenType.PRIORITY,
                    "ring":       TokenType.RING,
                    "packet":     TokenType.PACKET,
                    "vfs":        TokenType.VFS,
                    "mount":      TokenType.MOUNT,
                    "guard":      TokenType.GUARD,
                    "panic":      TokenType.PANIC,
                    "task_yield": TokenType.TASK_YIELD,
                }
                token_type = keywords.get(lexeme, TokenType.IDENTIFIER)
                tokens.append(Token(token_type, lexeme, self.line, start_col))
                continue
                
            if c.isdigit() or (c == '0' and self.peek() in ['x', 'b']):
                lexeme = c
                # Hex literals: 0x...
                if c == '0' and self.peek() == 'x':
                    lexeme += self.advance()  # consume 'x'
                    while (self.peek().isdigit() or self.peek() in 'abcdefABCDEF') and not self.is_at_end():
                        lexeme += self.advance()
                # Binary literals: 0b...
                elif c == '0' and self.peek() == 'b':
                    lexeme += self.advance()  # consume 'b'
                    while self.peek() in '01' and not self.is_at_end():
                        lexeme += self.advance()
                else:
                    while self.peek().isdigit() and not self.is_at_end():
                        lexeme += self.advance()
                    if self.peek() == '.' and self.peek_next().isdigit():
                        lexeme += self.advance()  # consume '.'
                        while self.peek().isdigit() and not self.is_at_end():
                            lexeme += self.advance()
                tokens.append(Token(TokenType.NUMBER, lexeme, self.line, start_col))
                continue
                
            if c == '"':
                lexeme = ""
                while self.peek() != '"' and not self.is_at_end():
                    if self.peek() == '\\':
                        self.advance()  # consume backslash
                        escaped = self.advance()
                        lexeme += '\\' + escaped
                    else:
                        lexeme += self.advance()
                if not self.is_at_end():
                    self.advance()  # consume closing quote
                tokens.append(Token(TokenType.STRING, lexeme, self.line, start_col))
                continue
            
            token_type = None
            if c == '+': token_type = TokenType.PLUS
            elif c == '-':
                if self.peek() == '>':
                    self.advance()
                    token_type = TokenType.ARROW
                    c = '->'
                else:
                    token_type = TokenType.MINUS
            elif c == '*': token_type = TokenType.STAR
            elif c == '/': token_type = TokenType.SLASH
            elif c == '=':
                if self.peek() == '=':
                    self.advance()
                    token_type = TokenType.EQ
                    c = '=='
                elif self.peek() == '>':
                    self.advance()
                    token_type = TokenType.FAT_ARROW
                    c = '=>'
                else:
                    token_type = TokenType.ASSIGN
            elif c == '!':
                if self.peek() == '=':
                    self.advance()
                    token_type = TokenType.NEQ
                    c = '!='
            elif c == '<':
                if self.peek() == '<':
                    self.advance()
                    token_type = TokenType.LSHIFT
                    c = '<<'
                else:
                    token_type = TokenType.LT
            elif c == '>':
                if self.peek() == '>':
                    self.advance()
                    token_type = TokenType.RSHIFT
                    c = '>>'
                else:
                    token_type = TokenType.GT
            elif c == '(': token_type = TokenType.LPAREN
            elif c == ')': token_type = TokenType.RPAREN
            elif c == '[': token_type = TokenType.LBRACKET
            elif c == ']': token_type = TokenType.RBRACKET
            elif c == '{': token_type = TokenType.LBRACE
            elif c == '}': token_type = TokenType.RBRACE
            elif c == ':': token_type = TokenType.COLON
            elif c == ';': token_type = TokenType.SEMICOLON
            elif c == ',': token_type = TokenType.COMMA
            elif c == '.': 
                # Check for ... (vararg)
                if self.peek() == '.' and self.peek_next() == '.':
                    self.advance()  # consume second .
                    self.advance()  # consume third .
                    token_type = TokenType.VARARG
                    c = '...'
                else:
                    token_type = TokenType.DOT
            elif c == '@': token_type = TokenType.AT
            elif c == '&': token_type = TokenType.AMPERSAND
            elif c == '|': token_type = TokenType.PIPE
            elif c == '^': token_type = TokenType.CARET
            
            if token_type is not None:
                tokens.append(Token(token_type, c, self.line, start_col))
            else:
                pass  # Unhandled character — silently skip for now

        # EOF Cleanup
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, "", self.line, self.column))
            
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
