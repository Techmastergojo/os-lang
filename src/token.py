from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    LET = auto()
    MUT = auto()
    FN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()
    IMPORT = auto()
    STRUCT = auto()
    HWMAP = auto()
    SHARED = auto()
    LOCK = auto()
    TRUE = auto()
    FALSE = auto()
    PTR = auto()
    ASM = auto()
    AS = auto()
    SIZEOF = auto()
    ENUM = auto()       # Phase 7: enum keyword
    MATCH = auto()      # Phase 10: match keyword
    SEMICOLON = auto()  # Phase 7: [u8; 16] array syntax
    EXTERN = auto()     # Phase 8: extern "C" declarations
    VARARG = auto()     # Phase 8: variadic ... arguments
    UNSAFE = auto()     # Phase 9: unsafe blocks
    
    # Identifiers and Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    # Operators and Punctuation
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()     # Phase 7: { for enum bodies
    RBRACE = auto()     # Phase 7: } for enum bodies
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    AT = auto()
    ARROW = auto()
    AMPERSAND = auto()
    PIPE = auto()
    CARET = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    FAT_ARROW = auto()  # =>
    
    # Structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()

    # ==========================================
    # OsGUI — GUI System Tokens
    # ==========================================

    # --- App / Page / Component Structure ---
    GUIAPP = auto()         # guiapp MyApp:
    PAGE = auto()           # page HomeScreen:
    COMPONENT = auto()      # component Card(title: str):
    ROUTER = auto()         # router:
    RENDER = auto()         # render:  (inside component)

    # --- Layout Containers ---
    WINDOW = auto()         # window Main:
    PANEL = auto()          # panel layout:
    SCROLLVIEW = auto()     # scrollview content:
    TABS = auto()           # tabs main_tabs:
    ACCORDION = auto()      # accordion faq:
    CARD = auto()           # card info_card:
    SIDEBAR = auto()        # sidebar left_panel:
    NAVBAR = auto()         # navbar top_bar:
    STATUSBAR = auto()      # statusbar bottom:
    TOOLBAR = auto()        # toolbar actions:
    MENUBAR = auto()        # menubar app_menu:

    # --- Basic Elements ---
    LABEL = auto()          # label title:
    BUTTON = auto()         # button submit:
    INPUT = auto()          # input search:
    TEXTAREA = auto()       # textarea body:
    IMAGE = auto()          # image avatar:
    ICON = auto()           # icon chevron:
    LINK = auto()           # link homepage:
    SEPARATOR = auto()      # separator line:
    SPACER = auto()         # spacer gap:

    # --- Form Elements ---
    CHECKBOX = auto()       # checkbox agree:
    RADIO = auto()          # radio opt_a:
    DROPDOWN = auto()       # dropdown sort_by:
    SLIDER = auto()         # slider volume:
    TOGGLE = auto()         # toggle dark_mode:
    SPINBOX = auto()        # spinbox quantity:
    COLORPICKER = auto()    # colorpicker accent:
    DATEPICKER = auto()     # datepicker birthday:
    FILEPICKER = auto()     # filepicker attachment:

    # --- Data Display ---
    TABLE = auto()          # table users_table:
    LIST = auto()           # list todo_list:
    TREE = auto()           # tree file_tree:
    CHART = auto()          # chart cpu_chart:
    PROGRESSBAR = auto()    # progressbar loading:
    SPINNER = auto()        # spinner loading_spin:
    BADGE = auto()          # badge notification_count:
    AVATAR = auto()         # avatar user_avatar:
    TAG = auto()            # tag status_tag:

    # --- Drawing / Media ---
    CANVAS = auto()         # canvas game_canvas:
    VIDEO = auto()          # video intro:
    AUDIO = auto()          # audio bg_music:

    # --- Overlays / Dialogs ---
    MODAL = auto()          # modal confirm_dialog:
    NOTIFICATION = auto()   # notification toast:
    TOOLTIP = auto()        # tooltip help_tip:
    POPOVER = auto()        # popover options:
    CONTEXT_MENU = auto()   # context_menu element_ctx:
    ALERT_DIALOG = auto()   # alert_dialog warning:
    DRAG_ZONE = auto()      # drag_zone file_drag:
    DROP_ZONE = auto()      # drop_zone upload_area:

    # --- Styling & Theming ---
    STYLE = auto()          # style PrimaryButton:
    THEME = auto()          # theme DarkMode:
    ANIMATION = auto()      # animation FadeIn:
    APPLY_STYLE = auto()    # apply_style: PrimaryButton
    APPLY_THEME = auto()    # apply_theme: DarkMode
    ANIMATE_IN = auto()     # animate_in: FadeIn
    ANIMATE_OUT = auto()    # animate_out: SlideUp

    # --- State & Binding ---
    STATE = auto()          # state count: int = 0
    BIND_VALUE = auto()     # bind_value: my_var

    # --- Events ---
    ON_CLICK = auto()           # on_click: handler
    ON_DOUBLE_CLICK = auto()    # on_double_click: handler
    ON_RIGHT_CLICK = auto()     # on_right_click: handler
    ON_HOVER_ENTER = auto()     # on_hover_enter: handler
    ON_HOVER_LEAVE = auto()     # on_hover_leave: handler
    ON_FOCUS = auto()           # on_focus: handler
    ON_BLUR = auto()            # on_blur: handler
    ON_CHANGE = auto()          # on_change: handler
    ON_SUBMIT = auto()          # on_submit: handler
    ON_KEY_DOWN = auto()        # on_key_down: handler
    ON_MOUSE_DOWN = auto()      # on_mouse_down: handler
    ON_MOUSE_MOVE = auto()      # on_mouse_move: handler
    ON_MOUSE_UP = auto()        # on_mouse_up: handler
    ON_SCROLL = auto()          # on_scroll: handler
    ON_DROP = auto()            # on_drop: handler
    ON_READY = auto()           # on_ready: handler
    ON_RESIZE = auto()          # on_resize: handler

    # --- Layout Properties ---
    LAYOUT = auto()         # layout: flex | grid | stack | absolute
    DIRECTION = auto()      # direction: row | column
    ALIGN = auto()          # align: center | start | end | stretch
    JUSTIFY = auto()        # justify: space_between | center | ...
    GAP = auto()            # gap: 10
    FLEX_PROP = auto()      # flex: 1
    COL = auto()            # col: 0
    ROW_PROP = auto()       # row: 0
    COL_SPAN = auto()       # col_span: 2
    Z_INDEX = auto()        # z_index: 10

    # --- Python Lib Access ---
    PYLIB = auto()          # @pylib("PIL.Image")

    # --- Menu Items ---
    MENU = auto()           # menu File:
    ITEM = auto()           # item "New File"
    SUBMENU = auto()        # submenu Zoom:

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
