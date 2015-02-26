import vim
import string
import clighter_helper
from clang import cindex
import clang_service

SYMBOL_REF_PRI = -11
SYNTAX_PRI = -12

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


def clear_highlight():
    __vim_clear_match_pri(SYMBOL_REF_PRI, SYNTAX_PRI)
    hl_window.syntax_range = None
    hl_window.symbol_range = None
    hl_window.symbol = None


def clear_symbol_hl():
    __vim_clear_match_pri(SYMBOL_REF_PRI)
    hl_window.symbol_range = None
    hl_window.symbol = None


def hl_window(clang_service, do_symbol_hl):
    cc = clang_service.get_cc(vim.current.buffer.name)
    if cc is None:
        return

    parse_tick = cc.parse_tick

    tu = cc.current_tu
    if tu is None:
        return

    file = tu.get_file(cc.name)

    top = string.atoi(vim.eval("line('w0')"))
    bottom = string.atoi(vim.eval("line('w$')"))
    height = bottom - top + 1

    symbol = None

    if vim.eval('g:ClighterCursorHL') == '1':
        vim_cursor = clighter_helper.get_vim_cursor(tu, file)
        symbol = clighter_helper.get_vim_symbol(vim_cursor)

    w_range = [top, bottom]
    syntax_range = [max(top - height, 1), min(
        bottom + height, len(vim.current.buffer))]
    symbol_range = w_range

    if vim.current.window.vars['hl_tick'] < parse_tick:
        clear_highlight()
    else:
        if not __is_contained_in(w_range, hl_window.syntax_range):
            __vim_clear_match_pri(SYNTAX_PRI)
        else:
            syntax_range = None

        if not __is_contained_in(w_range, hl_window.symbol_range) or (hl_window.symbol and (not symbol or symbol != hl_window.symbol)):
            clear_symbol_hl()
        else:
            symbol_range = None

    if not do_symbol_hl:
        symbol_range = None

    __do_highlight(tu, file, syntax_range, symbol, symbol_range)
    vim.current.window.vars['hl_tick'] = parse_tick

hl_window.syntax_range = None
hl_window.symbol_range = None
hl_window.symbol = None


def __do_highlight(tu, file, syntax_range, symbol, symbol_range):
    if not syntax_range and (not symbol or not symbol_range):
        return

    if syntax_range:
        hl_window.syntax_range = syntax_range

    if symbol_range and symbol:
        hl_window.symbol_range = symbol_range
        hl_window.symbol = symbol

    union_range = __union(syntax_range, symbol_range)

    location1 = cindex.SourceLocation.from_position(
        tu, file, line=union_range[0], column=1)
    location2 = cindex.SourceLocation.from_position(
        tu, file, line=union_range[1] + 1, column=1)
    tokens = tu.get_tokens(
        extent=cindex.SourceRange.from_locations(
            location1,
            location2))

    for t in tokens:
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

        if syntax_range:
            __draw_token(
                line=t.location.line,
                col=t.location.column,
                len=len(t.spelling),
                cursor_kind=t_cursor.kind,
                type_kind=t_cursor.type.kind
            )

        if symbol and symbol_range:
            t_symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if t_symbol and t.spelling == t_symbol.spelling and t_symbol == symbol:
                __vim_matchaddpos(
                    group='clighterCursorSymbolRef',
                    line=t.location.line,
                    col=t.location.column,
                    len=len(t.spelling),
                    priority=SYMBOL_REF_PRI
                )


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


def __union(range1, range2):
    if range1 and range2:
        return [min(range1[0], range2[0]), max(range1[1], range2[1])]
    elif range1 and not range2:
        return range1
    elif not range1 and range2:
        return range2
    else:
        return None


def __is_contained_in(range1, range2):
    if not range1:
        return True

    if not range2:
        return False

    if range1[0] < range2[0]:
        return False

    if range1[1] > range2[1]:
        return False

    return True
