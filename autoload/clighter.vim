let s:plug = expand("<sfile>:p:h:h") . '/misc'
execute 'python import sys'
execute 'python sys.path.append("' . s:plug . '")'
execute 'python import clighter'

let w:match_dict = {'semantic':[], 'def':[]}

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
  python clighter.start_parsing()
endf

fun! s:try_match_def()
  python clighter.try_match_def(int(vim.eval('line(".")')), int(vim.eval('col(".")')))
endf

fun! s:clear_match(type)
    for i in w:match_dict[a:type]
        call matchdelete(i)
    endfor

    let w:match_dict[a:type] = []
endf

fun! s:try_highlight_semantic()
  python clighter.try_highlight_semantic()
endf

fun! clighter#Enable()
    augroup ClighterEnable
        au!
        au BufEnter *.[ch],*.[ch]pp,*.m call s:start_parsing()
        au CursorHold *.[ch],*.[ch]pp,*.m call s:start_parsing()
        au CursorHold *.[ch],*.[ch]pp,*.m call s:try_match_def()
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m call s:try_highlight_semantic()
        else
            au CursorHold *.[ch],*.[ch]pp,*.m call s:try_highlight_semantic()
        endif
        
        au CursorMoved *.[ch],*.[ch]pp,*.m call s:clear_match('def')
    augroup END

    call s:start_parsing()
endf

fun! clighter#Disable()
    au! ClighterEnable
    call s:clear_match('semantic')
    call s:clear_match('def')
endf
