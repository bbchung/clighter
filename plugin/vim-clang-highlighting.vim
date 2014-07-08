python << endpython
import vim
import sys
import clang.cindex

def vim_highlight(t, group):
#    vim.command("call matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1)".format( group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1))
    vim.command("call add(s:matched_list, matchadd('{0}', '\%{1}l\%>{2}c.\%<{3}c', -1))".format( group, t.location.line, t.location.column-1, t.location.column+len(t.spelling) + 1));

def find_typerefs(node):
    vim.command('call s:clear_match()');
	
    for t in node.get_tokens():
        if t.kind.value == 2:
            if t.cursor.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
                vim_highlight(t, 'Macro')
            elif t.cursor.kind == clang.cindex.CursorKind.STRUCT_DECL:
                vim_highlight(t, 'Type')
            elif t.cursor.kind == clang.cindex.CursorKind.CLASS_DECL:
                vim_highlight(t, 'Type')
            elif t.cursor.kind == clang.cindex.CursorKind.ENUM_DECL:
                vim_highlight(t, 'Type')
            elif t.cursor.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                vim_highlight(t, 'Identifier')
            elif t.cursor.kind == clang.cindex.CursorKind.TYPE_REF:
                vim_highlight(t, 'Type')
    vim.command('let s:expired=0');
endpython

fun! s:clear_match()
	for i in s:matched_list
		call matchdelete(i)
	endfor
	let s:matched_list=[]
endf

fun! s:clang_highlight()
	if s:expired == 0	
		return
	endif
python << endpython
buffer = vim.current.buffer
index = clang.cindex.Index.create()
tu = index.parse(buffer.name, None, [(buffer.name, "\n".join(vim.current.buffer))], options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
find_typerefs(tu.cursor)
endpython
endf

let s:expired=1
let s:matched_list=[]
au CursorHold *.[ch],*.[ch]pp call s:clang_highlight()
au FileType c,cpp,objc call s:clang_highlight()
au InsertLeave *.[ch],*.[ch]pp let s:expired=1
