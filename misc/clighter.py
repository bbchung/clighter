import vim
from clang import cindex
from clang_service import ClangService
import clang_helper

DEF_REF_PRI = -11
SYNTAX_PRI = -12

if vim.vars['clighter_libclang_file']:
    ClangService.set_libclang_file(vim.vars['clighter_libclang_file'])

__clang_service = ClangService()

# def bfs(c, top, bottom, queue):
# if c.location.line >= top and c.location.line <= bottom:
#__draw_token(c)

# queue.put(c.get_children())

# while not queue.empty():
#curs = queue.get()
# for cur in curs:
# if cur.location.line >= top and cur.location.line <= bottom:
#__draw_token(cur)

# queue.put(cur.get_children())


# def dfs(cursor):
#    print cursor.location, cursor.spelling
#    for c in cursor.get_children():
#        dfs(c)

def clear_def_ref():
    vim.command("call s:clear_match_pri([{0}])".format(DEF_REF_PRI))
    highlight_window.highlighted_define_cur = None


def clear_highlight():
    vim.command(
        "call s:clear_match_pri([{0}, {1}])".format(DEF_REF_PRI, SYNTAX_PRI))
    highlight_window.highlighted_tu = None
    highlight_window.syntactic_range = None
    highlight_window.highlighted_define_cur = None


def highlight_window(extend=50):
    tu_ctx = __clang_service.get_tu_ctx(vim.current.buffer.name)
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

    if highlight_window.highlighted_tu is None or highlight_window.highlighted_tu != tu or highlight_window.syntactic_range is None or top < highlight_window.syntactic_range[0] or bottom > highlight_window.syntactic_range[1]:
        draw_syntax = True
        vim.command("call s:clear_match_pri([{0}])".format(SYNTAX_PRI))
        highlight_window.highlighted_tu = tu

    if vim.bindeval("s:cursor_hl") == 1:
        vim_cursor = tu_ctx.get_cursor(vim.current.window.cursor)
        def_cursor = clang_helper.get_semantic_definition(vim_cursor)

        if highlight_window.highlighted_define_cur is not None and (def_cursor is None or highlight_window.highlighted_define_cur != def_cursor):
            vim.command("call s:clear_match_pri([{0}])".format(DEF_REF_PRI))

        if def_cursor is not None and (highlight_window.highlighted_define_cur is None or highlight_window.highlighted_define_cur != def_cursor):
            draw_def_ref = True

            # special case for preprocessor
            if def_cursor.kind.is_preprocessing() and def_cursor.location.file.name == vim.current.buffer.name:
                __vim_matchaddpos('clighterCursorDefRef', def_cursor.location.line, def_cursor.location.column, len(
                    clang_helper.get_spelling_or_displayname(def_cursor)), DEF_REF_PRI)

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
            t_def_cursor = clang_helper.get_semantic_definition(t_cursor)
            if t_def_cursor is not None and t_def_cursor == highlight_window.highlighted_define_cur:
                __vim_matchaddpos(
                    'clighterCursorDefRef', t.location.line, t.location.column, len(t.spelling), DEF_REF_PRI)


highlight_window.highlighted_define_cur = None
highlight_window.highlighted_tu = None
highlight_window.syntactic_range = None


def refactor_rename():
    tu_ctx = __clang_service.get_tu_ctx(vim.current.buffer.name)
    if tu_ctx is None:
        return

    __clang_service.update_unsaved_dict(__get_buffer_dict(), False)
    try:
        __clang_service.parse(tu_ctx)
    except:
        return

    vim_cursor = tu_ctx.get_cursor(vim.current.window.cursor)
    def_cursor = clang_helper.get_semantic_definition(vim_cursor)
    if def_cursor is None:
        return

    old_name = clang_helper.get_spelling_or_displayname(def_cursor)
    new_name = vim.bindeval(
        "input('rename \"{0}\" to: ', '{1}')".format(old_name, old_name))

    if not new_name or old_name == new_name:
        return

    print ' '

    pos = vim.current.window.cursor

    locs = set()
    locs.add((def_cursor.location.line, def_cursor.location.column,
              def_cursor.location.file.name))
    clang_helper.search_ref_cursors(
        tu_ctx.translation_unit.cursor, def_cursor, locs)
    __vim_multi_replace(locs, old_name, new_name)

    if clang_helper.is_symbol_cursor(def_cursor) and vim.vars['clighter_enable_cross_rename'] == 1:
        __cross_buffer_rename(def_cursor.get_usr(), new_name)

    vim.current.window.cursor = pos

    __clang_service.update_unsaved_dict(__get_buffer_dict())


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


