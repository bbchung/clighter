let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
py import vim
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import clighter

fun! clighter#ToggleCursorHL()
    if g:ClighterCursorHL==1
        let a:wnr = winnr()
        windo py clighter.clear_symbol_ref()
        exe a:wnr."wincmd w"
    endif

    let g:ClighterCursorHL = !g:ClighterCursorHL

    echohl WarningMsg |
                \echom printf("Cursor Highlight: %s", g:ClighterCursorHL == 1 ? "Enabled" : "Disabled") |
                \echohl None
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
    silent! au! ClighterAutoStart

    if exists("s:clang_initialized")
        return
    endif

    if !pyeval('clighter.clang_start_service()')
        echohl WarningMsg |
                    \ echomsg "Clighter unavailable: clang service failed, you must setup clang environment for clighter" |
                    \ echohl None
        return
    endif

    py clighter.register_allowed_buffers()
    py clighter.clang_switch_to_current()

    augroup ClighterEnable
        au!
        au CursorMoved,CursorMovedI,CursorHold,CursorHoldI * py clighter.highlight_window()
        au TextChanged,TextChangedI * py clighter.update_buffer_if_allow()
        au WinEnter,BufEnter,SessionLoadPost * py clighter.clang_switch_to_current()
        au FileType * py clighter.on_FileType()
        au BufDelete,BufWipeout * py clighter.unregister_buffer(vim.eval('fnamemodify(expand("<afile>"), ":p")'))
        au VimLeavePre * py clighter.clang_stop_service()
    augroup END

    let s:clang_initialized=1
endf

fun! clighter#Disable()
    silent! au! ClighterEnable
    py clighter.clang_stop_service()
    silent! unlet s:clang_initialized
    let a:wnr = winnr()
    windo py clighter.clear_highlight()
    exe a:wnr."wincmd w"
endf

fun! clighter#Rename()
    py clighter.refactor_rename()
endf

fun! clighter#SetCompileArgs(args)
    let g:ClighterCompileArgs = a:args
    py clighter.clang_set_compile_args(vim.eval('g:ClighterCompileArgs'))
endf
