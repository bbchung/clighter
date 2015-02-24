import vim
import string
import clighter_helper
from clang import cindex
import clang_service

SYMBOL_REF_PRI = -11
SYNTAX_PRI = -12


def clear_highlight():
    __vim_clear_match_pri(SYMBOL_REF_PRI, SYNTAX_PRI)
    highlight_window.syntactic_range = None
    highlight_window.symbol = None


def clear_symbol_ref():
    __vim_clear_match_pri(SYMBOL_REF_PRI)
    highlight_window.symbol = None


def highlight_window(clang_service):
    cc = clang_service.get_cc(vim.current.buffer.name)
    if cc is None:
        return

    parse_tick = cc.parse_tick

    tu = cc.current_tu
    if tu is None:
        return

    top = string.atoi(vim.eval("line('w0')"))
    bottom = string.atoi(vim.eval("line('w$')"))

    draw_syntax = False
    draw_symbol_ref = False

    if vim.current.window.vars['hl_tick'] < parse_tick \
            or highlight_window.syntactic_range is None \
            or top < highlight_window.syntactic_range[0] \
            or bottom > highlight_window.syntactic_range[1]:
        draw_syntax = True
        __vim_clear_match_pri(SYNTAX_PRI)
        vim.current.window.vars['hl_tick'] = parse_tick

    file = tu.get_file(cc.name)
    if vim.eval('g:ClighterCursorHL') == '1':
        vim_cursor = clighter_helper.get_vim_cursor(tu, file)
        symbol = clighter_helper.get_vim_symbol(vim_cursor)

        if highlight_window.symbol and (symbol is None or symbol != highlight_window.symbol):
            __vim_clear_match_pri(SYMBOL_REF_PRI)

        if symbol and (highlight_window.symbol is None or symbol != highlight_window.symbol):
            draw_symbol_ref = True

        highlight_window.symbol = symbol

    if not draw_syntax and not draw_symbol_ref:
        return

    target_range = [top, bottom]
    height = bottom - top + 1

    if draw_syntax:
        buflinenr = len(vim.current.buffer)
        target_range = [
            max(top - height, 1),
            min(bottom + height, buflinenr)
        ]
        highlight_window.syntactic_range = target_range

    location1 = cindex.SourceLocation.from_position(
        tu, file, line=target_range[0], column=1)
    location2 = cindex.SourceLocation.from_position(
        tu, file, line=target_range[1] + 1, column=1)
    tokens = tu.get_tokens(
        extent=cindex.SourceRange.from_locations(
            location1,
            location2))

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
        )

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
        if draw_symbol_ref and t.location.line >= top and t.location.line <= bottom:
            t_symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if t_symbol and t.spelling == t_symbol.spelling and t_symbol == highlight_window.symbol:
                __vim_matchaddpos(
                    group='clighterCursorSymbolRef',
                    line=t.location.line,
                    col=t.location.column,
                    len=len(t.spelling),
                    priority=SYMBOL_REF_PRI
                )

highlight_window.syntactic_range = None
highlight_window.symbol = None

group_map = {
    cindex.CursorKind.MACRO_INSTANTIATION: 'clighterMacroInstantiation',
        cindex.CursorKind.STRUCT_DECL: 'clighterStructDecl',
        cindex.CursorKind.CLASS_DECL: 'clighterClassDecl',
        cindex.CursorKind.ENUM_DECL: 'clighterEnumDecl',
        cindex.CursorKind.ENUM_CONSTANT_DECL: 'clighterEnumConstantDecl',
        cindex.CursorKind.TYPE_REF: 'clighterTypeRef',
        cindex.CursorKind.FUNCTION_DECL: 'clighterFunctionDecl',
        cindex.CursorKind.MEMBER_REF_EXPR: 'clighterMemberRefExpr',
        cindex.CursorKind.NAMESPACE_REF: 'clighterNamespace',
        cindex.CursorKind.NAMESPACE: 'clighterNamespace',
        cindex.CursorKind.DECL_REF_EXPR:
        {
            cindex.TypeKind.ENUM: 'clighterDeclRefExprEnum',
            cindex.TypeKind.FUNCTIONPROTO: 'clighterDeclRefExprCall'
        }
}


def __draw_token(line, col, len, cursor_kind, type_kind):
    highlight_groups = vim.eval('g:clighter_highlight_groups')

    group = group_map.get(cursor_kind)
    if group is None:
        return

    if isinstance(group, dict):
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
