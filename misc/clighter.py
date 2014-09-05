import vim
from clang import cindex
from threading import Thread
import time

if vim.vars['clighter_libclang_file']:
    cindex.Config.set_library_file(vim.vars['clighter_libclang_file'])


class ParsingObject:

    def __init__(self, idx, bufname):
        self.__clang_idx = idx
        self.__bufname = bufname
        self.tu = None
        self.file = None
        self.drawn = False
        self.invalid = True

    def try_parse(self, args, unsaved, force=False):
        if not self.invalid and not force:
            return

        try:
            self.tu = self.__clang_idx.parse(
                self.__bufname, args, unsaved, options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
            self.file = self.tu.get_file(self.__bufname)
        except:
            pass

        self.invalid = False
        self.drawn = False


class ParsingService:
    __thread = None
    __is_running = False
    unsaved = set()
    objects = {}
    clang_idx = cindex.Index.create()

    @staticmethod
    def start_sched_looping():
        if ParsingService.__thread is not None:
            return

        ParsingService.__is_running = True
        ParsingService.__thread = Thread(
            target=ParsingService.__parsing_worker, args=[vim.vars['clighter_clang_options']])
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
        while ParsingService.__is_running:
            try:
                for pobj in ParsingService.objects.values():
                    pobj.try_parse(args, ParsingService.unsaved)
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
        ParsingService.unsaved.clear()
        for buf in vim.buffers:
            if buf.options['filetype'] not in ["c", "cpp", "objc"] or ((len(buf) == 1 and not buf[0])):
                continue

            ParsingService.unsaved.add((buf.name, '\n'.join(buf)))


def on_vim_cursor_hold():
    ParsingService.invalidate_current_pobj()
    ParsingService.update_unsaved()


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


def highlight_window():
    pobj = ParsingService.objects.get(vim.current.buffer.number)
    if pobj is None or pobj.tu is None:
        return

    vim_win_top = vim.bindeval("line('w0')")
    vim_win_bottom = vim.bindeval("line('w$')")

    clighter_window = vim.current.window.vars.get("clighter_window")
    in_window = clighter_window is not None and vim_win_top >= clighter_window[
        0] and vim_win_bottom <= clighter_window[1]

    def_cursor = None
    redraw_def_ref = False

    if vim.bindeval("s:cursor_decl_ref_hl_on") == 1:
        vim_cursor = __get_vim_cursor(pobj, vim.current.window.cursor)
        def_cursor = __get_definition(vim_cursor)

        if not hasattr(highlight_window, 'last_dc'):
            highlight_window.last_dc = None

        if highlight_window.last_dc is not None and (def_cursor is None or highlight_window.last_dc != def_cursor):
            vim.command("call s:clear_match(['CursorDefRef'])")
            highlight_window.last_dc = None

        if def_cursor is not None and (highlight_window.last_dc is None or def_cursor != highlight_window.last_dc):
            redraw_def_ref = True

            # special case for preprocessor
            if def_cursor.kind.is_preprocessing() and def_cursor.location.file.name == vim.current.buffer.name:
                __vim_matchaddpos('CursorDefRef', def_cursor.location.line, def_cursor.location.column, len(
                    __get_spelling_or_displayname(def_cursor)), -1)

            highlight_window.last_dc = def_cursor

    window_size = vim.vars['clighter_window_size'] * 100
    buflinenr = len(vim.current.buffer)
    target_window = [1, buflinenr] if window_size < 0 else [
        max(vim_win_top - window_size, 1), min(vim_win_bottom + window_size, buflinenr)]

    if not in_window or not pobj.drawn:
        vim.current.window.vars["clighter_window"] = target_window
        vim.command(
            "call s:clear_match(['ClighterMacroInstantiation', 'ClighterStructDecl', 'ClighterClassDecl', 'ClighterEnumDecl', 'ClighterEnumConstantDecl', 'ClighterTypeRef', 'ClighterDeclRefExprEnum'])")

    if in_window and pobj.drawn and not redraw_def_ref:
        return

    tokens = pobj.tu.get_tokens(extent=cindex.SourceRange.from_locations(cindex.SourceLocation.from_position(
        pobj.tu, pobj.file, target_window[0], 1), cindex.SourceLocation.from_position(pobj.tu, pobj.file, target_window[1], 1)))

    for t in tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value != 2:
            continue

        t_cursor = t.cursor
        t_cursor._tu = pobj.tu  

        if not in_window or not pobj.drawn:
            __draw_token(t.location.line, t.location.column, len(t.spelling), t_cursor.kind, t_cursor.type.kind)

        """ Do definition/reference highlighting'
        """
        if not redraw_def_ref:
            continue

        t_def_cursor = __get_definition(t_cursor)
        if t_def_cursor is not None and t_def_cursor == def_cursor:
            __vim_matchaddpos(
                'CursorDefRef', t.location.line, t.location.column, len(t.spelling), -1)

    pobj.drawn = True


def refactor_rename():
    if vim.current.buffer.options['filetype'] not in ["c", "cpp", "objc"]:
        return

    pobj = ParsingService.objects.get(vim.current.buffer.number)
    if pobj is None:
        return

    ParsingService.update_unsaved()
    pobj.try_parse(
        vim.vars['clighter_clang_options'], ParsingService.unsaved, True)

    vim_cursor = __get_vim_cursor(pobj, vim.current.window.cursor)
    def_cursor = __get_definition(vim_cursor)
    if def_cursor is None:
        return

    if def_cursor.kind == cindex.CursorKind.CONSTRUCTOR or def_cursor.kind == cindex.CursorKind.DESTRUCTOR:
        def_cursor = def_cursor.semantic_parent

    old_name = __get_spelling_or_displayname(def_cursor)
    new_name = vim.bindeval(
        "input('rename \"{0}\" to: ', '{1}')".format(old_name, old_name))

    if not new_name or old_name == new_name:
        return

    locs = set()
    locs.add(
        (def_cursor.location.line, def_cursor.location.column, def_cursor.location.file.name))
    __search_ref_cursors(pobj.tu.cursor, def_cursor, locs)
    __vim_multi_replace(locs, old_name, new_name)

    if __is_symbol_cursor(def_cursor) and vim.vars['clighter_enable_cross_rename'] == 1:
        __cross_buffer_rename(def_cursor.get_usr(), new_name)


def __get_spelling_or_displayname(cursor):
    return cursor.spelling if cursor.spelling is not None else cursor.displayname


def __get_definition(cursor):
    if cursor is None:
        return None

    if cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
        return cursor

    return cursor.get_definition()


def __draw_token(line, col, len, kind, type):
    if kind == cindex.CursorKind.MACRO_INSTANTIATION:
        __vim_matchaddpos('ClighterMacroInstantiation', line, col, len, -2)
    elif kind == cindex.CursorKind.STRUCT_DECL:
        __vim_matchaddpos('ClighterStructDecl', line, col, len, -2)
    elif kind == cindex.CursorKind.CLASS_DECL:
        __vim_matchaddpos('ClighterClassDecl', line, col, len, -2)
    elif kind == cindex.CursorKind.ENUM_DECL:
        __vim_matchaddpos('ClighterEnumDecl', line, col, len, -2)
    elif kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
        __vim_matchaddpos('ClighterEnumConstantDecl', line, col, len, -2)
    elif kind == cindex.CursorKind.TYPE_REF:
        __vim_matchaddpos('ClighterTypeRef', line, col, len, -2)
    elif kind == cindex.CursorKind.DECL_REF_EXPR and type == cindex.TypeKind.ENUM:
        __vim_matchaddpos('ClighterDeclRefExprEnum', line, col, len, -2)


def __cross_buffer_rename(usr, new_name):
    call_bufnr = vim.current.buffer.number

    vim.command("bn!")
    while vim.current.buffer.number != call_bufnr:
        if vim.current.buffer.options['filetype'] in ["c", "cpp", "objc"]:
            pobj = ParsingService.objects.get(vim.current.buffer.number)
            if pobj is not None:
                pobj.try_parse(
                    vim.vars['clighter_clang_options'], ParsingService.unsaved, True)
                __search_usr_and_rename_refs(pobj.tu, usr, new_name)

        vim.command("bn!")


def __search_usr_and_rename_refs(tu, usr, new_name):
    if tu is None:
        return

    symbols = []
    __find_cursors_by_usr(tu.cursor, usr, symbols)

    if not symbols:
        return

    if vim.vars['clighter_rename_prompt_level'] >= 1:
        cmd = "let l:choice = confirm(\"found symbols in {0}, rename them?\", \"&Yes\n&No\", 1)".format(
            vim.current.buffer.name)
        vim.command(cmd)

        if vim.bindeval('l:choice') == 2:
            return

    # all symbols with the same name
    old_name = __get_spelling_or_displayname(symbols[0])

    locs = set()
    for sym in symbols:
        locs.add(
            (sym.location.line, sym.location.column, sym.location.file.name))
        __search_ref_cursors(tu.cursor, sym, locs)

    __vim_multi_replace(locs, old_name, new_name)

# def dfs(cursor):
#    print cursor.location, cursor.spelling
#    for c in cursor.get_children():
#        dfs(c)


def __find_cursors_by_usr(cursor, usr, symbols):
    if cursor.get_usr() == usr and cursor not in symbols:
        symbols.append(cursor)

    for c in cursor.get_children():
        __find_cursors_by_usr(c, usr, symbols)


def __search_ref_cursors(cursor, def_cursor, locs):
    cursor_def = __get_definition(cursor)

    if (cursor_def is not None and cursor_def == def_cursor) or ((cursor.kind == cindex.CursorKind.CONSTRUCTOR or cursor.kind == cindex.CursorKind.DESTRUCTOR) and cursor.semantic_parent == def_cursor):
        locs.add(
            (cursor.location.line, cursor.location.column, cursor.location.file.name))

    for c in cursor.get_children():
        __search_ref_cursors(c, def_cursor, locs)


def __is_symbol_cursor(cursor):
    return cursor.kind.is_preprocessing() or cursor.semantic_parent.kind != cindex.CursorKind.FUNCTION_DECL


def __get_vim_cursor(pobj, pos):
    (row, col) = pos
    cursor = cindex.Cursor.from_location(pobj.tu, cindex.SourceLocation.from_position(
        pobj.tu, pobj.file, row, col + 1))  # cursor under vim

    return cursor if cursor.location.column <= col + 1 < cursor.location.column + len(__get_spelling_or_displayname(cursor)) else None


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
