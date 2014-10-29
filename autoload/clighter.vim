let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
py import vim
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import clighter

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
    silent! au! ClighterAutoStart

    if exists("s:clang_initialized")
        return
    endif

    if !pyeval('clighter.clang_init_service()')
        echohl WarningMsg |
                    \ echomsg "Clighter unavailable: cannot enable clighter, try set g:clighter_libclang_file" |
                    \ echohl None
        return
    endif

    py clighter.clang_create_all_tu()

    augroup ClighterEnable
        au!
        if g:clighter_realtime == 1
            au CursorMoved * py clighter.highlight_window()
            au CursorMovedI * py clighter.highlight_window()
            au TextChanged * py clighter.on_TextChanged()
            au TextChangedI * py clighter.on_TextChanged()
        else
            au CursorHold * py clighter.on_TextChanged()
            au CursorHoldI * py clighter.on_TextChanged()
        endif
        au CursorHold * py clighter.highlight_window()
        au CursorHoldI * py clighter.highlight_window()
        " workaround to rehighlight while split window
        au WinEnter * py clighter.unhighlight_window()
        au BufWinEnter * py clighter.unhighlight_window()
        au BufWinEnter * py clighter.highlight_window()
        au BufRead * py clighter.on_NewFile()
        au BufNewFile * py clighter.on_NewFile()
        au VimLeavePre * py clighter.clang_release_service()
    augroup END

    let s:clang_initialized=1
endf

fun! clighter#Disable()
    silent! au! ClighterEnable
    py clighter.clang_release_service()
    silent! unlet s:clang_initialized
    let a:wnr = winnr()
    windo py clighter.unhighlight_window()
    exe a:wnr."wincmd w"
endf

fun! clighter#Rename()
    py clighter.refactor_rename()
endf

fun! clighter#SetClangOptions(arg)
    py clighter.clang_set_compile_arg(list(vim.bindeval('a:arg')))
endf
