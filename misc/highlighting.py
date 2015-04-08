import vim
import string
import clighter_helper
from clang import cindex


OCCURRENCES_PRI = -11
SYNTAX_PRI = -12

SYNTAX_GROUP_MAP = {
    cindex.CursorKind.MACRO_INSTANTIATION: 'clighterMacroInstantiation',
    cindex.CursorKind.STRUCT_DECL: 'clighterStructDecl',
    cindex.CursorKind.UNION_DECL: 'clighterUnionDecl',
    cindex.CursorKind.CLASS_DECL: 'clighterClassDecl',
    cindex.CursorKind.ENUM_DECL: 'clighterEnumDecl',
    cindex.CursorKind.FIELD_DECL: 'clighterFieldDecl',
    cindex.CursorKind.FUNCTION_DECL: 'clighterFunctionDecl',
    cindex.CursorKind.CXX_METHOD: 'clighterFunctionDecl',
    cindex.CursorKind.ENUM_CONSTANT_DECL: 'clighterEnumConstantDecl',
    cindex.CursorKind.NAMESPACE: 'clighterNamespace',
    cindex.CursorKind.CLASS_TEMPLATE: 'clighterClassDecl',
    cindex.CursorKind.TEMPLATE_TYPE_PARAMETER: 'clighterTemplateTypeParameter',
    cindex.CursorKind.TYPE_REF: 'clighterTypeRef',
    cindex.CursorKind.MEMBER_REF_EXPR: 'clighterMemberRefExpr',
    cindex.CursorKind.NAMESPACE_REF: 'clighterNamespace',
    cindex.CursorKind.TEMPLATE_REF: 'clighterTemplateRef',
    cindex.CursorKind.DECL_REF_EXPR:
    {
        cindex.TypeKind.FUNCTIONPROTO: 'clighterDeclRefExprCall',
        cindex.TypeKind.ENUM: 'clighterDeclRefExprEnum',
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
    cc = clang_service.get_cc(vim.current.buffer.name)
    if not cc:
        return

    parse_tick = cc.parse_tick

    tu = cc.current_tu
    if not tu:
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

    # draw_map = {}  # {priority:{group:[[[line, column, len]]]}}

    for token in tokens:
        if token.kind.value != 2:
            continue

        t_cursor = cindex.Cursor.from_location(
            tu,
            cindex.SourceLocation.from_position(
                tu, f,
                token.location.line,
                token.location.column
            )
        )

        pos = [
            [token.location.line, token.location.column, len(
                token.spelling)]]

        if __is_in_range(token.location.line, syntax_range):
            group = __get_syntax_group(t_cursor.kind, t_cursor.type.kind)
            if group:
                __vim_matchaddpos(group, pos, SYNTAX_PRI)

            #__add_to_draw_map(
               # draw_map, SYNTAX_PRI, group, [token.location.line,
               # token.location.column, len( token.spelling)])

        if symbol and __is_in_range(token.location.line, occurrences_range):
            t_symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if t_symbol and token.spelling == t_symbol.spelling and t_symbol == symbol:
                __vim_matchaddpos('clighterOccurrences', pos, OCCURRENCES_PRI)

               #__add_to_draw_map(
                # draw_map, OCCURRENCES_PRI, 'clighterOccurrences', [
                # token.location.line, token.location.column, len(
                # token.spelling)])

    #__draw(draw_map, tick)
    vim.current.window.vars['clighter_hl'][0] = tick


# def __draw(draw_map, tick):
    # for priority, group_map in draw_map.items():
    # for group, draw_pos in group_map.items():
    # for pos in draw_pos:
    #__vim_matchaddpos(
    # group=group,
    # pos=pos,
    # priority=priority
    #)


# def __add_to_draw_map(draw_map, priority, group, pos):
    # if not group or not pos:
    # return

    # if not draw_map.get(priority):
    #draw_map[priority] = {}

    # if not draw_map[priority].get(group):
    #draw_map[priority][group] = [[pos]]
    # return

    # if len(draw_map[priority][group][-1]) < 8:
    # draw_map[priority][group][-1].append(pos)
    # else:
    # draw_map[priority][group].append([pos])


def __get_syntax_group(cursor_kind, type_kind):
    group = SYNTAX_GROUP_MAP.get(cursor_kind)
    if not group:
        return None

    if cursor_kind == cindex.CursorKind.DECL_REF_EXPR:
        group = group.get(type_kind)
        if not group:
            return None

    if group not in vim.eval('g:clighter_syntax_groups'):
        return None

    return group


def __vim_matchaddpos(group, pos, priority):
    cmd = "call matchaddpos('{0}', {1}, {2})".format(group, pos, priority)
    vim.command(cmd)


def __vim_clear_match_pri(*priorities):
    cmd = "call s:clear_match_pri({0})".format(list(priorities))
    vim.command(cmd)


def __union(range1, range2):
    if range1 and range2:
        return [min(range1[0], range2[0]), max(range1[1], range2[1])]
    elif range1 and not range2:
        return range1
    elif not range1 and range2:
        return range2
    else:
        return None


def __is_in_range(value, range):
    if not range:
        return False

    if value >= range[0] and value <= range[1]:
        return True

    return False


def __is_subrange(inner, outer):
    if not inner:
        return True

    if not outer:
        return False

    if inner[0] < outer[0]:
        return False

    if inner[1] > outer[1]:
        return False

    return True
