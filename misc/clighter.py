import vim
from clang import cindex
from threading import Thread
import time

if vim.eval("g:clighter_libclang_file") != "":
    cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))

class Parsing:
    thread = None
    run= 0
    dict={}
    def __init__(self, bufnr, bufname):
        self.tu=None
        self.applied=1
        self.timeup = time.time()*1000.0
        self.bufnr = bufnr
        self.bufname = bufname


def join_parsing_loop():
    Parsing.dict[vim.current.buffer.number] = Parsing(vim.current.buffer.number, vim.current.buffer.name) 

def leave_parsing_loop():
    Parsing.dict.pop(vim.current.buffer.number, None)


def start_parsing_thread():
    if Parsing.thread is not None:
        return

    Parsing.run = 1
    Parsing.thread = Thread(target=parsing_worker, args=[vim.eval('g:clighter_clang_options')])
    Parsing.thread.start()

def stop_parsing_thread():
    if Parsing.thread is None:
        return

    Parsing.run = 0
    Parsing.thread.join()
    Parsing.thread = None
    

def reset_timeup():
    pobj = Parsing.dict.get(vim.current.buffer.number)
    if pobj is None:
        return

    pobj.timeup = time.time()*1000.0 + 500


def parsing_worker(option):
    while Parsing.run == 1:
        for d in Parsing.dict.values():
            if d.timeup != None and time.time() * 1000.0 > d.timeup:
                d.timeup = None
                do_parsing(d.bufnr, option)

        time.sleep (500.0 / 1000.0);


def do_parsing(bufnr, options):
    try:
        idx = cindex.Index.create()
    except:
        vim.command('echohl WarningMsg | echomsg "Clighter runtime error: libclang error" | echohl None')
        return

    Parsing.dict[bufnr].tu = idx.parse(Parsing.dict[bufnr].bufname, options, [(Parsing.dict[bufnr].bufname, "\n".join(vim.buffers[bufnr]))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    Parsing.dict[bufnr].applied = 0


def try_highlight():
    pobj = Parsing.dict.get(vim.current.buffer.number)
    if pobj is None:
        return

    curr_tu = pobj.tu
    if curr_tu is None:
        return

    file = curr_tu.get_file(vim.current.buffer.name)
    if file == None:
        return

    w_top = int(vim.eval("line('w0')"))
    w_bottom = int(vim.eval("line('w$')"))
    window = [int(vim.eval("w:window[0]")), int(vim.eval("w:window[1]"))]

    resemantic = w_top < window[0] or w_bottom > window[1] or Parsing.dict[vim.current.buffer.number].applied == 0

    window_size = int(vim.eval('g:clighter_window_size'))

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
    vim.command("call s:clear_match(%s)" % ['CursorDefRef'])
    if resemantic:
        vim.command("call s:clear_match(%s)" % ['MacroInstantiation', 'StructDecl', 'ClassDecl', 'EnumDecl', 'EnumConstantDecl', 'TypeRef', 'EnumDeclRefExpr'])
        Parsing.dict[vim.current.buffer.number].applied = 1

    """ Do declaring highlighting'
    """

    if def_cursor is not None and def_cursor.location.file == curr_file:
        if def_cursor.kind.is_declaration():
            vim_match_add('CursorDefRef', def_cursor.location.line, def_cursor.location.column, len(def_cursor.spelling), -1)
        if def_cursor.kind.is_preprocessing():
            t = def_cursor.get_tokens().next()
            vim_match_add('CursorDefRef', t.location.line, t.location.column, len(t.spelling), -1)

    
    #print decl_ref_cursor.kind

    for t in window_tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value == 2:
            t_tu_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(tu, curr_file, t.location.line, t.location.column))

            if resemantic:
                if t_tu_cursor.kind == cindex.CursorKind.MACRO_INSTANTIATION:
                    vim_match_add('MacroInstantiation', t.location.line, t.location.column, len(t.spelling), -2)
                elif t_tu_cursor.kind == cindex.CursorKind.STRUCT_DECL:
                    vim_match_add('StructDecl', t.location.line, t.location.column, len(t.spelling), -2)
                elif t_tu_cursor.kind == cindex.CursorKind.CLASS_DECL:
                    vim_match_add('ClassDecl', t.location.line, t.location.column, len(t.spelling), -2)
                elif t_tu_cursor.kind == cindex.CursorKind.ENUM_DECL:
                    vim_match_add('EnumDecl', t.location.line, t.location.column, len(t.spelling), -2)
                elif t_tu_cursor.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                    vim_match_add('EnumConstantDecl', t.location.line, t.location.column, len(t.spelling), -2)
                elif t_tu_cursor.kind == cindex.CursorKind.TYPE_REF:
                    vim_match_add('TypeRef', t.location.line, t.location.column, len(t.spelling), -2)
                elif t_tu_cursor.kind == cindex.CursorKind.DECL_REF_EXPR and t_tu_cursor.type.kind == cindex.TypeKind.ENUM:
                    vim_match_add('EnumDeclRefExpr', t.location.line, t.location.column, len(t.spelling), -2)

            """ Do reference highlighting'
            """
            if def_cursor is not None and def_cursor.location.file.name == curr_file.name:
                t_def_cursor = t_tu_cursor.get_definition()
                if t_def_cursor is not None and t_def_cursor == def_cursor:
                    vim_match_add('CursorDefRef', t.location.line, t.location.column, len(t.spelling), -1)


def vim_match_add(group, line, col, len, priority):
    vim.command("call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})".format(group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));
