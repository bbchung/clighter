from clang import cindex

def is_symbol_cursor(cursor):
    return cursor.kind.is_preprocessing() or cursor.semantic_parent.kind != cindex.CursorKind.FUNCTION_DECL


def find_cursors_by_usr(cursor, usr, result):
    if cursor.get_usr() == usr and cursor not in result:
        result.append(cursor)

    for c in cursor.get_children():
        find_cursors_by_usr(c, usr, result)


def get_definition(cursor):
    if cursor is None:
        return None

    if cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
        return cursor

    def_cur = cursor.get_definition()
    if def_cur is None:
        def_cur = cursor.referenced

    return def_cur


def get_spelling_or_displayname(cursor):
    return cursor.spelling if cursor.spelling is not None else cursor.displayname


def search_ref_cursors(cursor, def_cursor, locs):
    cursor_def = get_definition(cursor)

    if (cursor_def is not None and cursor_def == def_cursor) or ((cursor.kind == cindex.CursorKind.CONSTRUCTOR or cursor.kind == cindex.CursorKind.DESTRUCTOR) and cursor.semantic_parent == def_cursor):
        locs.add(
            (cursor.location.line, cursor.location.column, cursor.location.file.name))

    for c in cursor.get_children():
        search_ref_cursors(c, def_cursor, locs)

