import vim
import string
import clighter_helper
from clang import cindex


OCCURRENCES_PRI = -11
SYNTAX_PRI = -12

CUSTOM_SYNTAX_GROUP = {
    cindex.CursorKind.INCLUSION_DIRECTIVE: 'cligherInclusionDirective',
    cindex.CursorKind.MACRO_INSTANTIATION: 'clighterMacroInstantiation',
    cindex.CursorKind.VAR_DECL: 'clighterVarDecl',
    cindex.CursorKind.STRUCT_DECL: 'clighterStructDecl',
    cindex.CursorKind.UNION_DECL: 'clighterUnionDecl',
    cindex.CursorKind.CLASS_DECL: 'clighterClassDecl',
    cindex.CursorKind.ENUM_DECL: 'clighterEnumDecl',
    cindex.CursorKind.PARM_DECL: 'clighterParmDecl',
    cindex.CursorKind.FUNCTION_DECL: 'clighterFunctionDecl',
    cindex.CursorKind.FUNCTION_TEMPLATE: 'clighterFunctionDecl',
    cindex.CursorKind.CXX_METHOD: 'clighterFunctionDecl',
    cindex.CursorKind.CONSTRUCTOR: 'clighterFunctionDecl',
    cindex.CursorKind.DESTRUCTOR: 'clighterFunctionDecl',
    cindex.CursorKind.FIELD_DECL: 'clighterFieldDecl',
    cindex.CursorKind.ENUM_CONSTANT_DECL: 'clighterEnumConstantDecl',
    cindex.CursorKind.NAMESPACE: 'clighterNamespace',
    cindex.CursorKind.CLASS_TEMPLATE: 'clighterClassDecl',
    cindex.CursorKind.TEMPLATE_TYPE_PARAMETER: 'clighterTemplateTypeParameter',
    cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER: 'clighterTemplateNoneTypeParameter',
    cindex.CursorKind.TYPE_REF: 'clighterTypeRef',  # class ref
    cindex.CursorKind.NAMESPACE_REF: 'clighterNamespaceRef',  # namespace ref
    cindex.CursorKind.TEMPLATE_REF: 'clighterTemplateRef',  # template class ref
    cindex.CursorKind.DECL_REF_EXPR:
    {
        cindex.TypeKind.FUNCTIONPROTO: 'clighterDeclRefExprCall',  # function call
        cindex.TypeKind.ENUM: 'clighterDeclRefExprEnum',  # enum ref
        cindex.TypeKind.TYPEDEF: 'clighterTypeRef',  # ex: cout
    },
    cindex.CursorKind.MEMBER_REF: 'clighterDeclRefExprCall',  # ex: designated initializer
    cindex.CursorKind.MEMBER_REF_EXPR:
    {
        cindex.TypeKind.UNEXPOSED: 'clighterMemberRefExprCall',  # member function call
    },
}


def clear_all():
    __vim_clear_match_pri(OCCURRENCES_PRI, SYNTAX_PRI)
    hl_window.symbol = None
    vim.current.window.vars['clighter_hl'] = [
        -1, [], []]  # [hl_tick, syntax_range, occurrences_range]


def clear_occurrences():
    __vim_clear_match_pri(OCCURRENCES_PRI)
    vim.current.window.vars['clighter_hl'][2] = []
    hl_window.symbol = None


def config_win_context(init):
    if not init and 'clighter_hl' in vim.current.window.vars:
        return

    clear_all()
    vim.current.window.vars['clighter_hl'] = [
        -1, [], []]  # [hl_tick, syntax_range, symbol_range]


def hl_window(clang_service, do_occurrences):
    cc = clang_service.get_cc(vim.current.buffer.name)
    if not cc:
        return

    parse_tick = cc.parse_tick

    tu = cc.current_tu
    if not tu:
        return

    top = string.atoi(vim.eval("line('w0')"))
    bottom = string.atoi(vim.eval("line('w$')"))
    height = bottom - top + 1

    symbol = None

    if vim.eval('g:ClighterOccurrences') == '1':
        vim_cursor = clighter_helper.get_vim_cursor(tu)
        symbol = clighter_helper.get_vim_symbol(vim_cursor)

    occurrences_range = w_range = [top, bottom]
    syntax_range = [max(top - height, 1), min(
        bottom + height, len(vim.current.buffer))]

    config_win_context(False)

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

    hl_window.symbol = symbol

    __do_highlight(
        tu,
        vim.current.buffer.name,
        syntax_range,
        occurrences_range,
        parse_tick)


def __do_highlight(tu, file_name, syntax_range, occurrences_range, tick):
    file = tu.get_file(file_name)

    if not syntax_range and (not hl_window.symbol or not occurrences_range):
        return

    if syntax_range:
        vim.current.window.vars['clighter_hl'][1] = syntax_range

    if occurrences_range and hl_window.symbol:
        vim.current.window.vars['clighter_hl'][2] = occurrences_range

    union_range = __union(syntax_range, occurrences_range)

    location1 = cindex.SourceLocation.from_position(
        tu, file, line=union_range[0], column=1)
    location2 = cindex.SourceLocation.from_position(
        tu, file, line=union_range[1] + 1, column=1)
    tokens = tu.get_tokens(
        extent=cindex.SourceRange.from_locations(
            location1,
            location2))

    syntax = {}
    occurrence = {'clighterOccurrences':[]}
    for token in tokens:
        if token.kind.value != 2:  # no keyword, comment
            continue

        t_cursor = token.cursor
        t_cursor._tu = tu

        # t_cursor = cindex.Cursor.from_location(
            # tu,
            # cindex.SourceLocation.from_position(
                # tu, file,
                # token.location.line,
                # token.location.column
            # )
        # )

        pos = [token.location.line, token.location.column, len( token.spelling)]

        if t_cursor.spelling == token.spelling and __is_in_range(token.location.line, syntax_range):
            group = __get_syntax_group(t_cursor.kind, t_cursor.type.kind)
            if group:
                if not syntax.has_key(group):
                    syntax[group] = []

                syntax[group].append(pos)

        if hl_window.symbol and __is_in_range(token.location.line, occurrences_range):
            t_symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if t_symbol and token.spelling == t_symbol.spelling and t_symbol == hl_window.symbol:
                occurrence['clighterOccurrences'].append(pos)

    cmd = "call MatchIt({0}, {1})".format(syntax, SYNTAX_PRI)
    vim.command(cmd)

    cmd = "call MatchIt({0}, {1})".format(occurrence , OCCURRENCES_PRI)
    vim.command(cmd)

    vim.current.window.vars['clighter_hl'][0] = tick


def __get_default_syn(cursor_kind):
    if cursor_kind.is_preprocessing():
        return 'clighterPrepro'
    elif cursor_kind.is_declaration():
        return 'clighterDecl'
    elif cursor_kind.is_reference():
        return 'clighterRef'
    else:
        return None


def __get_syntax_group(cursor_kind, type_kind):
    group = __get_default_syn(cursor_kind)

    custom = CUSTOM_SYNTAX_GROUP.get(cursor_kind)
    if custom:
        if cursor_kind == cindex.CursorKind.DECL_REF_EXPR:
            custom = custom.get(type_kind)
            if custom:
                group = custom
        elif cursor_kind == cursor_kind == cindex.CursorKind.MEMBER_REF_EXPR:
            custom = custom.get(type_kind)
            if custom:
                group = custom
            else:
                group = 'clighterMemberRefExprVar'
        else:
            group = custom

    if group in vim.eval('g:clighter_highlight_blacklist'):
        return None

    return group


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
