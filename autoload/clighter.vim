let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
py import vim
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import clighter

let s:cursor_decl_ref_hl_on = 1

fun! clighter#ToggleCursorHL()
    if s:cursor_decl_ref_hl_on==1
        let s:cursor_decl_ref_hl_on=0
        call s:clear_match('cursor_def_ref')
    else
        let s:cursor_decl_ref_hl_on=1
        "augroup CursorHighlight
            "au CursorHold * exe printf('match IncSearch /\V\<%s\>/', escape(expand('<cword>'), '/\'))
            "au CursorMoved * match none
            ""au CursorHold * let @/ = '\V\<'.escape(expand('<cword>'), '\').'\>'
        "augroup END
    endif
endf

fun! s:start_parsing()
    py clighter.start_parsing()
endf

fun! s:clear_match(type)
    for i in b:highlight_dict[a:type]
        call matchdelete(i)
    endfor

    let b:highlight_dict[a:type] = []
endf

fun! s:try_highlight()
    let b:highlight_dict = get(b:, 'highlight_dict', {'semantic':[], 'cursor_def_ref':[]})
    py clighter.try_highlight()
endf

fun! clighter#Enable()
    augroup ClighterEnable
        au!
        au BufEnter *.[ch],*.[ch]pp,*.m call s:start_parsing()
        au CursorHold *.[ch],*.[ch]pp,*.m call s:start_parsing()
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m call s:try_highlight()
        else
            au CursorHold *.[ch],*.[ch]pp,*.m call s:try_highlight()
        endif
    augroup END

    call s:start_parsing()
endf

fun! clighter#Disable()
    au! ClighterEnable
    call s:clear_match('semantic')
    call s:clear_match('cursor_def_ref')
endf
