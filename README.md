# Clighter: VIM plugin to improve c-family development environment based on Clang

## Intro

Clighter(C Lighter) is a vim plugin that integrates libclang to improve
development environment for c-family programming. Clighter provides following
features currently:

* Syntax(semantic) highlighting
* Cursor word highlighting
* Customizable color of highlighting
* Experimental function to for rename-refactoring

![Clighter GIF demo](http://goo.gl/C7FYg8)

## Requirements

Clighter requires the following:

* Vim version 7.4+ with python2.x enabled
* libclang(3.5 is recommended) 
* Clighter has been tested in linux platform only.

## Installation
* Vundle Install:
```vim
Bundle 'bbchung/clighter'
```
* Manuall Install

Untar the clighter.tar.gz to your vim path.


## Options

### g:clighter_autostart
Clighter automatically start while g:clighter_autostart == `1`.

Default: `1`
```vim
let g:clighter_autostart = 0
```

### g:ClighterCompileArgs

The compiler options for Clang. Clighter will pass these options to libclang to
parse the code. Notice that bad options will cause clighter not working even
crashing. For convenience, you can use vim session to remember this option.

Default: `'["-Iinclude"]'`
```vim
let g:ClighterCompileArgs = '["-x", "c++", "-std=c++", "-DLinux"]'
```

### g:clighter_libclang_file

Clighter try to find libclang-3.5 in your system automatically, if clighter
doesn't find the libclang or other version of libclang is used, you need set
this path.

Default: `''`
```vim
let g:clighter_libclang_file = '/usr/lib/libclang.so'
```
### g:clighter_realtime

Do syntax highlighting in realtime. Turn off this option may improve the
performance.

Default: `1`
```vim
let g:clighter_realtime = 1
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

### g:clighter_highlight_groups
Define the token type of syntax to highlight.

Default:
```vim
['clighterMacroInstantiation', 'clighterStructDecl', 'clighterClassDecl', 'clighterEnumDecl', 'clighterEnumConstantDecl', 'clighterTypeRef', 'clighterDeclRefExprEnum']
```

### g:clighter_cursor_hl_default
Enable cursor highlight by default

Default: `1`
```vim
let g:clighter_cursor_hl_default = 0
```



## Commands and Functions

Clighter provides these commands and functions.

* Enable Clighter

	`ClighterEnable`

* Disable Clighter

	`ClighterDisable`

* Toggle cursor highlighting

	`ClighterToggleCursorHL`

* Rename-refactor
	* It's a experimental function, and it's maybe not reliable.
	* It's not project scoped(the scope is opend vim buffer list).
	* Strongly recommend that backing up all files before calling this
	  function.

	`clighter#Rename()`
    
    For convenience, you can add key mapping in your vimrc:
	```vim
    nmap <silent> <Leader>r :call clighter#Rename()<CR>
	```

* Set clang compile args in runtime

	`call clighter#SetCompileArgs()`


## Customize Colors

Clighter defines these syntax groups corresponding to CursorKind of libclang.

* clighterMacroInstantiation
	```vim
	hi link clighterMacroInstantiation Constant
	```

* clighterTypeRef
	```vim
	hi link clighterTypeRef Identifier
	```

* clighterStructDecl
	```vim
	hi link clighterStructDecl Type
	```

* clighterClassDecl
	```vim
	hi link clighterClassDecl Type
	```

* clighterEnumDecl
	```vim
	hi link clighterEnumDecl Type
	```

* clighterEnumConstantDecl
	```vim
	hi link clighterEnumConstantDecl Identifier
	```

* clighterDeclRefExprEnum
	```vim
	hi link clighterDeclRefExprEnum Identifier
	```

* clighterCursorDefRef
	```vim
	hi link clighterCursorDefRef IncSearch
	```

* clighterFunctionDecl
	```vim
	hi link clighterFunctionDecl None
	```

* clighterDeclRefExprCall
	```vim
	hi link clighterDeclRefExprCall None
	```

* clighterMemberRefExpr
	```vim
	hi link clighterMemberRefExpr None
	```

* clighterNamespace
	```vim
	hi link clighterNamespace None
	```

You can customize these colors in your colorscheme, for example:
```vim
	hi clighterTypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
	hi clighterClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
```


## FAQ

### The clighter plugin doesn't work.
Vim version 7.4+ with python2.x is required, and make sure libclang(3.5 is
recommended) is installed correctly and set g:clighter_libclang_file if need.

### Why rename-refactoring function is an experimental function
Even though libclang provides many useful informations, it's not enough to do
cross file rename-refactoring, so Clighter needs to use its own way way to
'guess' what should be renamed. Clighter can't gurantee the result of
rename-factoring result is perfect.
