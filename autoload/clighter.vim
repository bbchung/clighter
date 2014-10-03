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
        call s:clear_match_grp(['clighterMacroInstantiation', 'clighterStructDecl', 'clighterClassDecl', 'clighterEnumDecl', 'clighterEnumConstantDecl', 'clighterTypeRef', 'clighterDeclRefExprEnum', 'clighterCursorDefRef'])
    else
        let s:cursor_decl_ref_hl_on=1
        "augroup CursorHighlight
            "au CursorHold * exe printf('match IncSearch /\V\<%s\>/', escape(expand('<cword>'), '/\'))
            "au CursorMoved * match none
            ""au CursorHold * let @/ = '\V\<'.escape(expand('<cword>'), '\').'\>'
        "augroup END
    endif
endf

fun! s:clear_match_grp(groups)
    for m in getmatches()
        if index(a:groups, m['group']) >= 0
            call matchdelete(m['id'])
        endif
    endfor
endf

fun! s:clear_match_pri(pri)
    for m in getmatches()
        if index(a:pri, m['priority']) >= 0
            call matchdelete(m['id'])
        endif
    endfor
endf

fun! s:on_buf_win_leave()
    call s:clear_match_pri([{0}, {1}])".format(DEF_REF_PRI, TOKEN_PRI))
endf


fun! clighter#Enable()

    if !exists("s:clang_initialized")
        py clighter.ClangService.init()
        if !exists("s:clang_initialized")
            echohl WarningMsg |
                        \ echomsg "Clighter unavailable: cannot enable clighter, try set g:clighter_libclang_file" |
                        \ echohl None
            return
        endif
    endif

    augroup ClighterEnable
        au!
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
            au CursorMovedI *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
            au TextChanged *.[ch],*.[ch]pp,*.m py clighter.ClangService.update_unsaved()
            au TextChangedI *.[ch],*.[ch]pp,*.m py clighter.ClangService.update_unsaved()
        else
            au CursorHold *.[ch],*.[ch]pp,*.m py clighter.ClangService.update_unsaved()
            au CursorHoldI *.[ch],*.[ch]pp,*.m py clighter.ClangService.update_unsaved()
        endif
        au CursorHold *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        au CursorHoldI *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        au BufWinEnter * py clighter.unhighlight_window()
        au BufWinEnter *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        au BufRead *.[ch],*.[ch]pp,*.m py clighter.ClangService.add_vim_buffer()
        au BufNewFile *.[ch],*.[ch]pp,*.m py clighter.ClangService.add_vim_buffer()
        au VimLeavePre * py clighter.ClangService.release()
    augroup END
endf

fun! clighter#Disable()
    au! ClighterEnable
    py clighter.ClangService.release()
    let a:wnr = winnr()
    windo call s:clear_match_grp(['clighterMacroInstantiation', 'clighterStructDecl', 'clighterClassDecl', 'clighterEnumDecl', 'clighterEnumConstantDecl', 'clighterTypeRef', 'clighterDeclRefExprEnum', 'clighterCursorDefRef'])
    exe a:wnr."wincmd w"
endf

fun! clighter#Rename()
    py clighter.refactor_rename()
endf
