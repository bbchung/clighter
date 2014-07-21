import vim
from clang import cindex
from threading import Thread
import time

if vim.eval("g:clighter_libclang_file") != "":
    cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))

g_tu = [None, 0] # [translation unit, have new tu for semantic]
g_parsing = [None, None, 0] # [thread, timeup, on/off]

def start_parsing_thread():
    global g_parsing

    if g_parsing[0] is not None:
        return

    g_parsing[1] = time.time()*1000.0
    g_parsing[2] = 1
    g_parsing[0] = Thread(target=parsing_worker)
    g_parsing[0].start()

def stop_parsing_thread():
    global g_parsing

    if g_parsing[0] is None:
        return

    g_parsing[2] = 0
    g_parsing[0].join()
    g_parsing[0] = None
    g_parsing[1] = None
    

def reset_timeup():
    global g_parsing

    g_parsing[1] = time.time()*1000.0 + 500


def parsing_worker():
    global g_parsing

    while g_parsing[2] == 1:
        if g_parsing[1] != None and time.time() * 1000.0 > g_parsing[1]:
            g_parsing[1] = None
            do_parsing(vim.eval('g:clighter_clang_options'))

        time.sleep (500.0 / 1000.0);


def do_parsing(options):
    global g_tu

    try:
        idx = cindex.Index.create()
    except:
        vim.command('echohl WarningMsg | echomsg "Clighter runtime error: libclang error" | echohl None')
        return

    g_tu[0] = idx.parse(vim.current.buffer.name, options, [(vim.current.buffer.name, "\n".join(vim.current.buffer))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    g_tu[1] = 1


def try_highlight():
    global g_tu

    curr_tu = g_tu[0]
    if curr_tu is None:
        return

    if curr_tu.get_file(vim.current.buffer.name) == None:
        return

    w_top = int(vim.eval("line('w0')"))
    w_bottom = int(vim.eval("line('w$')"))
    window = [int(vim.eval("w:window[0]")), int(vim.eval("w:window[1]"))]

    resemantic = w_top < window[0] or w_bottom > window[1] or g_tu[1] == 1

    window_size = int(vim.eval('g:clighter_window_size'))
    file = cindex.File.from_name(curr_tu, vim.current.buffer.name)

    if (window_size < 0):
        vim.command("let w:window=[0, %d]" % len(vim.current.buffer))
        window_tokens = curr_tu.cursor.get_tokens()
    else:
        top_line = max(w_top - 100 * window_size, 1);
        bottom_line = min(w_bottom + 100 * window_size, len(vim.current.buffer))
        vim.command("let w:window=[%d, %d]" %(top_line, bottom_line))
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


    highlight_window(curr_tu, window_tokens, def_cursor, file, resemantic)


def highlight_window(tu, window_tokens, def_cursor, curr_file, resemantic):
    vim.command('call s:clear_match("cursor_def_ref")')
    if resemantic:
        vim.command('call s:clear_match("semantic")')
        g_tu[1] = 0

    """ Do declaring highlighting'
    """
    if def_cursor is not None and tu.get_file(def_cursor.location.file.name) is not None:
        if def_cursor.kind.is_declaration():
            vim_match_add('cursor_def_ref', 'CursorDeclRef', def_cursor.location.line, def_cursor.location.column, len(def_cursor.spelling), -1)
        if def_cursor.kind.is_preprocessing():
            t = def_cursor.get_tokens().next()
            vim_match_add('cursor_def_ref', 'CursorDeclRef', t.location.line, t.location.column, len(t.spelling), -1)

    
    #print decl_ref_cursor.kind

    for t in window_tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value == 2:
            t_tu_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(tu, curr_file, t.location.line, t.location.column))

            if resemantic:
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
