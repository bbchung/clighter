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
let g:ClighterCompileArgs = get(g:, 'ClighterCompileArgs', '["-Iinclude", "-x", "c++"]')
let g:clighter_libclang_file = get(g:, 'clighter_libclang_file', '')
let g:clighter_realtime = get(g:, 'clighter_realtime', 1)
let g:clighter_rename_prompt_level = get(g:, 'clighter_rename_prompt_level', 1)
let g:clighter_enable_cross_rename = get(g:, 'clighter_enable_cross_rename', 1)
let g:clighter_highlight_groups = get(g:, 'clighter_highlight_groups', ['clighterMacroInstantiation', 'clighterStructDecl', 'clighterClassDecl', 'clighterEnumDecl', 'clighterEnumConstantDecl', 'clighterTypeRef', 'clighterDeclRefExprEnum'])
let g:clighter_cursor_hl_default = get(g:, 'clighter_cursor_hl_default', 1)

command! ClighterEnable call clighter#Enable()
command! ClighterDisable call clighter#Disable()
command! ClighterToggleCursorHL call clighter#ToggleCursorHL()

hi default link clighterMacroInstantiation Constant
hi default link clighterTypeRef Identifier
hi default link clighterStructDecl Type
hi default link clighterClassDecl Type
hi default link clighterEnumDecl Type
hi default link clighterEnumConstantDecl Identifier
hi default link clighterDeclRefExprEnum Identifier
hi default link clighterCursorDefRef IncSearch
hi default link clighterFunctionDecl None
hi default link clighterDeclRefExprCall None
hi default link clighterMemberRefExpr None
hi default link clighterNamespace None

if g:clighter_autostart == 1
    augroup ClighterAutoStart
        au FileType c,cpp,objc call clighter#Enable()
    augroup END
endif

let g:loaded_clighter=1
