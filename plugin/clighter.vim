if v:version < 704 || !exists('*matchaddpos')
    echohl WarningMsg |
                \ echomsg 'Clighter unavailable: requires Vim 7.4p330+' |
                \ echohl None
    finish
endif

if !has('python')
    echohl WarningMsg |
                \ echomsg 'Clighter unavailable: requires python2 support' |
                \ echohl None
    finish
endif

if exists('g:loaded_clighter')
    finish
endif

let g:clighter_autostart = get(g:, 'clighter_autostart', 1)
let g:clighter_libclang_file = get(g:, 'clighter_libclang_file', '')
let g:clighter_rename_prompt_level = get(g:, 'clighter_rename_prompt_level', 1)
let g:clighter_enable_cross_rename = get(g:, 'clighter_enable_cross_rename', 1)
let g:clighter_highlight_blacklist = get(g:, 'clighter_highlight_blacklist', ['cligherInclusionDirective'])
let g:clighter_occurrences_mode = get(g:, 'clighter_occurrences_mode', 0)
let g:clighter_heuristic_compile_args = get(g:, 'clighter_heuristic_compile_args', 1)
let g:clighter_compile_args = get(g:, 'clighter_compile_args', [])
let g:clighter_highlight_mode = get(g:, 'clighter_highlight_mode', 1)

let g:ClighterOccurrences = get(g:, 'ClighterOccurrences', 1)

command! ClighterEnable call clighter#Enable()
command! ClighterDisable call clighter#Disable()
command! ClighterToggleOccurrences call clighter#ToggleOccurrences()
command! ClighterShowInfo call clighter#ShowInfo()

if g:clighter_autostart
    augroup ClighterAutoStart
        au VimEnter * call clighter#Enable()
    augroup END
endif

let g:loaded_clighter=1
