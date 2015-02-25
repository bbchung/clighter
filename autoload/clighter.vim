let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )
py import sys
exe 'python sys.path = sys.path + ["' . s:script_folder_path . '/../misc"]'
py import vim
py import clighter
py import highlighting
py import clang_service
py import refactor

if !empty(g:clighter_libclang_file)

python << endpython
import vim
from clang import cindex
cindex.Config.set_library_file(vim.eval('g:clighter_libclang_file'))
endpython

endif


fun! clighter#ToggleCursorHL()
    if g:ClighterCursorHL==1
        let a:wnr = winnr()
        windo py highlighting.clear_symbol_hl()
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

    let a:cwd = getcwd()
    if !filereadable(a:cwd.'/compile_commands.json')
        let a:cwd = ''
    endif

    let a:start_cmd = printf("clang_service.ClangService().start('%s')", a:cwd)

    if !pyeval(a:start_cmd)
        echohl WarningMsg |
                    \ echomsg "Clighter unavailable: clang service failed, you must setup clang environment for clighter" |
                    \ echohl None
        return
    endif

    py clighter.register_allowed_buffers()
    py clighter.clang_switch_to_current()

    augroup ClighterEnable
        au!
        au CursorMoved,CursorMovedI * py highlighting.hl_window(clang_service.ClangService(), False)
        au CursorHold,CursorHoldI * py highlighting.hl_window(clang_service.ClangService(), True)
        au TextChanged,TextChangedI * py clighter.update_buffer_if_allow()
        au WinEnter,BufEnter,SessionLoadPost * py clighter.clang_switch_to_current()
        au FileType * py clighter.on_FileType()
        au BufDelete,BufWipeout * py clang_service.ClangService().unregister([vim.eval('fnamemodify(expand("<afile>"), ":p")')])
        au VimLeavePre * py clang_service.ClangService().stop()
    augroup END

    let s:clang_initialized=1
endf

fun! clighter#Disable()
    silent! au! ClighterEnable
    py clang_service.ClangService().stop()
    silent! unlet s:clang_initialized
    let a:wnr = winnr()
    windo py highlighting.clear_highlight()
    exe a:wnr."wincmd w"
endf

fun! clighter#Rename()
    py refactor.rename(clang_service.ClangService())
endf