def __cross_buffer_rename(usr, new_name):
    call_bufnr = vim.current.buffer.number

    vim.command("bn!")
    while vim.current.buffer.number != call_bufnr:
        tu_ctx = __clang_service.get_tu_ctx(vim.current.buffer.name)
        if tu_ctx is not None:
            try:
                __clang_service.parse(tu_ctx)
                __search_usr_and_rename_refs(
                    tu_ctx.translation_unit, usr, new_name)
            except:
                pass

        vim.command("bn!")


def __search_usr_and_rename_refs(tu, usr, new_name):
    if tu is None:
        return

    symbols = []
    clang_helper.find_cursors_by_usr(tu.cursor, usr, symbols)

    if not symbols:
        return

    if vim.vars['clighter_rename_prompt_level'] >= 1:
        cmd = "let l:choice = confirm(\"found symbols in {0}, rename them?\", \"&Yes\n&No\", 1)".format(
            vim.current.buffer.name)
        vim.command(cmd)

        if vim.bindeval('l:choice') == 2:
            return

    # all symbols with the same name
    old_name = clang_helper.get_spelling_or_displayname(symbols[0])

    locs = set()
    for sym in symbols:
        locs.add(
            (sym.location.line, sym.location.column, sym.location.file.name))
        clang_helper.search_ref_cursors(tu.cursor, sym, locs)

    __vim_multi_replace(locs, old_name, new_name)


def __vim_multi_replace(locs, old, new):
    if locs is None:
        return

    pattern = ""

    for line, column, file in locs:
        if file is None or file != vim.current.buffer.name:
            continue

        if pattern:
            pattern += "\|"

        pattern += "\%" + str(line) + "l" + "\%>" + str(
            column - 1) + "c\%<" + str(column + len(old)) + "c" + old

    if not pattern:
        return

    cmd = "%s/" + pattern + "/" + new + "/gI"

    if vim.vars['clighter_rename_prompt_level'] >= 2:
        cmd = cmd + "c"

    vim.command(cmd)


def __vim_matchaddpos(group, line, col, len, priority):
    vim.command("call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})".format(
        group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}',
    # '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line,
    # t.location.column-1, t.location.column+len(t.spelling) + 1));


def __get_buffer_dict():
    dict = {}

    for buf in vim.buffers:
        if not __is_buffer_allowed(buf):
            continue

        if len(buf) == 1 and buf[0] == "":
            continue

        dict[buf.name] = '\n'.join(buf)

    return dict


def clang_start_service():
    return __clang_service.start(eval(vim.vars["ClighterCompileArgs"]))


def clang_stop_service():
    return __clang_service.stop()


def clang_set_compile_args(args):
    __clang_service.set_compile_args(args)


def clang_create_all_tu():
    list = []
    for buf in vim.buffers:
        if __is_buffer_allowed(buf):
            list.append(buf.name)

    __clang_service.create_tu(list)


def on_TextChanged():
    if __is_buffer_allowed(vim.current.buffer):
        __clang_service.update_unsaved(
            vim.current.buffer.name, '\n'.join(vim.current.buffer))


def on_FileType():
    if __is_buffer_allowed(vim.current.buffer):
        __clang_service.create_tu([vim.current.buffer.name])
    else:
        __clang_service.remove_tu([vim.current.buffer.name])
        clear_highlight()


def __is_buffer_allowed(buf):
    return buf.options['filetype'] in ["c", "cpp", "objc"]
