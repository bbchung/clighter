import vim
import clighter_helper
from clang import cindex
import clang_service

DEF_REF_PRI = -11
SYNTAX_PRI = -12


def clear_highlight():
    vim.command(
        "call s:clear_match_pri([{0}, {1}])".format(DEF_REF_PRI, SYNTAX_PRI))
    highlight_window.hl_tick = 0
    highlight_window.syntactic_range = None
    highlight_window.highlighted_define_cur = None


def clear_def_ref():
    vim.command("call s:clear_match_pri([{0}])".format(DEF_REF_PRI))
    highlight_window.highlighted_define_cur = None


def highlight_window(clang_service, extend=50):
    tu_ctx = clang_service.get_tu_ctx(vim.current.buffer.name)
    if tu_ctx is None:
        clear_highlight()
        return

    tu = tu_ctx.translation_unit
    if tu is None:
        clear_highlight()
        return

    (top, bottom) = (vim.bindeval("line('w0')"), vim.bindeval("line('w$')"))

    draw_syntax = False
    draw_def_ref = False

    if highlight_window.hl_tick < clang_service.parse_tick or highlight_window.syntactic_range is None or top < highlight_window.syntactic_range[0] or bottom > highlight_window.syntactic_range[1]:
        draw_syntax = True
        vim.command("call s:clear_match_pri([{0}])".format(SYNTAX_PRI))
        highlight_window.hl_tick = clang_service.parse_tick

    if vim.vars["ClighterCursorHL"] == 1:
        vim_cursor, def_cursor = clighter_helper.get_vim_cursor_and_def(tu_ctx)

        if highlight_window.highlighted_define_cur is not None and (def_cursor is None or highlight_window.highlighted_define_cur != def_cursor):
            vim.command("call s:clear_match_pri([{0}])".format(DEF_REF_PRI))

        if def_cursor is not None and (highlight_window.highlighted_define_cur is None or highlight_window.highlighted_define_cur != def_cursor):
            draw_def_ref = True

            # special case for preprocessor
            if def_cursor.kind.is_preprocessing() and def_cursor.location.file.name == vim.current.buffer.name:
                __vim_matchaddpos('clighterCursorDefRef', def_cursor.location.line, def_cursor.location.column, len(
                    clighter_helper.get_spelling_or_displayname(def_cursor)), DEF_REF_PRI)

        highlight_window.highlighted_define_cur = def_cursor

    if not draw_syntax and not draw_def_ref:
        return

    target_range = [top, bottom]

    if draw_syntax:
        buflinenr = len(vim.current.buffer)
        target_range = [max(top - extend, 1), min(bottom + extend, buflinenr)]
        highlight_window.syntactic_range = target_range

    file = tu.get_file(tu_ctx.bufname)
    tokens = tu.get_tokens(extent=cindex.SourceRange.from_locations(cindex.SourceLocation.from_position(
        tu, file, target_range[0], 1), cindex.SourceLocation.from_position(tu, file, target_range[1] + 1, 1)))

    for t in tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value != 2:
            continue

        t_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(
            tu, file, t.location.line, t.location.column))  # cursor under vim

        if draw_syntax:
            __draw_token(t.location.line, t.location.column, len(
                t.spelling), t_cursor.kind, t_cursor.type.kind)

        """ Do definition/reference highlighting'
        """
        if draw_def_ref:
            t_def_cursor = clighter_helper.get_semantic_definition(t_cursor)
            if t_def_cursor is not None and t_def_cursor == highlight_window.highlighted_define_cur:
                __vim_matchaddpos(
                    'clighterCursorDefRef', t.location.line, t.location.column, len(t.spelling), DEF_REF_PRI)


highlight_window.highlighted_define_cur = None
highlight_window.hl_tick = 0
highlight_window.syntactic_range = None


def __draw_token(line, col, len, kind, type):
    if kind == cindex.CursorKind.MACRO_INSTANTIATION and 'clighterMacroInstantiation' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos(
            'clighterMacroInstantiation', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.STRUCT_DECL and 'clighterStructDecl' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterStructDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.CLASS_DECL and 'clighterClassDecl' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterClassDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.ENUM_DECL and 'clighterEnumDecl' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterEnumDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.ENUM_CONSTANT_DECL and 'clighterEnumConstantDecl' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos(
            'clighterEnumConstantDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.TYPE_REF and 'clighterTypeRef' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterTypeRef', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.FUNCTION_DECL and 'clighterFunctionDecl' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterFunctionDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.MEMBER_REF_EXPR and 'clighterMemberRefExpr' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterMemberRefExpr', line, col, len, SYNTAX_PRI)
    elif kind == (cindex.CursorKind.NAMESPACE_REF or kind == cindex.CursorKind.NAMESPACE) and 'clighterNamespace' in vim.vars['clighter_highlight_groups']:
        __vim_matchaddpos('clighterNamespace', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.DECL_REF_EXPR:
        if type == cindex.TypeKind.ENUM and 'clighterDeclRefExprEnum' in vim.vars['clighter_highlight_groups']:
            __vim_matchaddpos(
                'clighterDeclRefExprEnum', line, col, len, SYNTAX_PRI)
        elif type == cindex.TypeKind.FUNCTIONPROTO and 'clighterDeclRefExprCall' in vim.vars['clighter_highlight_groups']:
            __vim_matchaddpos(
                'clighterDeclRefExprCall', line, col, len, SYNTAX_PRI)


def __vim_matchaddpos(group, line, col, len, priority):
    vim.command("call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})".format(
        group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}',
    # '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line,
    # t.location.column-1, t.location.column+len(t.spelling) + 1));
