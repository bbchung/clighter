let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
py import vim
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import clighter

augroup ClighterEnable
let s:cursor_decl_ref_hl_on = 1

fun! clighter#ToggleCursorHL()
    if s:cursor_decl_ref_hl_on==1
        let s:cursor_decl_ref_hl_on=0
        call s:clear_match(['ClighterMacroInstantiation', 'ClighterStructDecl', 'ClighterClassDecl', 'ClighterEnumDecl', 'ClighterEnumConstantDecl', 'ClighterTypeRef', 'ClighterDeclRefExprEnum', 'CursorDefRef'])
    else
        let s:cursor_decl_ref_hl_on=1
        "augroup CursorHighlight
            "au CursorHold * exe printf('match IncSearch /\V\<%s\>/', escape(expand('<cword>'), '/\'))
            "au CursorMoved * match none
            ""au CursorHold * let @/ = '\V\<'.escape(expand('<cword>'), '\').'\>'
        "augroup END
    endif
endf

fun! s:clear_match(groups)
    for m in getmatches()
        if index(a:groups, m['group']) >= 0
            call matchdelete(m['id'])
        endif
    endfor
endf

fun! clighter#Enable()
    py clighter.ParsingService.join_all()
    py clighter.ParsingService.start_sched_looping()

    augroup ClighterEnable
        au!
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        else
            au CursorHold *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        endif
        au WinEnter *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        au CursorHold *.[ch],*.[ch]pp,*.m py clighter.on_vim_cursor_hold()
        au BufRead *.[ch],*.[ch]pp,*.m py clighter.ParsingService.join()
        au BufWinEnter * call s:clear_match(['ClighterMacroInstantiation', 'ClighterStructDecl', 'ClighterClassDecl', 'ClighterEnumDecl', 'ClighterEnumConstantDecl', 'ClighterTypeRef', 'ClighterDeclRefExprEnum', 'CursorDefRef'])
        au VimLeavePre * py clighter.ParsingService.stop_sched_looping()
    augroup END
endf

fun! clighter#Disable()
    au! ClighterEnable
    py clighter.ParsingService.stop_sched_looping()
    let a:wnr = winnr()
    windo call s:clear_match(['ClighterMacroInstantiation', 'ClighterStructDecl', 'ClighterClassDecl', 'ClighterEnumDecl', 'ClighterEnumConstantDecl', 'ClighterTypeRef', 'ClighterDeclRefExprEnum', 'CursorDefRef'])
    exe a:wnr."wincmd w"
endf

fun! clighter#Rename()
    py clighter.refactor_rename()
endf
