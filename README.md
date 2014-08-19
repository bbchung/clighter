# Clighter: Plugin to improve c-family development environment based on Clang

## Intro

Clighter(C Lighter) is a vim plugin that integrates the libclang to improve c-family
development environment, and it currently provides the following features(for c-family):

* Automatically do semantic highlighting
* Automatically highlight all words that with the same definition
* Options to customize the colors
* Experimental function to do rename-refactoring

![clighter demo](http://goo.gl/ivfipF "Enable Clighter")
![clighter demo](http://goo.gl/zq2Epq "Disable Clighter")

## Requirements

Clighter requires the following:

* Vim version 7.4+ with python2.x enabled
* libclang(only 3.5 has been tested)

Clighter only has been tested in linux platform

## Options

### g:clighter_autostart
Clighter will automatically start syntax highlight engine if g:clighter_autostart == `1`.

Default: `1`
```vim
let g:clighter_autostart = 0
```

### g:clighter_window_size

Clighter uses vim's regular expression(RE) engine to do syntax highlighting, however,
vim's RE engine performs bad while there are too many RE rules. To avoid too many RE
rules, Clighter only highlights a given region(window) instead of whole buffer.
	
* `< 0`: highlight whole buffer.
* `>= 0`: highlight from top line number reduce 100 * clighter_window_size to bottom line
number plug 100 * clighter_window_size of screen.

Default: `1`
```vim
let g:clighter_window_size = -1 " whole buffer
let g:clighter_window_size = 0 " highlight current screen of window
```

### g:clighter_clang_options

The compiler options for Clang. Clighter will pass these options to libclang
to parse the code.

Default: `[]`
```vim
let g:clighter_clang_options = ['-std=c++', '-DLinux']
```

### g:clighter_libclang_file

The path of libclang.

Default: `''`
```vim
let g:clighter_libclang_file = '/usr/lib/libclang.so'
```
### g:clighter_realtime

Do syntax highlighting in realtime(by CursorMoved event). Turn off this option may improve
the performance.

Default: `1`
```vim
let g:clighter_realtime = 1
```

## Commands and Functions

Clighter provides these commands and functions

* Enable Clighter's syntax highlight engine

	`ClighterEnable`

* Disable Clighter's syntax highlight engine

	`ClighterDisable`

* Toggle cursor highlighting

	`ClighterToggleCursorHL`

* Rename-refactor the variable/function name under vim cursor
	* It's a experimental function
	* It only processes the files that have been opened in vim's buffer list already.
	* Makesure that you have save all files before calling this function.

	`clighter#Rename()`


## Customize Colors

Clighter defines the following syntax group corresponding to CursorKind of libclang.

* MacroInstantiation
	```vim
	hi link MacroInstantiation Macro
	```

* TypeRef
	```vim
	hi link TypeRef Type
	```

* StructDecl
	```vim
	hi link StructDecl Type
	```

* ClassDecl
	```vim
	hi link ClassDecl Type
	```

* EnumDecl
	```vim
	hi link EnumDecl Type
	```

* EnumConstantDecl
	```vim
	hi link EnumConstantDecl Identifier
	```

* EnumDefRefExpr
	```vim
	hi link EnumDefRefExpr Identifier
	```

You can customize these colors in your colorscheme, for example:
```vim
	hi TypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
	hi ClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
```


## FAQ

### The clighter plugin doesn't work.
Vim version 7.4+ with python2.x is required, and make sure libclang(3.5 has been tested
only) is installed correctly and set g:clighter_libclang_file if need.

### Highlighting is not quick-response
Clighter use CursorHold event to update the current window highlighting,
and only highlight the code when parsing is done. To get the better response
time, you can set g:clighter_realtime = 1, or change updatetime to a smaller
value and pray your Clang run faster. Notice that many other plugins will
change updatetime. If the code includes the header file that was modified,
you must save the header.
```vim
	let g:clighter_realtime = 1
	set updatetime=1200
```
### Why rename-refactoring function is an experimental function
Libclang doesn't provide direct way to do rename-refactoring, so Clighter needs to
give its own way to search the AST. The search method is relatively easy and reliable when
there is only single file, but when there are many files, Clighter can't gurantee the
result of rename-factoring is totally correct.


[1]: http://goo.gl/ncGLYC
[2]: http://goo.gl/4QCv6O
