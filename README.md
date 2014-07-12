# Clighter: plugin for c-family semantic source code highlighting, based on Clang

## Intro

Clighter(Clang Highlighter) is a c-family semantic highlighting plugin for
Vim, based on Clang. Clighter use libclang to enhance c-family source code
highlighting from Vim builtin syntax highlighting to semantic highlighting.
Clighter doesn't disable the builtin syntax highlighting, but just "append"
the semantic highlighting into the code.  

Clighter provides the following features:

* Automatically do semantic highlighting for c-family source code.
* Automatically mark all words that are same as the word under cursor
* Options to customize the colors

![clighter demo](http://goo.gl/ivfipF "Enable Clighter")
![clighter demo](http://goo.gl/zq2Epq "Disable Clighter")

## Requirements

The clighter plugin requires the following:

* Vim version 7.3(or above) with python2.x enabled
* libclang

Clighter currently works only at linux platform, others have not been tested.


## Options

### g:clighter_autostart
Clighter will automatically start with Vim if set g:clighter_autostart to 1,
otherwise, you have to manually start Clighter by ClighterEnable command.

Default: `1`
```vim
let g:clighter_autostart = 0
```

### g:clighter_window_size

Clighter uses vim regular expression engine to do syntax highlighting,
but vim's RE engine performs very bad when there are too many rules. Clighter
can only highlight a given region instead of whole buffer each time to get
the good performance even when the file is very large. 
	
clighter_window_size < 0: highlight whole buffer.

clighter_window_size >= 0: highlight from top line number reduce 30 *
clighter_window_size to bottom line number plug 30 * clighter_window_size of
screen.

Default: `0`
```vim
let g:clighter_window_size = -1 " whole buffer
let g:clighter_window_size = 0 " highlight current screen of window
```

### g:clighter_clang_options

The compiler options for Clang. Sometimes Clighter doesn't do correct
highlighting cause Clang can't parse the source code without necessary
options, so you need tell Clang how to parse the code. You can set the 
compiler options to g:clighter_clang_options with list.

Default: `[]`
```vim
let g:clighter_clang_options = ['-std=c++', '-DLinux']
```

### g:clighter_libclang_file

If your libclang is not in default path of system, tell Clighter by this
option.

Default: `''`
```vim
let g:clighter_libclang_file = '/usr/lib/libclang.so'
```
## Commands

Clighter provides command to control it

* Enable Clighter

	`ClighterEnable`

* Disable Clighter

	Notice that is will not disable the cursor highlighting.

	`ClighterDisable`

* Toggle cursor highlighting

	`ClighterToggleCursorHL`

## Customize Colors

Clighter defines the following syntax group corresponding to CursorKing of Clang.

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

* DeclRefExpr
	```vim
	hi link DeclRefExpr Identifier
	```

You can customize these colors in your colorscheme, for example:
```vim
	hi TypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
	hi ClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
```


## FAQ

### The clighter plugin doesn't work.
Vim version 7.3(or above) with python2.x is required, and make sure libclang is installed
correctly and set g:clighter_libclang_file if need.

### Highlighting is not quick-response
Clighter use CursorHold event to update the current window highlighting,
and only highlight the code when parsing is done. To get the better response
time, you can change updatetime smaller and pray your Clang run faster.
Notice that many other plugins will change updatetime. If the code includes
the header file that was modified, you must save the header.
```vim
	set updatetime=1200
```
[1]: http://goo.gl/ncGLYC
[2]: http://goo.gl/4QCv6O
