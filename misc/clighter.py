import os.path
import vim
from clang import cindex
from threading import Thread
import time

class ParsingObject:
    thread = None
    run= 0
    dict={}
    idx = cindex.Index.create()
    def __init__(self, buf, bufnr, bufname):
        self.tu=None
        self.applied=1
        self.timeup = time.time()
        self.bufnr = bufnr
        self.bufname = bufname
        self.buf = buf

window_size = int(vim.eval('g:clighter_window_size')) * 100

g_libclang_file = vim.eval("g:clighter_libclang_file")
if g_libclang_file:
    cindex.Config.set_library_file(g_libclang_file)


def join_parsing_loop_all():
    for buf in vim.buffers:
        ext = os.path.splitext(buf.name)[1]
        if ext in ['.c', '.cpp', '.h', '.hpp', '.m']:
            ParsingObject.dict[buf.number] = ParsingObject(buf, buf.number, buf.name) 


def join_parsing_loop():
    ft = vim.eval("&filetype") 
    if ft in ["c", "cpp", "objc"]:
        ParsingObject.dict[vim.current.buffer.number] = ParsingObject(vim.current.buffer, vim.current.buffer.number, vim.current.buffer.name) 


def start_parsing_loop():
    if ParsingObject.thread is not None:
        return

    ParsingObject.run = 1
    ParsingObject.thread = Thread(target=parsing_worker, args=[vim.eval('g:clighter_clang_options')])
    ParsingObject.thread.start()


def stop_parsing_loop():
    if ParsingObject.thread is None:
        return

    ParsingObject.run = 0
    ParsingObject.thread.join()
    ParsingObject.thread = None
    

def reset_timer():
    pobj = ParsingObject.dict.get(vim.current.buffer.number)
    if pobj is None:
        return

    pobj.timeup = time.time() + 0.5
    pobj.buf = vim.current.buffer


def parsing_worker(args):
    while ParsingObject.run == 1:
        try:
            for pobj in ParsingObject.dict.values():
                if pobj.timeup is not None and time.time() > pobj.timeup:
                    if pobj.tu is None:
                        pobj.tu = ParsingObject.idx.parse(pobj.bufname, args, [(pobj.bufname, "\n".join(pobj.buf))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
                    else:
                        pobj.tu.reparse([(pobj.bufname, "\n".join(pobj.buf))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

                    pobj.applied = 0
                    pobj.timeup = None
        finally:
            time.sleep(0.2)


def try_highlight():
    global window_size
    pobj = ParsingObject.dict.get(vim.current.buffer.number)

    if pobj is None or pobj.tu is None:
        return

    file = pobj.tu.get_file(vim.current.buffer.name)
    if file == None: # should not happened
        return

    w_top = int(vim.eval("line('w0')"))
    w_bottom = int(vim.eval("line('w$')"))
    window = vim.current.window.vars["window"]

    resemantic = w_top < window[0] or w_bottom > window[1] or ParsingObject.dict[vim.current.buffer.number].applied == 0

    buflinenr = len(vim.current.buffer);
    if (window_size < 0):
        vim.command("let w:window=[0, %d]" % buflinenr)
        window_tokens = pobj.tu.cursor.get_tokens()
    else:
        top_line = max(w_top - window_size, 1);
        bottom_line = min(w_bottom + window_size, buflinenr)
        vim.command("let w:window=[%d, %d]" %(top_line, bottom_line))
        top = cindex.SourceLocation.from_position(pobj.tu, file, top_line, 1)
        bottom = cindex.SourceLocation.from_position(pobj.tu, file, bottom_line, 1)
        range = cindex.SourceRange.from_locations(top, bottom)
        window_tokens = pobj.tu.get_tokens(extent=range)

    vim_cursor = None
    if int(vim.eval("s:cursor_decl_ref_hl_on")) == 1:
        (row, col) = vim.current.window.cursor
        vim_cursor = cindex.Cursor.from_location(pobj.tu, cindex.SourceLocation.from_position(pobj.tu, file, row, col + 1)) # cusor under vim-cursor

    def_cursor = None
    if vim_cursor is not None:
        if vim_cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
            def_cursor = vim_cursor
        else:
            def_cursor = vim_cursor.get_definition()

    show_def_ref = def_cursor is not None and def_cursor.location.file.name == file.name

    highlight_window(pobj.tu, window_tokens, def_cursor, file, resemantic, show_def_ref)


def highlight_window(tu, window_tokens, def_cursor, curr_file, resemantic, show_def_ref):
    vim.command("call s:clear_match(['CursorDefRef'])")
    if resemantic:
        vim.command("call s:clear_match(['MacroInstantiation', 'StructDecl', 'ClassDecl', 'EnumDecl', 'EnumConstantDecl', 'TypeRef', 'EnumDeclRefExpr'])")
        ParsingObject.dict[vim.current.buffer.number].applied = 1

    """ Do declaring highlighting'
    """

    if show_def_ref == 1 and def_cursor.kind.is_preprocessing():
        vim_match_add('CursorDefRef', def_cursor.location.line, def_cursor.location.column, len(def_cursor.displayname), -1)

    
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

            """ Do definition/reference highlighting'
            """
            if show_def_ref:
                t_def_cursor = t_tu_cursor.get_definition()
                if t_def_cursor is not None and t_def_cursor == def_cursor:
                    vim_match_add('CursorDefRef', t.location.line, t.location.column, len(t.spelling), -1)


def vim_match_add(group, line, col, len, priority):
    vim.command("call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})".format(group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));
