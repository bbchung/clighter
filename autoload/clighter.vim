let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
py import vim
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import clighter
py from clang_service import ClangService

let s:cursor_decl_ref_hl_on = 1

fun! clighter#ToggleCursorHL()
    if s:cursor_decl_ref_hl_on==1
        let s:cursor_decl_ref_hl_on=0
        py clighter.unhighlight_def_ref()
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

fun! clighter#Enable()
    if exists("s:clang_initialized")
        return
    endif

    if !pyeval('ClangService.init(vim.vars["clighter_clang_options"])')
        echohl WarningMsg |
                    \ echomsg "Clighter unavailable: cannot enable clighter, try set g:clighter_libclang_file" |
                    \ echohl None
        return
    endif

    py clighter.create_all_tu()

    augroup ClighterEnable
        au!
        if g:clighter_realtime == 1
            au CursorMoved *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
            au CursorMovedI *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
            au TextChanged *.[ch],*.[ch]pp,*.m py ClangService.update_unsaved(vim.current.buffer.name, '\n'.join(vim.current.buffer))
            au TextChangedI *.[ch],*.[ch]pp,*.m py ClangService.update_unsaved(vim.current.buffer.name, '\n'.join(vim.current.buffer))
        else
            au CursorHold *.[ch],*.[ch]pp,*.m py ClangService.update_unsaved(vim.current.buffer.name, '\n'.join(vim.current.buffer))
            au CursorHoldI *.[ch],*.[ch]pp,*.m py ClangService.update_unsaved(vim.current.buffer.name, '\n'.join(vim.current.buffer))
        endif
        au CursorHold *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        au CursorHoldI *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        " workaround to rehighlight while split window
        au WinEnter * py clighter.unhighlight_window()
        au BufWinEnter * py clighter.unhighlight_window()
        au BufWinEnter *.[ch],*.[ch]pp,*.m py clighter.highlight_window()
        au BufRead *.[ch],*.[ch]pp,*.m py ClangService.create_tu([vim.current.buffer.name])
        au BufNewFile *.[ch],*.[ch]pp,*.m py ClangService.create_tu([vim.current.buffer.name])
        au VimLeavePre * py ClangService.release()
    augroup END

    let s:clang_initialized=1
endf

fun! clighter#Disable()
    silent! au! ClighterEnable
    py ClangService.release()
    silent! unlet s:clang_initialized
    let a:wnr = winnr()
    windo py clighter.unhighlight_window()
    exe a:wnr."wincmd w"
endf

fun! clighter#Rename()
    py clighter.refactor_rename()
endf

fun! clighter#SetClangOptions(arg)
    py ClangService.set_compile_arg(list(vim.bindeval('a:arg')))
endf
