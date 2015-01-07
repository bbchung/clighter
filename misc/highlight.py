import vim
import clighter_helper
from clang import cindex
import clang_service

SYMBOL_REF_PRI = -11
SYNTAX_PRI = -12


def clear_highlight():
    __vim_clear_match_pri(SYMBOL_REF_PRI, SYNTAX_PRI)
    highlight_window.syntactic_range = None
    highlight_window.hl_cursor = None


def clear_symbol_ref():
    __vim_clear_match_pri(SYMBOL_REF_PRI)
    highlight_window.hl_cursor = None


def highlight_window(clang_service, extend=50):
    cc = clang_service.get_cc(vim.current.buffer.name)
    if cc is None:
        return

    tu = cc.current_tu
    if tu is None:
        return

    top = vim.bindeval("line('w0')")
    bottom = vim.bindeval("line('w$')")

    draw_syntax = False
    draw_symbol_ref = False

    parse_tick = cc.parse_tick
    if vim.current.window.vars['hl_tick'] < parse_tick \
            or highlight_window.syntactic_range is None \
            or top < highlight_window.syntactic_range[0] \
            or bottom > highlight_window.syntactic_range[1]:
        draw_syntax = True
        __vim_clear_match_pri(SYNTAX_PRI)
        vim.current.window.vars['hl_tick'] = parse_tick

    file = tu.get_file(cc.name)
    symbol = None
    if vim.vars["ClighterCursorHL"] == 1:
        vim_cursor = clighter_helper.get_vim_cursor(tu, file)

        if highlight_window.hl_cursor is not None and (vim_cursor is None or highlight_window.hl_cursor != vim_cursor):
            __vim_clear_match_pri(SYMBOL_REF_PRI)

        symbol = clighter_helper.get_vim_symbol(vim_cursor)
        if symbol is not None:
            draw_symbol_ref = True

        highlight_window.hl_cursor = vim_cursor

    if not draw_syntax and not draw_symbol_ref:
        return

    target_range = [top, bottom]

    if draw_syntax:
        buflinenr = len(vim.current.buffer)
        target_range = [
            max(top - extend, 1),
            min(bottom + extend, buflinenr)
        ]
        highlight_window.syntactic_range = target_range

    location1 = cindex.SourceLocation.from_position(tu, file, line=target_range[0], column=1)
    location2 = cindex.SourceLocation.from_position(tu, file, line=target_range[1] + 1, column=1)
    tokens = tu.get_tokens(extent=cindex.SourceRange.from_locations(location1, location2))

    for t in tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value != 2:
            continue

        t_cursor = cindex.Cursor.from_location(
            tu,
            cindex.SourceLocation.from_position(
                tu, file,
                t.location.line,
                t.location.column
            )
        )  # cursor under vim

        if draw_syntax:
            __draw_token(
                line=t.location.line,
                col=t.location.column,
                len=len(t.spelling),
                cursor_kind=t_cursor.kind,
                type_kind=t_cursor.type.kind
            )

        """ Do definition/reference highlighting'
        """
        if draw_symbol_ref:
            t_symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if t_symbol is not None and t.spelling == t_symbol.spelling and t_symbol == symbol:
                __vim_matchaddpos(
                    group='clighterCursorSymbolRef',
                    line=t.location.line,
                    col=t.location.column,
                    len=len(t.spelling),
                    priority=SYMBOL_REF_PRI
                )


highlight_window.hl_cursor = None
highlight_window.syntactic_range = None

group_map = {
        cindex.CursorKind.MACRO_INSTANTIATION:'clighterMacroInstantiation',
        cindex.CursorKind.STRUCT_DECL:'clighterStructDecl',
        cindex.CursorKind.CLASS_DECL:'clighterClassDecl',
        cindex.CursorKind.ENUM_DECL:'clighterEnumDecl',
        cindex.CursorKind.ENUM_CONSTANT_DECL:'clighterEnumConstantDecl',
        cindex.CursorKind.TYPE_REF:'clighterTypeRef',
        cindex.CursorKind.FUNCTION_DECL:'clighterFunctionDecl',
        cindex.CursorKind.MEMBER_REF_EXPR:'clighterMemberRefExpr',
        cindex.CursorKind.NAMESPACE_REF:'clighterNamespace',
        cindex.CursorKind.NAMESPACE:'clighterNamespace',
        cindex.CursorKind.DECL_REF_EXPR:
        {
            cindex.TypeKind.ENUM:'clighterDeclRefExprEnum',
            cindex.TypeKind.FUNCTIONPROTO:'clighterDeclRefExprCall'
        }
}

def __draw_token(line, col, len, cursor_kind, type_kind):
    highlight_groups = vim.vars['clighter_highlight_groups']

    group = group_map.get(cursor_kind)
    if group is None:
        return

    if type(group) is dict:
        group = group.get(type_kind)
        if group is None:
            return

    if group in highlight_groups:
        __vim_matchaddpos(group, line, col, len, SYNTAX_PRI)


def __vim_matchaddpos(group, line, col, len, priority):
    cmd = "call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})"
    vim.command(cmd.format(group, line, col, len, priority))


def __vim_clear_match_pri(*priorities):
    cmd = "call s:clear_match_pri({0})"
    vim.command(cmd.format(list(priorities)))
