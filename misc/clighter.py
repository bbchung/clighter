import vim
from clang import cindex
from threading import Thread
import time

if vim.eval("g:clighter_libclang_file"):
    cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))


class ParsingObject:

    def __init__(self, idx, bufname):
        self.__clang_idx = idx
        self.__bufname = bufname
        self.unsaved = None
        self.tu = None
        self.file = None
        self.drawn = False
        self.invalid = True

    def parse(self, args, unsaved=None):
        if unsaved is not None:
            self.unsaved = unsaved

        if self.invalid == False:
            return

        try:
            self.tu = self.__clang_idx.parse(
                self.__bufname, args, self.unsaved, options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
            self.file = self.tu.get_file(self.__bufname)
        except:
            pass

        self.invalid = False
        self.drawn = False


class ParsingService:
    __thread = None
    __is_running = False
    objects = {}
    clang_idx = cindex.Index.create()

    @staticmethod
    def start_sched_looping():
        if ParsingService.__thread is not None:
            return

        ParsingService.__is_running = True
        ParsingService.__thread = Thread(
            target=ParsingService.__parsing_worker, args=[vim.eval('g:clighter_clang_options')])
        ParsingService.__thread.start()

    @staticmethod
    def stop_sched_looping():
        if ParsingService.__thread is None:
            return

        ParsingService.__is_running = False
        ParsingService.__thread.join()
        ParsingService.__thread = None

    @staticmethod
    def __parsing_worker(args):
        while ParsingService.__is_running == True:
            try:
                for pobj in ParsingService.objects.values():
                    pobj.parse(args)
            finally:
                time.sleep(0.5)

    @staticmethod
    def join_all():
        for buf in vim.buffers:
            if buf.options['filetype'] in ["c", "cpp", "objc"] and buf.number not in ParsingService.objects.keys():
                ParsingService.objects[buf.number] = ParsingObject(
                    ParsingService.clang_idx, buf.name)

    @staticmethod
    def join():
        if vim.current.buffer.options['filetype'] in ["c", "cpp", "objc"] and vim.current.buffer.number not in ParsingService.objects.keys():
            ParsingService.objects[vim.current.buffer.number] = ParsingObject(
                ParsingService.clang_idx, vim.current.buffer.name)


    @staticmethod
    def invalidate_current_pobj():
        pobj = ParsingService.objects.get(vim.current.buffer.number)
        if pobj is not None:
            pobj.invalid = True
        

    @staticmethod
    def update_unsaved():
        pobj = ParsingService.objects.get(vim.current.buffer.number)
        if pobj is not None:
            pobj.invalid = True

        unsaved = get_unsaved_buffer_list()
        for pobj in ParsingService.objects.values():
            pobj.unsaved = unsaved


def on_vim_cursor_hold():
    ParsingService.invalidate_current_pobj()
    ParsingService.update_unsaved()



# def try_highlight2():
    # vim_win_top = int(vim.eval("line('w0')"))
    # vim_win_bottom = int(vim.eval("line('w$')"))
    # clighter_window = vim.current.window.vars["clighter_window"]

    # pobj = ParsingService.objects.get(vim.current.buffer.number)
    # if pobj is None:
        # return

    # with pobj.lock:
        # if pobj.tu is None:
            # return

        # file = pobj.tu.get_file(vim.current.buffer.name)
        # if file == None: # should not happened
            # return

        # dfs(pobj.tu.cursor, vim_win_top, vim_win_bottom)

# def bfs(c, top, bottom, queue):
    # if c.location.line >= top and c.location.line <= bottom:
        #__draw_token(c)

    # queue.put(c.get_children())

    # while not queue.empty():
        # curs = queue.get()
        # for cur in curs:
            # if cur.location.line >= top and cur.location.line <= bottom:
                #__draw_token(cur)

            # queue.put(cur.get_children())


# def dfs(cursor, top, bottom):
    # if cursor.location.line >= top and cursor.location.line <= bottom:
        #__draw_token(cursor)

    # for c in cursor.get_children():
        # dfs(c, top, bottom)


def highlight_window():
    window_size = int(vim.eval('g:clighter_window_size')) * 100
    vim_win_top = int(vim.eval("line('w0')"))
    vim_win_bottom = int(vim.eval("line('w$')"))

    pobj = ParsingService.objects.get(vim.current.buffer.number)
    if pobj is None or pobj.tu is None:
        return

    buflinenr = len(vim.current.buffer)
    target_window = [0, buflinenr] if window_size < 0 else [max(vim_win_top - window_size, 1), min(vim_win_bottom + window_size, buflinenr)]
    range = cindex.SourceRange.from_locations(cindex.SourceLocation.from_position(pobj.tu, pobj.file, target_window[0], 1), cindex.SourceLocation.from_position(pobj.tu, pobj.file, target_window[1], 1))
    tokens = pobj.tu.get_tokens(extent=range)

    clighter_window = vim.current.window.vars.get("clighter_window")
    in_window = clighter_window is not None and vim_win_top >= clighter_window[0] and vim_win_bottom <= clighter_window[1]

    vim_cursor = None
    if int(vim.eval("s:cursor_decl_ref_hl_on")) == 1:
        (row, col) = vim.current.window.cursor
        vim_cursor = cindex.Cursor.from_location( pobj.tu, cindex.SourceLocation.from_position(pobj.tu, pobj.file, row, col + 1))  # cursor under vim

    def_cursor = None
    if vim_cursor is not None:
        def_cursor = __get_definition_or_declaration(vim_cursor, True)

    vim.command("call s:clear_match(['CursorDefRef'])")

    if not in_window or not pobj.drawn:
        vim.current.window.vars["clighter_window"] = target_window
        vim.command( "call s:clear_match(['MacroInstantiation', 'StructDecl', 'ClassDecl', 'EnumDecl', 'EnumConstantDecl', 'TypeRef', 'EnumDeclRefExpr'])")

    if def_cursor is not None and def_cursor.location.file.name == vim.current.buffer.name and def_cursor.kind.is_preprocessing():
        __vim_matchaddpos('CursorDefRef', def_cursor.location.line, def_cursor.location.column, len(__get_spelling_or_displayname(def_cursor)), -1)

    for t in tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value == 2:
            t_tu_cursor = cindex.Cursor.from_location(
                pobj.tu, cindex.SourceLocation.from_position(pobj.tu, pobj.file, t.location.line, t.location.column))

            if not in_window or not pobj.drawn:
                __draw_token(t, t_tu_cursor.type.kind)

            """ Do definition/reference highlighting'
            """
            if def_cursor is not None and def_cursor.location.file.name == vim.current.buffer.name:
                t_def_cursor = __get_definition_or_declaration(
                    t_tu_cursor, False)
                if t_def_cursor is not None and t_def_cursor == def_cursor:
                    __vim_matchaddpos( 'CursorDefRef', t.location.line, t.location.column, len(t.spelling), -1)

    pobj.drawn = True


def __get_spelling_or_displayname(cursor):
    if cursor.spelling is not None:
        return cursor.spelling

    return cursor.displayname


def __get_definition_or_declaration(cursor, check_cword):
    if cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
        return cursor

    def_cursor = cursor.get_definition()
    if def_cursor is None:
        def_cursor = cursor.referenced

    if check_cword and def_cursor is not None and vim.eval('expand("<cword>")') != __get_spelling_or_displayname(def_cursor):
        def_cursor = None

    return def_cursor


def __draw_token(token, type):
    if token.cursor.kind == cindex.CursorKind.MACRO_INSTANTIATION:
        __vim_matchaddpos('MacroInstantiation', token.location.line,
                          token.location.column, len(token.spelling), -2)
    elif token.cursor.kind == cindex.CursorKind.STRUCT_DECL:
        __vim_matchaddpos('StructDecl', token.location.line,
                          token.location.column, len(token.spelling), -2)
    elif token.cursor.kind == cindex.CursorKind.CLASS_DECL:
        __vim_matchaddpos('ClassDecl', token.location.line,
                          token.location.column, len(token.spelling), -2)
    elif token.cursor.kind == cindex.CursorKind.ENUM_DECL:
        __vim_matchaddpos('EnumDecl', token.location.line,
                          token.location.column, len(token.spelling), -2)
    elif token.cursor.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
        __vim_matchaddpos('EnumConstantDecl', token.location.line,
                          token.location.column, len(token.spelling), -2)
    elif token.cursor.kind == cindex.CursorKind.TYPE_REF:
        __vim_matchaddpos('TypeRef', token.location.line,
                          token.location.column, len(token.spelling), -2)
    elif token.cursor.kind == cindex.CursorKind.DECL_REF_EXPR and type == cindex.TypeKind.ENUM:
        __vim_matchaddpos('EnumDeclRefExpr', token.location.line,
                          token.location.column, len(token.spelling), -2)


def cross_buffer_rename(usr, new_name, unsaved, caller):
    start_bufnr = vim.current.buffer.number
    while True:
        if vim.current.buffer.number != caller and vim.current.buffer.options['filetype'] in ["c", "cpp", "objc"]:
            pobj = ParsingService.objects.get(vim.current.buffer.number)
            if pobj is not None:
                pobj.parse(
                    vim.eval('g:clighter_clang_options'), unsaved)
                if pobj.tu is not None:
                    __search_and_rename(pobj.tu, usr, new_name)

        vim.command("bn!")
        if vim.current.buffer.number == start_bufnr:
            break


def get_unsaved_buffer_list():
    unsaved_list = set()
    for buf in vim.buffers:
        if buf.options['filetype'] not in ["c", "cpp", "objc"] or ((len(buf) == 1 and not buf[0])):
            continue

        unsaved_list.add((buf.name, "\n".join(buf)))

    return unsaved_list


def __search_and_rename(tu, usr, new_name):
    symbols = []
    __search_cursors_by_usr(tu.cursor, usr, symbols)

    if symbols and int(vim.eval('g:clighter_rename_prompt_level')) >= 1:
        cmd = "let l:choice = confirm(\"found symbols in {0}, rename them?\", \"&Yes\n&No\", 1)".format(
            vim.current.buffer.name)
        vim.command(cmd)

        if int(vim.eval("l:choice")) == 2:
            return

    for sym in symbols:
        locs = set()
        locs.add(
            (sym.location.line, sym.location.column, sym.location.file.name))

        __search_cursors_by_define(tu.cursor, sym, locs)
        __vim_replace(locs, __get_spelling_or_displayname(sym), new_name)

# def dfs(cursor):
#    print cursor.location, cursor.spelling
#    for c in cursor.get_children():
#        dfs(c)


def __search_cursors_by_usr(cursor, usr, symbols):
    if cursor.get_usr() == usr and cursor not in symbols:
        symbols.append(cursor)

    for c in cursor.get_children():
        __search_cursors_by_usr(c, usr, symbols)


def refactor_rename():
    if vim.current.buffer.options['filetype'] not in ["c", "cpp", "objc"]:
        return

    pobj = ParsingService.objects.get(vim.current.buffer.number)
    if pobj is None:
        return

    unsaved = get_unsaved_buffer_list()
    pobj.parse(vim.eval('g:clighter_clang_options'), unsaved)
    file = cindex.File.from_name(pobj.tu, vim.current.buffer.name)
    (row, col) = vim.current.window.cursor
    vim_cursor = cindex.Cursor.from_location(
        pobj.tu, cindex.SourceLocation.from_position(pobj.tu, file, row, col + 1))  # cursor under vim

    def_cursor = __get_definition_or_declaration(vim_cursor, True)
    if def_cursor is None:
        return

    if def_cursor.kind == cindex.CursorKind.CONSTRUCTOR:
        def_cursor = def_cursor.semantic_parent

    old_name = __get_spelling_or_displayname(def_cursor)
    vim.command(
        "let a:new_name = input('rename \"{0}\" to: ', '{1}')".format(old_name, old_name))

    new_name = vim.eval("a:new_name")
    if not new_name or old_name == new_name:
        return

    locs = set()
    locs.add(
        (def_cursor.location.line, def_cursor.location.column, def_cursor.location.file.name))
    __search_cursors_by_define(pobj.tu.cursor, def_cursor, locs)
    __vim_replace(locs, old_name, new_name)

    if __is_symbol_cursor(def_cursor) and int(vim.eval('g:clighter_enable_cross_rename')) == 1:
        cross_buffer_rename(
            def_cursor.get_usr(), new_name, unsaved, vim.current.buffer.number)


def __search_cursors_by_define(cursor, def_cursor, locs):
    cursor_def = __get_definition_or_declaration(cursor, False)

    if (cursor_def is not None and cursor_def == def_cursor) or (cursor.kind == cindex.CursorKind.CONSTRUCTOR and cursor.semantic_parent == def_cursor):
        locs.add(
            (cursor.location.line, cursor.location.column, cursor.location.file.name))

    for c in cursor.get_children():
        __search_cursors_by_define(c, def_cursor, locs)


def __is_symbol_cursor(cursor):
    return cursor.kind.is_preprocessing() or cursor.semantic_parent.kind != cindex.CursorKind.FUNCTION_DECL


def __vim_replace(locs, old, new):
    if not locs:
        return

    pattern = ""

    for line, column, file in locs:
        if file is None or file != vim.current.buffer.name:
            continue

        if pattern:
            pattern += "\|"

        pattern += "\%" + str(line) + "l" + "\%>" + str(
            column - 1) + "v\%<" + str(column + len(old)) + "v" + old

    if not pattern:
        return

    cmd = "%s/" + pattern + "/" + new + "/gI"

    if int(vim.eval('g:clighter_rename_prompt_level')) >= 2:
        cmd = cmd + "c"

    vim.command(cmd)


def __vim_matchaddpos(group, line, col, len, priority):
    vim.command("call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})".format(
        group, line, col, len, priority))
    # vim.command("call add(w:semantic_list, matchadd('{0}',
    # '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line,
    # t.location.column-1, t.location.column+len(t.spelling) + 1));
