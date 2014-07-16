import vim
from clang import cindex
from threading import Thread

gTranslationUnit = [None, 0]

gWindow = []
if vim.eval("g:clighter_libclang_file") != "":
    cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))

def start_parsing():
    t = Thread(target=do_parsing, args=(vim.eval('g:clighter_clang_options'),))
    t.start()


def do_parsing(options):
    global gTranslationUnit

    try:
        idx = cindex.Index.create()
    except:
        vim.command('echohl WarningMsg | echomsg "Clighter runtime error: libclang error" | echohl None')
        return

    gTranslationUnit[0] = idx.parse(vim.current.buffer.name, options, [(vim.current.buffer.name, "\n".join(vim.current.buffer))], options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    gTranslationUnit[1] = 1


def try_highlight_semantic():
    global gWindow
    global gTranslationUnit
    if gTranslationUnit[0] is None:
        return

    w_top = int(vim.eval("line('w0')"))
    w_bottom = int(vim.eval("line('w$')"))

    if gWindow != [] and w_top >= gWindow[0] and w_bottom <= gWindow[1] and gTranslationUnit[1] == 0:
        return

    gTranslationUnit[1] = 0
    b_bottom = int(vim.eval("line('$')"))
    window_size = int(vim.eval('g:clighter_window_size'))

    if (window_size < 0):
        gWindow = [1, b_bottom]
        hl_tokens(gTranslationUnit[0].cursor.get_tokens())
    else:
        gWindow = [max(w_top - 100 * window_size, 1), min(w_bottom + 100 * window_size, b_bottom)]
        file = cindex.File.from_name(gTranslationUnit[0], vim.current.buffer.name)
        top = cindex.SourceLocation.from_position(gTranslationUnit[0], file, gWindow[0], 1)
        bottom = cindex.SourceLocation.from_position(gTranslationUnit[0], file, gWindow[1], 1)
        range = cindex.SourceRange.from_locations(top, bottom)
        hl_tokens(gTranslationUnit[0].get_tokens(extent=range))


def try_match_def(line, col):
    global gTranslationUnit
    if gTranslationUnit[0] is None:
        return

    file = cindex.File.from_name(gTranslationUnit[0], vim.current.buffer.name)
    def_cursor = cindex.Cursor.from_location(gTranslationUnit[0], cindex.SourceLocation.from_position(gTranslationUnit[0], file, line, col)).get_definition()

    if def_cursor is None:
        return

    vim_match_add('def', 'Search', def_cursor.location.line, def_cursor.location.column, len(def_cursor.spelling))

def hl_tokens(tokens):
    first = 0
    for t in tokens:
        if first == 0:
            vim.command('call s:clear_match("semantic")')
            first = 1
        if t.kind.value == 2:
            if t.cursor.kind == cindex.CursorKind.MACRO_DEFINITION:
                vim_match_add('semantic', 'MacroInstantiation', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind == cindex.CursorKind.STRUCT_DECL:
                vim_match_add('semantic', 'StructDecl', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind == cindex.CursorKind.CLASS_DECL:
                vim_match_add('semantic', 'ClassDecl', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind == cindex.CursorKind.ENUM_DECL:
                vim_match_add('semantic', 'EnumDecl', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                vim_match_add('semantic', 'EnumConstantDecl', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind == cindex.CursorKind.TYPE_REF:
                vim_match_add('semantic', 'TypeRef', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind == cindex.CursorKind.DECL_REF_EXPR:
                vim_match_add('semantic', 'DeclRefExpr', t.location.line, t.location.column, len(t.spelling))
            elif t.cursor.kind.is_reference():
                vim_match_add('semantic', 'DeclRefExpr', t.location.line, t.location.column, len(t.spelling))


def vim_match_add(type, group, line, col, len):
    vim.command("call add(w:match_dict['{0}'], matchaddpos('{1}', [[{2}, {3}, {4}]], -1))".format(type, group, line, col, len))
    # vim.command("call add(w:semantic_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));


