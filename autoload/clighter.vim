python << endpython
import vim
import sys
import clang.cindex
from threading import Thread

gTu=None # global translation unit
if vim.eval("g:clighter_libclang_file") != "":
    clang.cindex.Config.set_library_file(vim.eval("g:clighter_libclang_file"))

def start_parsing():
    t = Thread(target=do_parsing, args=(vim.eval('g:clighter_clang_options'),))
    t.start()

def do_parsing(options):
    global gTu

    try:
        idx = clang.cindex.Index.create()
    except:
        vim.command('echohl WarningMsg | echomsg "Clighter runtime error: libclang error" | echohl None')
        return

    gTu = idx.parse(vim.current.buffer.name, options, [(vim.current.buffer.name, "\n".join(vim.current.buffer))], options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

def vim_matchadd(t, group):
	vim.command("call add(w:matched_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format(group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));

def try_highlighting():
    global gTu
    if gTu == None:
        return

    window_size =  int(vim.eval('g:clighter_window_size'))
    if (window_size < 0):
        vim_hl_tokens(gTu.cursor.get_tokens())
    else:
        file = clang.cindex.File.from_name(gTu, vim.current.buffer.name)
        top = clang.cindex.SourceLocation.from_position(gTu, file, max(int(vim.eval("line('w0')")) - 30 * window_size, 1), 1)
        bottom = clang.cindex.SourceLocation.from_position(gTu, file, min(int(vim.eval("line('w$')")) + 30 * window_size, int(vim.eval("line('$')"))), 1)
        range = clang.cindex.SourceRange.from_locations(top, bottom)
        vim_by_tokens(gTu.get_tokens(extent=range))

def vim_by_tokens(tokens):
    first = 0
    for t in tokens:
        if first == 0:
            vim.command('call s:clear_match()')
            first = 1

        if t.kind.value == 2:
            if t.cursor.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
                vim_matchadd(t, 'MacroInstantiation')
            elif t.cursor.kind == clang.cindex.CursorKind.STRUCT_DECL:
                vim_matchadd(t, 'StructDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.CLASS_DECL:
                vim_matchadd(t, 'ClassDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.ENUM_DECL:
                vim_matchadd(t, 'EnumDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                vim_matchadd(t, 'EnumConstantDecl')
            elif t.cursor.kind == clang.cindex.CursorKind.TYPE_REF:
                vim_matchadd(t, 'TypeRef')
            elif t.cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
                vim_matchadd(t, 'DeclRefExpr')
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
        au BufEnter *.[ch],*.[ch]pp,*.objc call s:start_parsing()
        au CursorHold *.[ch],*.[ch]pp,*.objc call s:highlighting()
        au CursorHold *.[ch],*.[ch]pp,*.objc call s:start_parsing()
    augroup END
endf

fun! clighter#Disable()
    au! ClighterEnable
    call s:clear_match()
endf

augroup ClighterEnable
