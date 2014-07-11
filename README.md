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

![clighter demo](http://goo.gl/ivfipF "Enable Clighter")
![clighter demo](http://goo.gl/zq2Epq "Disable Clighter")

## Requirements

The clighter plugin requires the following:

* Vim version 7.3 and above with python2.x enabled
* libclang

Clighter currently works only at linux platform, others have not been tested.


## Options

### g:enable_clighter
If enabled, Clighter will start with Vim, you can disable Clighter by set
g:enable_clighter to 0

Default: `1`
```vim
let g:enable_clighter = 0
```

### g:clighter_cursor_toggle_key

The hotkey to toggle cursor highlighting function.

Default: `'<F3>'`
```vim
let g:clighter_cursor_toggle_key = '<F3>'
```

### g:clighter_clang_options

The compiler options for libclang. Sometimes Clighter doesn't do corret
highlighting cause Clang can't parse the source code, then you need tell Clang
how to parse it. You can set the compiler options to the list in
g:clighter_clang_options.

Default: `[]`
```vim
let g:clighter_clang_options = ['-std=c++', '-DLinux']
```

### g:clighter_libclang_path

Clighter use default path to find libclang, if your libclang is not in
default path, tell Clighter by this option.

Default: `undefine`
```vim
let g:clighter_libclang_path = '/usr/lib/libclang.so'
```

## Customize Colors

Clighter defines the following syntax group corresponding to CursorKing of Clang

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
