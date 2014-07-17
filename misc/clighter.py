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


def try_highlight(vim_cursor_line, vim_cursor_col):
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
    file = cindex.File.from_name(gTranslationUnit[0], vim.current.buffer.name)

    if (window_size < 0):
        gWindow = []
        window_tokens = gTranslationUnit[0].cursor.get_tokens()
    else:
        gWindow = [max(w_top - 100 * window_size, 1), min(w_bottom + 100 * window_size, b_bottom)]
        top = cindex.SourceLocation.from_position(gTranslationUnit[0], file, gWindow[0], 1)
        bottom = cindex.SourceLocation.from_position(gTranslationUnit[0], file, gWindow[1], 1)
        range = cindex.SourceRange.from_locations(top, bottom)
        window_tokens = gTranslationUnit[0].get_tokens(extent=range)

    decl_ref_cursor = None
    if int(vim.eval("s:cursor_decl_ref_hl_on")) == 1:
        decl_ref_cursor = cindex.Cursor.from_location(gTranslationUnit[0], cindex.SourceLocation.from_position(gTranslationUnit[0], file, vim_cursor_line, vim_cursor_col)) # cusor under vim-cursor

    do_highlight(window_tokens, decl_ref_cursor)


def do_highlight(window_tokens, decl_ref_cursor):
    vim.command('call s:clear_match("cursor_decl_ref")')
    ref_spelling = None
    
    if decl_ref_cursor is not None:
        if decl_ref_cursor.kind == cindex.CursorKind.DECL_REF_EXPR or decl_ref_cursor.kind == cindex.CursorKind.MEMBER_REF_EXPR:
            for t in decl_ref_cursor.get_tokens():
                if t.kind.value == 2:
                    ref_spelling = t.spelling

    need_clear_semantic = 1
    for t in window_tokens:
        """ Do semantic highlighting'
        """
        if need_clear_semantic == 1:
            vim.command('call s:clear_match("semantic")')
            need_clear_semantic = 0
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
                is_call = 0
                try:
                    if window_tokens.next().cursor.kind == cindex.CursorKind.CALL_EXPR:
                        is_call = 1
                except:
                    pass
                    
                if is_call == 0:
                    vim_match_add('semantic', 'DeclRefExpr', t.location.line, t.location.column, len(t.spelling))

            """ Do reference highlighting'
            """
            if ref_spelling is not None and t.spelling == ref_spelling and (t.cursor.kind == cindex.CursorKind.DECL_REF_EXPR or t.cursor.kind == cindex.CursorKind.MEMBER_REF_EXPR):
                vim_match_add('cursor_decl_ref', 'CursorDeclRef', t.location.line, t.location.column, len(t.spelling))

    """ Do declaring highlighting'
    """
    if decl_ref_cursor is not None:
        def_cursor = decl_ref_cursor.get_definition()
        if def_cursor is not None:
            vim_match_add('cursor_decl_ref', 'CursorDeclRef', def_cursor.location.line, def_cursor.location.column, len(def_cursor.spelling))
    

def vim_match_add(type, group, line, col, len):
    vim.command("call add(w:highlight_dict['{0}'], matchaddpos('{1}', [[{2}, {3}, {4}]], -1))".format(type, group, line, col, len))
    # vim.command("call add(w:semantic_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));
