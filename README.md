# Clighter: VIM plugin to improve c-family development environment based on Clang

## Intro

Clighter(C Lighter) is a vim plugin that integrates libclang to improve
c-family development environment, and it currently provides the following
features(for c-family):

* Automatically do syntax(semantic) highlighting.
* Automatically highlight all words with the same definition.
* Options to customize the colors.
* Experimental function to do rename-refactoring.

![clighter demo](http://goo.gl/ivfipF "Enable Clighter")
![clighter demo](http://goo.gl/zq2Epq "Disable Clighter")

## Requirements

Clighter requires the following:

* Vim version 7.4+ with python2.x enabled
* libclang(3.5 is recommanded) 
* Clighter has been tested in linux platform only.

## Options

### g:clighter_autostart
Clighter automatically start while g:clighter_autostart == `1`.

Default: `1`
```vim
let g:clighter_autostart = 0
```

### g:clighter_window_size

Clighter uses vim's regular expression(RE) engine to do syntax highlighting,
but the RE engine performs not well while there are too many RE rules. To get
the better performance, Clighter can highlights a given region(window) instead
of whole buffer.
	
`<0`: highlight whole buffer.

`>=0`: highlight from top line number reduce 100 * clighter_window_size to
bottom line number plug 100 * clighter_window_size of screen.

Default: `1`
```vim
let g:clighter_window_size = -1 " whole buffer
let g:clighter_window_size = 0 " highlight current screen of window
```

### g:clighter_clang_options

The compiler options for Clang. Clighter will pass these options to libclang
to parse the code.

Default: `[-Iinclude]`
```vim
let g:clighter_clang_options = ['-std=c++', '-DLinux']
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


## Commands and Functions

Clighter provides these commands and functions

* Enable Clighter

	`ClighterEnable`

* Disable Clighter

	`ClighterDisable`

* Toggle cursor highlighting

	`ClighterToggleCursorHL`

* Rename-refactor the variable/function name under vim cursor
	* It's a experimental function, and maybe not reliable.
	* It's not project based(only processes the files that have been opened in
	  vim's buffer list already).
	* Stronglly recommend that backing up all files before using this function
	  is recommanded.

	`clighter#Rename()`
    
    For convenience, you can add this key map in you vimrc:
	```vim
    nmap <silent> <Leader>r :call clighter#Rename()<CR>
	```


## Customize Colors

Clighter defines the following syntax group corresponding to CursorKind of
libclang.

* ClighterMacroInstantiation
	```vim
	hi link ClighterMacroInstantiation Macro
	```

* ClighterTypeRef
	```vim
	hi link ClighterTypeRef Type
	```

* ClighterStructDecl
	```vim
	hi link ClighterStructDecl Type
	```

* ClighterClassDecl
	```vim
	hi link ClighterClassDecl Type
	```

* ClighterEnumDecl
	```vim
	hi link ClighterEnumDecl Type
	```

* ClighterEnumConstantDecl
	```vim
	hi link ClighterEnumConstantDecl Identifier
	```

* ClighterEnumDefRefExpr
	```vim
	hi link ClighterEnumDefRefExpr Identifier
	```

You can customize these colors in your colorscheme, for example:
```vim
	hi ClighterTypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
	hi ClighterClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
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


[1]: http://goo.gl/ncGLYC
[2]: http://goo.gl/4QCv6O
