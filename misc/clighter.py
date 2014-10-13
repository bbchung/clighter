import vim
from clang import cindex
import threading
import time

DEF_REF_PRI = -11
SYNTAX_PRI = -12

if vim.vars['clighter_libclang_file']:
    cindex.Config.set_library_file(vim.vars['clighter_libclang_file'])


class BufferCtx:

    def __init__(self, bufname):
        self.__bufname = bufname
        self.__tu = None

    def get_cursor(self, location):
        if self.__tu is None:
            return None

        (row, col) = location
        cursor = cindex.Cursor.from_location(self.__tu, cindex.SourceLocation.from_position(
            self.__tu, self.__tu.get_file(self.__bufname), row, col + 1))

        return cursor if cursor.location.line == row and cursor.location.column <= col + 1 < cursor.location.column + len(get_spelling_or_displayname(cursor)) else None

    def parse(self, idx, args, unsaved):
        self.__tu = idx.parse(
            self.__bufname, args, unsaved, options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

    @property
    def bufname(self):
        return self.__bufname

    @property
    def translation_unit(self):
        return self.__tu


class ClighterService:
    buf_ctxs = {}
    __thread = None
    __is_running = False

    # for internal use, to sync the parsing worker
    __change_tick = 1
    __parse_tick = 0

    __lock = threading.Lock()
    __unsaved = set()
    __idx = None

    @staticmethod
    def init():
        if ClighterService.__idx is None:
            try:
                ClighterService.__idx = cindex.Index.create()
            except:
                return

        for buf in vim.buffers:
            if buf.options['filetype'] in ["c", "cpp", "objc"] and buf.name not in ClighterService.buf_ctxs.keys():
                ClighterService.buf_ctxs[buf.name] = BufferCtx(buf.name)

        if ClighterService.__thread is None:
            ClighterService.__is_running = True
            ClighterService.__thread = threading.Thread(
                target=ClighterService.__parsing_worker, args=[list(vim.vars['clighter_clang_options'])])
            ClighterService.__thread.start()

        vim.command("let s:clang_initialized=1")

    @staticmethod
    def release():
        if ClighterService.__thread is not None:
            ClighterService.__is_running = False
            ClighterService.__thread.join()
            ClighterService.__thread = None

        if ClighterService.__idx is None:
            ClighterService.__idx = None

        vim.command("silent! unlet s:clang_initialized")

    @staticmethod
    def __parsing_worker(args):
        while ClighterService.__is_running:
            try:
                # has parse all unsaved files
                if ClighterService.__parse_tick == ClighterService.__change_tick:
                    continue

                last_change_tick = ClighterService.__change_tick

                for buf_ctx in ClighterService.buf_ctxs.values():
                    ClighterService.parse(buf_ctx, args)

                ClighterService.__parse_tick = last_change_tick
            except:
                pass
            finally:
                time.sleep(0.2)

    @staticmethod
    def add_vim_buffer():
        if vim.current.buffer.options['filetype'] not in ["c", "cpp", "objc"] or vim.current.buffer.name in ClighterService.buf_ctxs.keys():
            return

        ClighterService.buf_ctxs[vim.current.buffer.name] = BufferCtx(
            vim.current.buffer.name)

        ClighterService.__change_tick += 1

    @staticmethod
    def update_unsaved_all(increase_tick=True):
        ClighterService.__unsaved = set()

        for buf in vim.buffers:
            if buf.options['filetype'] not in ["c", "cpp", "objc"]:
                continue

            if len(buf) == 1 and buf[0] == "":
                continue

            ClighterService.__unsaved.add(
                (buf.name, '\n'.join(buf)))

        if increase_tick:
            ClighterService.__change_tick += 1

    @staticmethod
    def update_unsaved(increase_tick=True):
        for file in ClighterService.__unsaved:
            if file[0] == vim.current.buffer.name:
                ClighterService.__unsaved.discard(file)
                break

        ClighterService.__unsaved.add(
            (vim.current.buffer.name, '\n'.join(vim.current.buffer)))

        if increase_tick:
            ClighterService.__change_tick += 1

    @staticmethod
    def parse(buf_ctx, args):
        with ClighterService.__lock:
            buf_ctx.parse(
                ClighterService.__idx, args, ClighterService.__unsaved)

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


def unhighlight_window():
    vim.command(
        "call s:clear_match_pri([{0}, {1}])".format(DEF_REF_PRI, SYNTAX_PRI))
    highlight_window.syntaxed_window = None
    highlight_window.last_dc = None


def unhighlight_def_ref():
    vim.command("call s:clear_match_pri([{0}])".format(DEF_REF_PRI))
    highlight_window.last_dc = None


def highlight_window():
    buf_ctx = ClighterService.buf_ctxs.get(vim.current.buffer.name)
    if buf_ctx is None:
        return

    tu = buf_ctx.translation_unit
    if tu is None:
        return

    (top, bottom) = (vim.bindeval("line('w0')"), vim.bindeval("line('w$')"))

    draw_syntax = highlight_window.last_tu is None or highlight_window.last_tu != tu or highlight_window.syntaxed_window is None or highlight_window.syntaxed_window[
        0] != vim.current.window.number or top < highlight_window.syntaxed_window[1] or bottom > highlight_window.syntaxed_window[2]
    draw_def_ref = False

    def_cursor = None
    if vim.bindeval("s:cursor_decl_ref_hl_on") == 1:
        vim_cursor = buf_ctx.get_cursor(vim.current.window.cursor)
        def_cursor = __get_definition(vim_cursor)

        if highlight_window.last_dc is not None and (def_cursor is None or highlight_window.last_dc != def_cursor):
            unhighlight_def_ref()

        if def_cursor is not None and (highlight_window.last_dc is None or highlight_window.last_dc != def_cursor):
            draw_def_ref = True

            # special case for preprocessor
            if def_cursor.kind.is_preprocessing() and def_cursor.location.file.name == vim.current.buffer.name:
                __vim_matchaddpos('clighterCursorDefRef', def_cursor.location.line, def_cursor.location.column, len(
                    get_spelling_or_displayname(def_cursor)), DEF_REF_PRI)

            highlight_window.last_dc = def_cursor

    if not draw_syntax and not draw_def_ref:
        return

    window_size = vim.vars['clighter_window_size'] * 100
    buflinenr = len(vim.current.buffer)
    target_window = [vim.current.window.number, 1, buflinenr] if window_size < 0 else [
        vim.current.window.number, max(top - window_size, 1), min(bottom + window_size, buflinenr)]

    if draw_syntax:
        highlight_window.syntaxed_window = target_window
        vim.command("call s:clear_match_pri([{0}])".format(SYNTAX_PRI))

    file = tu.get_file(buf_ctx.bufname)
    tokens = tu.get_tokens(extent=cindex.SourceRange.from_locations(cindex.SourceLocation.from_position(
        tu, file, target_window[1], 1), cindex.SourceLocation.from_position(tu, file, target_window[2], 1)))

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
            highlight_window.last_tu = tu

        """ Do definition/reference highlighting'
        """
        if draw_def_ref:
            t_def_cursor = __get_definition(t_cursor)
            if t_def_cursor is not None and t_def_cursor == def_cursor:
                __vim_matchaddpos(
                    'clighterCursorDefRef', t.location.line, t.location.column, len(t.spelling), DEF_REF_PRI)


highlight_window.last_dc = None
highlight_window.last_tu = None
highlight_window.syntaxed_window = None


def refactor_rename():
    if vim.current.buffer.options['filetype'] not in ["c", "cpp", "objc"]:
        return

    buf_ctx = ClighterService.buf_ctxs.get(vim.current.buffer.name)
    if buf_ctx is None:
        return

    ClighterService.update_unsaved_all(False)
    try:
        ClighterService.parse(buf_ctx, vim.vars['clighter_clang_options'])
    except:
        return

    vim_cursor = buf_ctx.get_cursor(vim.current.window.cursor)
    def_cursor = __get_definition(vim_cursor)
    if def_cursor is None:
        return

    if def_cursor.kind == cindex.CursorKind.CONSTRUCTOR or def_cursor.kind == cindex.CursorKind.DESTRUCTOR:
        def_cursor = def_cursor.semantic_parent

    old_name = get_spelling_or_displayname(def_cursor)
    new_name = vim.bindeval(
        "input('rename \"{0}\" to: ', '{1}')".format(old_name, old_name))

    if not new_name or old_name == new_name:
        return

    pos = vim.current.window.cursor

    locs = set()
    locs.add((def_cursor.location.line, def_cursor.location.column,
              def_cursor.location.file.name))
    __search_ref_cursors(buf_ctx.translation_unit.cursor, def_cursor, locs)
    __vim_multi_replace(locs, old_name, new_name)

    if __is_symbol_cursor(def_cursor) and vim.vars['clighter_enable_cross_rename'] == 1:
        __cross_buffer_rename(def_cursor.get_usr(), new_name)

    vim.current.window.cursor = pos

    ClighterService.update_unsaved_all()


def get_spelling_or_displayname(cursor):
    return cursor.spelling if cursor.spelling is not None else cursor.displayname


def __get_definition(cursor):
    if cursor is None:
        return None

    return cursor if cursor.kind == cindex.CursorKind.MACRO_DEFINITION else cursor.referenced


def __draw_token(line, col, len, kind, type):
    if kind == cindex.CursorKind.MACRO_INSTANTIATION:
        __vim_matchaddpos(
            'clighterMacroInstantiation', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.STRUCT_DECL:
        __vim_matchaddpos('clighterStructDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.CLASS_DECL:
        __vim_matchaddpos('clighterClassDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.ENUM_DECL:
        __vim_matchaddpos('clighterEnumDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
        __vim_matchaddpos(
            'clighterEnumConstantDecl', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.TYPE_REF:
        __vim_matchaddpos('clighterTypeRef', line, col, len, SYNTAX_PRI)
    elif kind == cindex.CursorKind.DECL_REF_EXPR and type == cindex.TypeKind.ENUM:
        __vim_matchaddpos(
            'clighterDeclRefExprEnum', line, col, len, SYNTAX_PRI)


def __cross_buffer_rename(usr, new_name):
    call_bufnr = vim.current.buffer.number

    vim.command("bn!")
    while vim.current.buffer.number != call_bufnr:
        if vim.current.buffer.options['filetype'] in ["c", "cpp", "objc"]:
            buf_ctx = ClighterService.buf_ctxs.get(vim.current.buffer.name)
            if buf_ctx is not None:
                try:
                    ClighterService.parse(
                        buf_ctx, vim.vars['clighter_clang_options'])
                    __search_usr_and_rename_refs(
                        buf_ctx.translation_unit, usr, new_name)
                except:
                    pass

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
    old_name = get_spelling_or_displayname(symbols[0])

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
