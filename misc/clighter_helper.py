import vim
from clang import cindex


def get_vim_cursor_and_def(tu_ctx):
    vim_cursor = None
    def_cursor = None

    col = vim.current.window.cursor[1]
    if len(vim.current.line) > col:
        c = vim.current.line[col]
        if c.isalnum() or c == '_':
            vim_cursor = tu_ctx.get_cursor(vim.current.window.cursor)

            if vim_cursor is not None:
                def_cursor = get_semantic_definition(vim_cursor)

    if def_cursor is None:
        return None, None

    if vim.eval('expand("<cword>")') != def_cursor.spelling:
        return None, None

    return vim_cursor, def_cursor


def is_vim_buffer_allowed(buf):
    return buf.options['filetype'] in ["c", "cpp", "objc", "objcpp"]


def is_symbol_cursor(cursor):
    return cursor.kind.is_preprocessing() or cursor.semantic_parent.kind != cindex.CursorKind.FUNCTION_DECL


def find_cursors_by_usr(cursor, usr, result):
    if cursor.get_usr() == usr and cursor not in result:
        result.append(cursor)

    for c in cursor.get_children():
        find_cursors_by_usr(c, usr, result)


def get_semantic_definition(cursor):
    if cursor is None:
        return None

    if cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
        return cursor

    def_cur = cursor.get_definition()
    if def_cur is None:
        def_cur = cursor.referenced

    if def_cur is None:
        return None

    if def_cur.kind == cindex.CursorKind.CONSTRUCTOR or def_cur.kind == cindex.CursorKind.DESTRUCTOR:
        def_cur = def_cur.semantic_parent

    return def_cur


def get_spelling_or_displayname(cursor):
    return cursor.spelling if cursor.spelling is not None else cursor.displayname


def search_ref_tokens(tu, def_cursor, locs):
    tokens = tu.cursor.get_tokens()

    for t in tokens:
        if t.kind.value != 2:
            continue

        t_cursor = cindex.Cursor.from_location(tu, cindex.SourceLocation.from_position(
            tu, t.location.file, t.location.line, t.location.column))  # cursor under vim

        t_cursor_def = get_semantic_definition(t_cursor)

        if t_cursor_def is not None and t_cursor_def == def_cursor:
            locs.add(
                (t.location.line, t.location.column, t.location.file.name))
