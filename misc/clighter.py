import vim
from clang import cindex
from threading import Thread, Lock

gTu = [None, 0]


if vim.eval("g:clighter_libclang_file") != "":
    cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))


def start_parsing():
    t = Thread(target=do_parsing, args=(vim.eval('g:clighter_clang_options'),))
    t.start()


def do_parsing(options):
    global gTu
    global mutext

    try:
        idx = cindex.Index.create()
    except:
        vim.command('echohl WarningMsg | echomsg "Clighter runtime error: libclang error" | echohl None')
        return

    gTu[0] = idx.parse(vim.current.buffer.name, options, [(vim.current.buffer.name, "\n".join(vim.current.buffer))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    gTu[1] = 1


def try_highlight():
    global gTu
    global mutext

    curr_tu = gTu[0]
    if curr_tu is None:
        return

    if curr_tu.get_file(vim.current.buffer.name) == None:
        return

    w_top = int(vim.eval("line('w0')"))
    w_bottom = int(vim.eval("line('w$')"))

    window = vim.eval("w:window")
    if window != [] and w_top >= window[0] and w_bottom <= window[1] and gTu[1] == 0:
        return

    gTu[1] = 0

    vim.command('call s:clear_match("cursor_def_ref")')
    vim.command('call s:clear_match("semantic")')


    window_size = int(vim.eval('g:clighter_window_size'))
    file = cindex.File.from_name(curr_tu, vim.current.buffer.name)

    if (window_size < 0):
        vim.command("let w:window=[]")
        window_tokens = curr_tu.cursor.get_tokens()
    else:
        top_line = max(w_top - 100 * window_size, 1);
        bottom_line = min(w_bottom + 100 * window_size, len(vim.current.buffer))
        vim.command("let w:window=[" + `top_line` + ", " + `bottom_line` + "]")
        top = cindex.SourceLocation.from_position(curr_tu, file, top_line, 1)
        bottom = cindex.SourceLocation.from_position(curr_tu, file, bottom_line, 1)
        range = cindex.SourceRange.from_locations(top, bottom)
        window_tokens = curr_tu.get_tokens(extent=range)

    vim_cursor = None
    if int(vim.eval("s:cursor_decl_ref_hl_on")) == 1:
        (row, col) = vim.current.window.cursor
        vim_cursor = cindex.Cursor.from_location(curr_tu, cindex.SourceLocation.from_position(curr_tu, file, row, col + 1)) # cusor under vim-cursor

    def_cursor = None
    if vim_cursor is not None:
        if vim_cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
            def_cursor = vim_cursor
        else:
            def_cursor = vim_cursor.get_definition()

        """ Do declaring highlighting'
        """

        if def_cursor is not None and def_cursor.location.file.name == vim_cursor.location.file.name:
            if def_cursor.kind.is_declaration():
                vim_match_add('cursor_def_ref', 'CursorDeclRef', def_cursor.location.line, def_cursor.location.column, len(def_cursor.spelling), -1)
            if def_cursor.kind.is_preprocessing():
                t = def_cursor.get_tokens().next()
                vim_match_add('cursor_def_ref', 'CursorDeclRef', t.location.line, t.location.column, len(t.spelling), -1)

    highlight_window(curr_tu, window_tokens, def_cursor, file)


def highlight_window(tu, window_tokens, def_cursor, curr_file):
    ref_spelling = None
    
    #print decl_ref_cursor.kind

    for t in window_tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value == 2:
            t_tu_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(tu, curr_file, t.location.line, t.location.column))

            if t_tu_cursor.kind == cindex.CursorKind.MACRO_INSTANTIATION:
                vim_match_add('semantic', 'MacroInstantiation', t.location.line, t.location.column, len(t.spelling), -2)
            elif t_tu_cursor.kind == cindex.CursorKind.STRUCT_DECL:
                vim_match_add('semantic', 'StructDecl', t.location.line, t.location.column, len(t.spelling), -2)
            elif t_tu_cursor.kind == cindex.CursorKind.CLASS_DECL:
                vim_match_add('semantic', 'ClassDecl', t.location.line, t.location.column, len(t.spelling), -2)
            elif t_tu_cursor.kind == cindex.CursorKind.ENUM_DECL:
                vim_match_add('semantic', 'EnumDecl', t.location.line, t.location.column, len(t.spelling), -2)
            elif t_tu_cursor.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                vim_match_add('semantic', 'EnumConstantDecl', t.location.line, t.location.column, len(t.spelling), -2)
            elif t_tu_cursor.kind == cindex.CursorKind.TYPE_REF:
                vim_match_add('semantic', 'TypeRef', t.location.line, t.location.column, len(t.spelling), -2)
            elif t_tu_cursor.kind == cindex.CursorKind.DECL_REF_EXPR and t_tu_cursor.type.kind == cindex.TypeKind.ENUM:
                vim_match_add('semantic', 'EnumDeclRefExpr', t.location.line, t.location.column, len(t.spelling), -2)

            """ Do reference highlighting'
            """
            if def_cursor is not None:
                t_def_cursor = t_tu_cursor.get_definition()
                if t_def_cursor is not None and t_def_cursor == def_cursor:
                    vim_match_add('cursor_def_ref', 'CursorDeclRef', t.location.line, t.location.column, len(t.spelling), -1)


def vim_match_add(type, group, line, col, len, priority):
    vim.command("call add(w:highlight_dict['{0}'], matchaddpos('{1}', [[{2}, {3}, {4}]], {5}))".format(type, group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));
