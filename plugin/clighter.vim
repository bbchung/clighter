if v:version < 703
    echohl WarningMsg |
                \ echomsg "Clighter unavailable: requires Vim 7.3+" |
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
let g:clighter_window_size = get(g:, 'clighter_window_size', 0)
let g:clighter_libclang_file = get(g:, 'clighter_libclang_file', '')

command! ClighterEnable call clighter#Enable()
command! ClighterDisable call clighter#Disable()
command! ClighterToggleCursorHL call clighter#ToggleCursorHL()

hi link MacroInstantiation Macro
hi link TypeRef Type
hi link StructDecl Type
hi link ClassDecl Type
hi link EnumDecl Type
hi link EnumConstantDecl Identifier
hi link DeclRefExpr Identifier

augroup ClighterStart
  au!
  au VimEnter *.[ch],*.[ch]pp,*.objc if g:clighter_autostart == 1 | call clighter#Enable() | endif
augroup END

let g:loaded_clighter = 1
