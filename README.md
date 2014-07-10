# Clighter
Plugin for c-family semantic source code highlighting

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
Default: `'<F3>'`
The hotkey to toggle cursor highlighting function.
```vim
	let g:clighter_cursor_toggle_key = '<F3>'
```

### g:clighter_clang_options
Default: `[]`
The compiler options for libclang. Sometimes Clighter doesn't do corret
highlighting cause Clang can't parse the source code, then you need tell Clang
how to parse it. You can set the compiler options to the list in
g:clighter_clang_options
```vim
	let g:clighter_clang_options = ['-std=c++', '-DLinux']
```

### g:clighter_libclang_path
Default: `undefine`
Clighter use default path to find libclang, if your libclang is not in
default path, tell Clighter by this option
```vim
	let g:clighter_libclang_path = '/usr/lib/libclang.so'
```

## Customize Colors~

Clighter defines the following syntax group corresponding to CursorKing of

MacroInstantiation~
Default: link to Macro

TypeRef~
Default: link to Type

StructDecl~
Default: link to Type

ClassDecl~
Default: link to Type

EnumDecl~
Default: link to Type

EnumConstantDecl~
Default: link to Identifier

eg:
>
	hi TypeRef term=NONE cterm=NONE ctermbg=232 ctermfg=255 gui=NONE
	hi ClassDecl term=NONE cterm=NONE ctermbg=255 ctermfg=232 gui=NONE
<

==============================================================================
						*clighter-faq*
6. Frequently Asked Questions~

Q. The clighter plugin doesn't work.
A. Vim version 7.3 or above is need, and make sure libclang is installed
correctly and set g:clighter_libclang_path if need.

Q. Highlighing is not quick-response
A. Clighter use CursorHold event to update the current window highlighting,
you can set updatetime smaller. Remember that other plugins may chagne the
updatetime
>
	set updatetime=1200
<

==============================================================================

vim:tw=78:ts=8:noet:ft=help:
