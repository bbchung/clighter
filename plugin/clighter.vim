if v:version < 704 || !exists("*matchaddpos")
    echohl WarningMsg |
                \ echomsg "Clighter unavailable: requires Vim 7.4p330+" |
                \ echohl None
    finish
endif

if !has('python')
    echohl WarningMsg |
                \ echomsg "Clighter unavailable: required python2 support" |
                \ echohl None
    finish
endif

if exists('g:loaded_clighter')
  finish
endif

let g:clighter_autostart = get(g:, 'clighter_autostart', 1)
let g:clighter_clang_options = get(g:, 'clighter_clang_options', [])
let g:clighter_window_size = get(g:, 'clighter_window_size', 1)
let g:clighter_libclang_file = get(g:, 'clighter_libclang_file', '')
let g:clighter_realtime = get(g:, 'clighter_realtime', 1)
let g:clighter_rename_prompt_level = get(g:, 'clighter_rename_prompt_level', 1)
let g:clighter_enable_cross_rename = get(g:, 'clighter_enable_cross_rename', 1)

command! ClighterEnable call clighter#Enable()
command! ClighterDisable call clighter#Disable()
command! ClighterToggleCursorHL call clighter#ToggleCursorHL()

hi link MacroInstantiation Macro
hi link TypeRef Type
hi link StructDecl Type
hi link ClassDecl Type
hi link EnumDecl Type
hi link EnumConstantDecl Identifier

hi link EnumDeclRefExpr Identifier
hi link CursorDefRef Search

if g:clighter_autostart == 1
    augroup ClighterAutoStart
        au VimEnter * call clighter#Enable()
    augroup END
endif
