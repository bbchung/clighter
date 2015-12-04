# Clighter: VIM plugin to improve c-family development environment based on Clang

## Try Clamp If You Use NeoVim
Try Clamp if you use NeoVim, it use NeoVim's new plugin api with lighting highlight speed

https://github.com/bbchung/Clamp

## Intro

Clighter(C lighter) makes vim a better c-family development environment as a
plugin based on libclang. Clighter provides following features currently:

* Context-sentitive highlight
	* Syntax highlight
	* Occurrences highlight
* Experimental rename-refactoring function

![Clighter GIF demo](http://goo.gl/C7FYg8)



## Requirements

Clighter requires the following:

* Vim version 7.4 with python2.x enabled
* libclang. Please reference http://llvm.org/apt/ to install
* Clighter has been tested under Linux

## Installation

* Vundle Install:
```vim
Bundle 'bbchung/clighter'
```
* Manuall Install

Untar the clighter.tar.gz to your vim path.

## Options

### g:clighter_autostart

Clighter will automatically start while g:clighter_autostart == `1`.

Default: `1`
```vim
let g:clighter_autostart = 1
```

### g:clighter_libclang_file

Clighter searches libclang-3.5 in your system automatically. You must set this
option when clighter cannot find libclang, or other version of libclang is
used.

Default: `''`
```vim
let g:clighter_libclang_file = '/usr/lib/libclang.so'
```

### g:clighter_rename_prompt_level

The prompt level of rename refactoring.

`0`: no prompt

`1`: prompt while do cross buffer renaming

`2`: prompt of each word that going to be replaced

Default: `1`
```vim
let g:clighter_rename_prompt_level = 1
```

### g:clighter_enable_cross_rename

`0`: disable

`1`: enable

Default: `1`
```vim
let g:clighter_enable_cross_rename = 1
```

### g:clighter_highlight_blacklist

Define the group of syntax NOT to be highlighted.

Default: `['cligherInclusionDirective']`

The recommend setting to not be dazzled:
```vim
let g:clighter_highlight_blacklist = ['clighterNamespaceRef', 'clighterFunctionDecl', 'clighterFieldDecl', 'clighterDeclRefExprCall', 'clighterMemberRefExprCall', 'clighterMemberRefExprVar', 'clighterNamespace', 'clighterNamespaceRef', 'cligherInclusionDirective', 'clighterVarDecl']
```

### g:clighter_occurrences_mode

If value is 0, the behavior of occurrences highlight is visual studio
liked(some delay before highlighting different cursors), or the cursors will
always be highlighted immediately.

Default: `0`
```vim
let g:clighter_occurrences_mode = 0
```

### g:clighter_heuristic_compile_args

Clighter will search the compilation database to compile, however the
compilation database the CMake generated doesn't include the header files(make
sense, but clighter needs it). Clighter can heuristic search the compilation
database to guess the most possible compile args if set this option, and it's
useful for header files.

Default: `1`
```vim
let g:clighter_heuristic_compile_args = 1
```

### g:clighter_compile_args

The global compile args of clighter. It will be appended in each file's
compile args.

Default: `[]`
```vim
let g:clighter_compile_args = []
```

### g:ClighterOccurrences

Enable occurrences highlight. Occurrences highlight is a clighter function
that highlight all words with the same semantic symbol.

Default: `1`
```vim
let g:ClighterOccurrences = 1
```


## Commands and Functions

Clighter provides these commands and functions.

### ClighterEnable

Enable clighter plugin.

### ClighterDisable

Disable clighter plugin.

### ClighterToggleOccurrences

Toggle occurrences highlighting.

### ClighterShowInfo

Show clighter runtime informations.

### clighter#Rename()

* An experimental function to do rename refactoring.
* The scope is opened vim buffers.
* There is no one-step undo/redo method.
* Strongly recommend that backing up all files before calling this function.
* For convenience, you can add key mapping in your vimrc:
```vim
nmap <silent> <Leader>r :call clighter#Rename()<CR>
```

## Compilation Database

Clighter automatically load and parse the compilation database
"compile_commands.json" if it exists in current working directory, then the
compile options will be passed to libclang. For more information about
compilation database, please reference [Compilation Database][cdb].

## Highlight Group

Clighter defines these highlight groups corresponded to libclang.

```vim
hi default link clighterPrepro PreProc
hi default link clighterDecl Identifier
hi default link clighterRef Type
hi default link cligherInclusionDirective cIncluded
hi default link clighterMacroInstantiation Constant
hi default link clighterVarDecl Identifier
hi default link clighterStructDecl Identifier
hi default link clighterUnionDecl Identifier
hi default link clighterClassDecl Identifier
hi default link clighterEnumDecl Identifier
hi default link clighterParmDecl Identifier
hi default link clighterFunctionDecl Identifier
hi default link clighterFieldDecl Identifier
hi default link clighterEnumConstantDecl Constant
hi default link clighterDeclRefExprEnum Constant
hi default link clighterDeclRefExprCall Type
hi default link clighterMemberRefExprCall Type
hi default link clighterMemberRefExprVar Type
hi default link clighterTypeRef Type
hi default link clighterNamespace Identifier
hi default link clighterNamespaceRef Type
hi default link clighterTemplateTypeParameter Identifier
hi default link clighterTemplateRef Type
hi default link clighterOccurrences IncSearch
```

You can customize these colors in your colorscheme, for example:
```vim
hi clighterTypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
hi clighterClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
```

## FAQ

### The clighter plugin doesn't work?
Vim version 7.4 with python2.x is required, and make sure libclang(3.5 and 3.6
is recommended) is installed correctly and set g:clighter_libclang_file if
need.

### Why rename-refactoring function is an experimental function?
Due to the character of c-family language, even libclang provides a powerful
c-family parser, it still hard to do rename refactoring. Clighter can only
search the current opened buffer to do rename refactoring and it can't
guarantee the result correct.

### Libclang crash?
When incorrect compile args meet incorrect source code, libclang possibly
crashes(for example: empty compile arg meet .hxx), and it may happend in vim
thread or background thread of clighter. Currently clighter can't catch such
crash, so vim will become unstable if it happens.

### Highlighting always are messed up as typing, can fix?
No, Clighter use position based matching by vim. When typing, it can't
automatically move the typing offset for highlighted word. Once vim provides
such api, it will be fixed.

### How to set compile args?
Clighter set the compile args for each file with (g:clighter_compile_args +
"compilation database"), and both are optional. Compile args will affect the
correctness of highlight and refactoring function.

## LICENSE

This software is licensed under the [GPL v3 license][gpl].

Note: This license does not cover the files that come from the LLVM project.


[gpl]: http://www.gnu.org/copyleft/gpl.html
[ycm]: https://github.com/Valloric/YouCompleteMe
[cdb]: http://clang.llvm.org/docs/JSONCompilationDatabase.html
