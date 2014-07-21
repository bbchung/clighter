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

fun! s:clear_match(type)
    if !exists('w:highlight_dict')
        return
    endif

    for i in w:highlight_dict[a:type]
        call matchdelete(i)
    endfor

    let w:highlight_dict[a:type] = []
endf

fun! s:try_highlight()
    let w:highlight_dict = get(w:, 'highlight_dict', {'semantic':[], 'cursor_def_ref':[]})
    let w:window = get(w:, 'window', [0, 0])

    py clighter.try_highlight()
endf

fun! clighter#Enable()
    py clighter.start_parsing_thread()
    augroup ClighterEnable
        au!
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m call s:try_highlight()
        else
            au CursorHold *.[ch],*.[ch]pp,*.m call s:try_highlight()
        endif
        au TextChanged *.[ch],*.[ch]pp,*.m py clighter.reset_timeup()
        au BufEnter *.[ch],*.[ch]pp,*.m py clighter.reset_timeup()
        au VimLeavePre * py clighter.stop_parsing_thread()
    augroup END
endf

fun! clighter#Disable()
    au! ClighterEnable
    py clighter.stop_parsing_thread()
    call s:clear_match('semantic')
    call s:clear_match('cursor_def_ref')
endf
