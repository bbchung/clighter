python << endpython
import vim
import sys
import clang.cindex
from threading import Thread

gTranslationUnit = [None, 0]

gWindow=[]
if vim.eval("g:clighter_libclang_file") != "":
    clang.cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))

def start_parsing():
    t = Thread(target=do_parsing, args=(vim.eval('g:clighter_clang_options'),))
    t.start()

def do_parsing(options):
    global gTranslationUnit

    try:
        idx = clang.cindex.Index.create()
    except:
        vim.command('echohl WarningMsg | echomsg "Clighter runtime error: libclang error" | echohl None')
        return

    gTranslationUnit[0] = idx.parse(vim.current.buffer.name, options, [(vim.current.buffer.name, "\n".join(vim.current.buffer))], options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    gTranslationUnit[1] = 1

def vim_matchpos(t, group):
	vim.command("call add(w:matched_list, matchaddpos('{0}', [[{1}, {2}, {3}], -1]))".format(group, t.location.line, t.location.column, len(t.spelling)));
    #vim.command("call add(w:matched_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));


def try_highlighting():
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
        vim_hl_tokens(gTranslationUnit[0].cursor.get_tokens())
    else:
        gWindow = [max(w_top - 100 * window_size, 1), min(w_bottom + 100 * window_size, b_bottom)]
        file = clang.cindex.File.from_name(gTranslationUnit[0], vim.current.buffer.name)
        top = clang.cindex.SourceLocation.from_position(gTranslationUnit[0], file, gWindow[0], 1)
        bottom = clang.cindex.SourceLocation.from_position(gTranslationUnit[0], file, gWindow[1], 1)
        range = clang.cindex.SourceRange.from_locations(top, bottom)
        vim_hl_tokens(gTranslationUnit[0].get_tokens(extent=range))


def vim_hl_tokens(tokens):
    first = 0
    for t in tokens:
        if first == 0:
            vim.command('call s:clear_match()')
            first = 1

        if t.kind.value == 2:
            if t.cursor.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
                vim_matchpos(t, 'MacroInstantiation')
            elif t.cursor.kind == clang.cindex.CursorKind.STRUCT_DECL:
                vim_matchpos(t, 'StructDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.CLASS_DECL:
                vim_matchpos(t, 'ClassDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.ENUM_DECL:
                vim_matchpos(t, 'EnumDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                vim_matchpos(t, 'EnumConstantDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.TYPE_REF:
                vim_matchpos(t, 'TypeRef')
            elif t.cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
                vim_matchpos(t, 'DeclRefExpr')
endpython


fun! clighter#ToggleCursorHL()
    if exists('s:cursor_highlight_on') && s:cursor_highlight_on==1
        match none
        au! CursorHighlight
        let s:cursor_highlight_on=0
    else
        augroup CursorHighlight
            au CursorHold * exe printf('match IncSearch /\V\<%s\>/', escape(expand('<cword>'), '/\'))
            au CursorMoved * match none
            "au CursorHold * let @/ = '\V\<'.escape(expand('<cword>'), '\').'\>'
        augroup END
        let s:cursor_highlight_on=1
    endif
endf

fun! s:start_parsing()
python << endpython
start_parsing()
endpython
endf

fun! s:clear_match()
    if !exists('w:matched_list')
        return
    endif

	for i in w:matched_list
		call matchdelete(i)
	endfor
	let w:matched_list=[]
endf

fun! s:highlighting()
if !exists('w:matched_list')
    let w:matched_list = []
endif
python << endpython
try_highlighting()
endpython
endf

fun! clighter#Enable()
    augroup ClighterEnable
        au!
        au BufEnter *.[ch],*.[ch]pp,*.m call s:start_parsing()
        au CursorHold *.[ch],*.[ch]pp,*.m call s:start_parsing()
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m call s:highlighting()
        else
            au CursorHold *.[ch],*.[ch]pp,*.m call s:highlighting()
        endif
    augroup END

    call s:start_parsing()
endf

fun! clighter#Disable()
    au! ClighterEnable
    call s:clear_match()
endf

augroup ClighterEnable
