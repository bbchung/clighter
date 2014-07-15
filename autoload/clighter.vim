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
  python start_parsing()
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

  python try_highlighting()
endf

fun! clighter#Enable()
  echom "Enabling"
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
