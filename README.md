# Clighter: plugin for c-family semantic source code highlighting

## Intro
Clighter(Clang Highlighter) is a c-family semantic highlighting plugin for
Vim based on Clang. This plugin use libclang to enhance c-family source code
highlighting from Vim builtin syntax highlighting to semantic highlighting.
Clighter doesn't disable the builtin syntax highlighting, it just "append"
the semantic highlighting into the word.  

Clighter provides the following features:

* Autumatically do semantic highlighting for c-family source code.
* Automatically mark all words that are same as the word under cursor
* Options to customize the colors

![clighter demo](http://goo.gl/ZtCD9x)   ![clighter demo](http://goo.gl/1a1JH5)

## Requirements

The clighter plugin requires the following:

* Vim version 7.3 and above
* libclang

Clighter currently works only at linux platform, others have not been test.


## Options

### g:enable_clighter
If enabled, Clighter will start with Vim, you can disable Clighter by set
g:enable_clighter to 0

Default: `1`

	let g:enable_clighter = 0


### g:clighter_cursor_toggle_key
The hotkey to toggle cursor highlighting function.

Default: `'<F3>'`


	let g:clighter_cursor_toggle_key = '<F3>'


### g:clighter_clang_options
The compiler options for libclang. Sometimes Clighter doesn't do corret
highlighting cause Clang can't parse the source code, then you need tell Clang
how to parse it. You can set the compiler options to the list in
g:clighter_clang_options.

Default: `[]`

	let g:clighter_clang_options = ['-std=c++', '-DLinux']


### g:clighter_libclang_path
Clighter use default path to find libclang, if your libclang is not in
default path, tell Clighter by this option.

Default: `undefine`


	let g:clighter_libclang_path = '/usr/lib/libclang.so'


## Customize Colors

Clighter defines the following syntax group corresponding to CursorKing of libclang

###MacroInstantiation
Default: `hi link MacroInstantiation Macro`

###TypeRef
Default: `hi link TypeRef Type`

###StructDecl
Default: `hi link StructDecl Type`

###ClassDecl
Default: `hi link ClassDecl Type`

###EnumDecl
Default: `hi link EnumDecl Type`

###EnumConstantDecl
Default: `hi link EnumConstantDecl Identifier`

###DeclRefExpr
Default: `hi link DeclRefExpr Identifier`

eg:
```vim
	hi TypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
	hi ClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
```


## Frequently Asked Questions

### The clighter plugin doesn't work.
Vim version 7.3 or above is need, and make sure libclang is installed
correctly and set g:clighter_libclang_path if need.

### Highlighing is not quick-response
Clighter use CursorHold event to update the current window highlighting,
you can set updatetime smaller. Remember that other plugins may chagne the
updatetime
```vim
	set updatetime=1200
```
[1]: http://goo.gl/ncGLYC
[2]: http://goo.gl/4QCv6O
