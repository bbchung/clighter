let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
py import vim
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import clighter

fun! clighter#ToggleCursorHL()
    if g:ClighterCursorHL==1
        py clighter.clear_def_ref()
    endif

    let g:ClighterCursorHL = !g:ClighterCursorHL
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
                    \ echomsg "Clighter unavailable: cannot enable clighter, try set g:clighter_libclang_file" |
                    \ echohl None
        return
    endif

    py clighter.clang_switch_buffer()
    py clighter.clang_create_all_tu_ctx()

    augroup ClighterEnable
        au!
        if g:clighter_realtime == 1
            au CursorMoved * py clighter.highlight_window()
            au CursorMovedI * py clighter.highlight_window()
            au TextChanged * py clighter.update_unsaved_if_allow()
            au TextChangedI * py clighter.update_unsaved_if_allow()
        else
            au CursorHold * py clighter.update_unsaved_if_allow()
            au CursorHoldI * py clighter.update_unsaved_if_allow()
        endif
        au CursorHold * py clighter.highlight_window()
        au CursorHoldI * py clighter.highlight_window()
        au WinEnter * py clighter.clang_switch_buffer()
        au BufEnter * py clighter.clang_switch_buffer()
        au SessionLoadPost * py clighter.clang_switch_buffer()
        au FileType * py clighter.on_FileType()
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

fun! clighter#SetCompileArgs(str_args)
    let g:ClighterCompileArgs = a:str_args
    py clighter.clang_set_compile_args(eval(vim.bindeval('a:str_args')))
endf
