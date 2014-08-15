import os.path
import vim
from clang import cindex
from threading import Thread
import time
import threading

class ParsingService:
    thread = None
    is_running= 0
    instances={}
    clang_idx = cindex.Index.create()
    def __init__(self, bufnr, bufname):
        self.tu=None
        self.applied=1
        self.sched_time = time.time()
        self.bufnr = bufnr
        self.bufname = bufname
        self.lock = threading.Lock()

    @staticmethod
    def start_parsing_loop():
        ParsingService.is_running = 1
        ParsingService.thread = Thread(target=ParsingService.__parsing_worker, args=[vim.eval('g:clighter_clang_options')])
        ParsingService.thread.start()

    @staticmethod
    def stop_parsing_loop():
        ParsingService.is_running = 0
        ParsingService.thread.join()
        ParsingService.thread = None

    @staticmethod
    def __parsing_worker(args):
        while ParsingService.is_running == 1:
            try:
                for pobj in ParsingService.instances.values():
                    with pobj.lock:
                        if pobj.sched_time is not None and time.time() > pobj.sched_time:
                            if pobj.tu is None:
                                pobj.tu = ParsingService.clang_idx.parse(pobj.bufname, args, [(pobj.bufname, "\n".join(vim.buffers[pobj.bufnr]))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
                            else:
                                pobj.tu.reparse([(pobj.bufname, "\n".join(vim.buffers[pobj.bufnr]))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

                            pobj.applied = 0
                            pobj.sched_time = None
            finally:
                time.sleep(0.2)

    @staticmethod
    def join_all():
        for buf in vim.buffers:
            ext = os.path.splitext(buf.name)[1]
            if ext in ['.c', '.cpp', '.h', '.hpp', '.m']:
                ParsingService.instances[buf.number] = ParsingService(buf.number, buf.name) 

    @staticmethod
    def join():
        ft = vim.eval("&filetype") 
        if ft in ["c", "cpp", "objc"]:
            ParsingService.instances[vim.current.buffer.number] = ParsingService(vim.current.buffer.number, vim.current.buffer.name) 

    @staticmethod
    def reset_current_sched():
        pobj = ParsingService.instances.get(vim.current.buffer.number)
        if pobj is None:
            return

        with pobj.lock:
            pobj.sched_time = time.time() + 0.5




__window_size = int(vim.eval('g:clighter_window_size')) * 100

if vim.eval("g:clighter_libclang_file"):
    cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))

#def try_highlight2():
    #vim_win_top = int(vim.eval("line('w0')"))
    #vim_win_bottom = int(vim.eval("line('w$')"))
    #clighter_window = vim.current.window.vars["clighter_window"]

    #pobj = ParsingService.instances.get(vim.current.buffer.number)
    #if pobj is None:
        #return

    #with pobj.lock:
        #if pobj.tu is None:
            #return

        #file = pobj.tu.get_file(vim.current.buffer.name)
        #if file == None: # should not happened
            #return

        #dfs(pobj.tu.cursor, vim_win_top, vim_win_bottom)

#def bfs(c, top, bottom, queue):
    #if c.location.line >= top and c.location.line <= bottom:
        #draw_token(c)

    #queue.put(c.get_children())

    #while not queue.empty():
        #curs = queue.get()
        #for cur in curs:
            #if cur.location.line >= top and cur.location.line <= bottom:
                #draw_token(cur)

            #queue.put(cur.get_children())


#def dfs(cursor, top, bottom):
    #if cursor.location.line >= top and cursor.location.line <= bottom:
        #draw_token(cursor)

    #for c in cursor.get_children():
        #dfs(c, top, bottom)


def __try_highlight():
    global __window_size

    vim_win_top = int(vim.eval("line('w0')"))
    vim_win_bottom = int(vim.eval("line('w$')"))
    clighter_window = vim.current.window.vars["clighter_window"]

    pobj = ParsingService.instances.get(vim.current.buffer.number)
    if pobj is None:
        return

    with pobj.lock:
        if pobj.tu is None:
            return

        file = pobj.tu.get_file(vim.current.buffer.name)
        if file == None: # should not happened
            return

        need_update = vim_win_top < clighter_window[0] or vim_win_bottom > clighter_window[1] or pobj.applied == 0

        buflinenr = len(vim.current.buffer);
        if (__window_size < 0):
            vim.command("let w:clighter_window=[0, %d]" % buflinenr)
            window_tokens = pobj.tu.cursor.get_tokens()
        else:
            top_linenr = max(vim_win_top - __window_size, 1);
            bottom_linenr = min(vim_win_bottom + __window_size, buflinenr)
            vim.command("let w:clighter_window=[%d, %d]" %(top_linenr, bottom_linenr))
            range = cindex.SourceRange.from_locations(cindex.SourceLocation.from_position(pobj.tu, file, top_linenr, 1), cindex.SourceLocation.from_position(pobj.tu, file, bottom_linenr, 1))
            window_tokens = pobj.tu.get_tokens(extent=range)

        vim_cursor = None
        if int(vim.eval("s:cursor_decl_ref_hl_on")) == 1:
            (row, col) = vim.current.window.cursor
            vim_cursor = cindex.Cursor.from_location(pobj.tu, cindex.SourceLocation.from_position(pobj.tu, file, row, col + 1)) # cusor under vim-cursor

        def_cursor = None
        if vim_cursor is not None and get_spelling_or_displayname(vim_cursor) == vim.eval('expand("<cword>")'):
            def_cursor = get_definition_or_declaration(vim_cursor)

        __highlight_window(pobj.tu, window_tokens, def_cursor, file, need_update)


def __highlight_window(tu, window_tokens, def_cursor, file, need_update):
    vim.command("call s:clear_match(['CursorDefRef'])")
    if need_update:
        vim.command("call s:clear_match(['MacroInstantiation', 'StructDecl', 'ClassDecl', 'EnumDecl', 'EnumConstantDecl', 'TypeRef', 'EnumDeclRefExpr'])")
        ParsingService.instances[vim.current.buffer.number].applied = 1

    """ Do declaring highlighting'
    """

    if def_cursor is not None and def_cursor.location.file.name == file.name and def_cursor.kind.is_preprocessing():
        __vim_matchaddpos('CursorDefRef', def_cursor.location.line, def_cursor.location.column, len(get_spelling_or_displayname(def_cursor)), -1)

    
    #print decl_ref_cursor.kind

    for t in window_tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value == 2:
            t_tu_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(tu, file, t.location.line, t.location.column))

            if need_update:
                draw_token(t_tu_cursor.kind, t_tu_cursor.type.kind, t)

            """ Do definition/reference highlighting'
            """
            if def_cursor is not None and def_cursor.location.file.name == file.name:
                t_def_cursor = get_definition_or_declaration(t_tu_cursor)
                if t_def_cursor is not None and t_def_cursor == def_cursor and t.spelling == get_spelling_or_displayname(def_cursor):
                    __vim_matchaddpos('CursorDefRef', t.location.line, t.location.column, len(t.spelling), -1)


def get_spelling_or_displayname(cursor):
    if cursor.spelling is not None:
        return cursor.spelling

    return cursor.displayname


def get_definition_or_declaration(cursor):
    if cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
        return cursor

    definition = cursor.get_definition()
    if definition is not None:
        return definition

    return cursor.referenced

def draw_token(kind, type, token):
    if kind == cindex.CursorKind.MACRO_INSTANTIATION:
        __vim_matchaddpos('MacroInstantiation', token.location.line, token.location.column, len(token.spelling), -2)
    elif kind == cindex.CursorKind.STRUCT_DECL:
        __vim_matchaddpos('StructDecl', token.location.line, token.location.column, len(token.spelling), -2)
    elif kind == cindex.CursorKind.CLASS_DECL:
        __vim_matchaddpos('ClassDecl', token.location.line, token.location.column, len(token.spelling), -2)
    elif kind == cindex.CursorKind.ENUM_DECL:
        __vim_matchaddpos('EnumDecl', token.location.line, token.location.column, len(token.spelling), -2)
    elif kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
        __vim_matchaddpos('EnumConstantDecl', token.location.line, token.location.column, len(token.spelling), -2)
    elif kind == cindex.CursorKind.TYPE_REF:
        __vim_matchaddpos('TypeRef', token.location.line, token.location.column, len(token.spelling), -2)
    elif kind == cindex.CursorKind.DECL_REF_EXPR and type == cindex.TypeKind.ENUM:
        __vim_matchaddpos('EnumDeclRefExpr', token.location.line, token.location.column, len(token.spelling), -2)


def rename():
    tu = ParsingService.clang_idx.parse(vim.current.buffer.name, vim.eval('g:clighter_clang_options'), [(vim.current.buffer.name, "\n".join(vim.buffers[vim.current.buffer.number]))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    file = cindex.File.from_name(tu, vim.current.buffer.name)
    (row, col) = vim.current.window.cursor
    vim_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(tu, file, row, col + 1)) # cusor under vim-cursor
    locs = []

    def_cur = get_definition_or_declaration(vim_cursor)
    if def_cur is None or def_cur.location.file.name != file.name:
        return


    vim.command("let a:new_name = input(\'rename \'.expand(\'<cword>\').' to: ')")
    
    if not vim.eval("a:new_name"):
        return

    if def_cur.kind.is_preprocessing():
        locs.append(def_cur.location)

    __dfs(tu.cursor, locs, def_cur)

    vim_replace(locs, get_spelling_or_displayname(def_cur), vim.eval("a:new_name"))


def __dfs(cursor, locs, def_cur):
    if get_definition_or_declaration(cursor) is not None and get_definition_or_declaration(cursor) == def_cur:
        locs.append(cursor.location)

    for c in cursor.get_children():
        __dfs(c, locs, def_cur)


def vim_replace(locs, old, new):
    pattern = ""

    for loc in locs:
        if pattern:
            pattern += "\|"

        pattern += "\%" + str(loc.line) + "l" + "\%>" + str(loc.column - 1) + "v\%<" + str(loc.column + len(old) + 1) + "v" + old 

    cmd = ":%s/" + pattern + "/" + new + "/gI"

    vim.command(cmd)


def __vim_matchaddpos(group, line, col, len, priority):
    vim.command("call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})".format(group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));
