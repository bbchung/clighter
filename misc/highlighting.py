import vim
import string
import clighter_helper
from clang import cindex


OCCURRENCES_PRI = -11
SYNTAX_PRI = -12

SYNTAX_GROUP_MAP = {
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


def clear_all():
    __vim_clear_match_pri(OCCURRENCES_PRI, SYNTAX_PRI)
    vim.current.window.vars['clighter_hl'] = [
        -1, [], []]  # [hl_tick, syntax_range, occurrences_range]


def clear_occurrences():
    __vim_clear_match_pri(OCCURRENCES_PRI)
    vim.current.window.vars['clighter_hl'][2] = []
    hl_window.symbol = None


def hl_window(clang_service, do_occurrences):
    cc = clang_service.current_cc
    if cc is None:
        return

    parse_tick = cc.parse_tick

    tu = cc.current_tu
    if tu is None:
        return

    current_file = tu.get_file(cc.name)

    top = string.atoi(vim.eval("line('w0')"))
    bottom = string.atoi(vim.eval("line('w$')"))
    height = bottom - top + 1

    symbol = None

    if vim.eval('g:ClighterOccurrences') == '1':
        vim_cursor = clighter_helper.get_vim_cursor(tu, current_file)
        symbol = clighter_helper.get_vim_symbol(vim_cursor)

    occurrences_range = w_range = [top, bottom]
    syntax_range = [max(top - height, 1), min(
        bottom + height, len(vim.current.buffer))]

    if vim.current.window.vars['clighter_hl'][0] < parse_tick:
        clear_all()
    else:
        if not __is_subrange(
            w_range, list(
                vim.current.window.vars['clighter_hl'][1])):
            __vim_clear_match_pri(SYNTAX_PRI)
        else:
            syntax_range = None

        if not __is_subrange(
            w_range, list(
                vim.current.window.vars['clighter_hl'][2])) or (
            hl_window.symbol and (
                not symbol or symbol != hl_window.symbol)):
            clear_occurrences()
        else:
            occurrences_range = None

    if not do_occurrences:
        occurrences_range = None

    __do_highlight(
        tu,
        current_file,
        syntax_range,
        symbol,
        occurrences_range,
        parse_tick)


def __do_highlight(tu, f, syntax_range, symbol, occurrences_range, tick):
    if not syntax_range and (not symbol or not occurrences_range):
        return

    if syntax_range:
        vim.current.window.vars['clighter_hl'][1] = syntax_range

    if occurrences_range and symbol:
        vim.current.window.vars['clighter_hl'][2] = occurrences_range
        hl_window.symbol = symbol

    union_range = __union(syntax_range, occurrences_range)

    location1 = cindex.SourceLocation.from_position(
        tu, f, line=union_range[0], column=1)
    location2 = cindex.SourceLocation.from_position(
        tu, f, line=union_range[1] + 1, column=1)
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
                tu, f,
                t.location.line,
                t.location.column
            )
        )

        if __is_in_range(t.location.line, syntax_range):
            __draw_syntax(
                line=t.location.line,
                col=t.location.column,
                length=len(t.spelling),
                cursor_kind=t_cursor.kind,
                type_kind=t_cursor.type.kind
            )

        if symbol and __is_in_range(t.location.line, occurrences_range):
            t_symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if t_symbol and t.spelling == t_symbol.spelling and t_symbol == symbol:
                __vim_matchaddpos(
                    group='clighterOccurrences',
                    line=t.location.line,
                    col=t.location.column,
                    length=len(t.spelling),
                    priority=OCCURRENCES_PRI
                )

    vim.current.window.vars['clighter_hl'][0] = tick


def __draw_syntax(line, col, length, cursor_kind, type_kind):
    syntax_groups = vim.eval('g:clighter_syntax_groups')

    group = SYNTAX_GROUP_MAP.get(cursor_kind)
    if group is None:
        return

    if group == cindex.CursorKind.DECL_REF_EXPR:
        group = group.get(type_kind)
        if group is None:
            return

    if group in syntax_groups:
        __vim_matchaddpos(group, line, col, length, SYNTAX_PRI)


def __vim_matchaddpos(group, line, col, length, priority):
    cmd = "call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})"
    vim.command(cmd.format(group, line, col, length, priority))


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


def __is_in_range(value, r):
    if r is None:
        return False

    if value >= r[0] and value <= r[1]:
        return True

    return False


def __is_subrange(range1, range2):
    if not range1:
        return True

    if not range2:
        return False

    if range1[0] < range2[0]:
        return False

    if range1[1] > range2[1]:
        return False

    return True
