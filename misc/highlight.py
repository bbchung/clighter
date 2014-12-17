import vim
import clighter_helper
from clang import cindex
import clang_service

SYMBOL_REF_PRI = -11
SYNTAX_PRI = -12


def clear_highlight():
    __vim_clear_match_pri(SYMBOL_REF_PRI, SYNTAX_PRI)
    highlight_window.syntactic_range = None
    highlight_window.hl_symbol = None


def clear_symbol_ref():
    __vim_clear_match_pri(SYMBOL_REF_PRI)
    highlight_window.hl_symbol = None


def highlight_window(clang_service, extend=50):
    cc = clang_service.get_cc(vim.current.buffer.name)
    if cc is None:
        clear_highlight()
        return

    tu = cc.translation_unit
    if tu is None:
        clear_highlight()
        return

    top = vim.bindeval("line('w0')")
    bottom = vim.bindeval("line('w$')")

    draw_syntax = False
    draw_symbol_ref = False

    current_tick = cc.parse_tick
    if cc.hl_tick < current_tick \
            or highlight_window.syntactic_range is None \
            or top < highlight_window.syntactic_range[0] \
            or bottom > highlight_window.syntactic_range[1]:
        draw_syntax = True
        __vim_clear_match_pri(SYNTAX_PRI)
        cc.hl_tick = current_tick

    if vim.vars["ClighterCursorHL"] == 1:
        symbol = clighter_helper.get_vim_symbol(cc)

        if highlight_window.hl_symbol is not None \
                and (symbol is None
                     or highlight_window.hl_symbol != symbol):
            __vim_clear_match_pri(SYMBOL_REF_PRI)

        if symbol is not None \
                and (highlight_window.hl_symbol is None
                     or highlight_window.hl_symbol != symbol):
            draw_symbol_ref = True

            # special case for preprocessor
            if symbol.kind.is_preprocessing() \
                    and symbol.location.file.name == vim.current.buffer.name:
                __vim_matchaddpos(
                    group='clighterCursorSymbolRef',
                    line=symbol.location.line,
                    col=symbol.location.column,
                    len=len(
                        clighter_helper.get_spelling_or_displayname(symbol)),
                    priority=SYMBOL_REF_PRI
                )

        highlight_window.hl_symbol = symbol

    if not draw_syntax and not draw_symbol_ref:
        return

    target_range = [top, bottom]

    if draw_syntax:
        buflinenr = len(vim.current.buffer)
        target_range = [
            max(top - extend, 1),
            min(bottom + extend, buflinenr)
        ]
        highlight_window.syntactic_range = target_range

    file = tu.get_file(cc.name)
    tokens = tu.get_tokens(
        extent=cindex.SourceRange.from_locations(
            cindex.SourceLocation.from_position(
                tu, file,
                line=target_range[0],
                column=1
            ),
            cindex.SourceLocation.from_position(
                tu, file,
                line=target_range[1] + 1,
                column=1
            )
        )
    )

    for t in tokens:
        """ Do semantic highlighting'
        """
        if t.kind.value != 2:
            continue

        t_cursor = cindex.Cursor.from_location(
            tu,
            cindex.SourceLocation.from_position(
                tu, file,
                t.location.line,
                t.location.column
            )
        )  # cursor under vim

        if draw_syntax:
            __draw_token(
                line=t.location.line,
                col=t.location.column,
                len=len(t.spelling),
                kind=t_cursor.kind,
                type=t_cursor.type.kind
            )

        """ Do definition/reference highlighting'
        """
        if draw_symbol_ref:
            symbol = clighter_helper.get_semantic_symbol(t_cursor)
            if symbol is not None and t.spelling == symbol.spelling and symbol == highlight_window.hl_symbol:
                __vim_matchaddpos(
                    group='clighterCursorSymbolRef',
                    line=t.location.line,
                    col=t.location.column,
                    len=len(t.spelling),
                    priority=SYMBOL_REF_PRI
                )


highlight_window.hl_symbol = None
highlight_window.syntactic_range = None


def __draw_token(line, col, len, kind, type):
    highlight_groups = vim.vars['clighter_highlight_groups']

    def draw(group):
        if group in highlight_groups:
            __vim_matchaddpos(group, line, col, len, SYNTAX_PRI)

    if kind == cindex.CursorKind.MACRO_INSTANTIATION:
        draw('clighterMacroInstantiation')
    elif kind == cindex.CursorKind.STRUCT_DECL:
        draw('clighterStructDecl')
    elif kind == cindex.CursorKind.CLASS_DECL:
        draw('clighterClassDecl')
    elif kind == cindex.CursorKind.ENUM_DECL:
        draw('clighterEnumDecl')
    elif kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
        draw('clighterEnumConstantDecl')
    elif kind == cindex.CursorKind.TYPE_REF:
        draw('clighterTypeRef')
    elif kind == cindex.CursorKind.FUNCTION_DECL:
        draw('clighterFunctionDecl')
    elif kind == cindex.CursorKind.MEMBER_REF_EXPR:
        draw('clighterMemberRefExpr')
    elif kind in (cindex.CursorKind.NAMESPACE_REF, cindex.CursorKind.NAMESPACE):
        draw('clighterNamespace')
    elif kind == cindex.CursorKind.DECL_REF_EXPR:
        if type == cindex.TypeKind.ENUM:
            draw('clighterDeclRefExprEnum')
        elif type == cindex.TypeKind.FUNCTIONPROTO:
            draw('clighterDeclRefExprCall')


def __vim_matchaddpos(group, line, col, len, priority):
    cmd = "call matchaddpos('{0}', [[{1}, {2}, {3}]], {4})"
    vim.command(cmd.format(group, line, col, len, priority))


def __vim_clear_match_pri(*priorities):
    cmd = "call s:clear_match_pri({0})"
    vim.command(cmd.format(list(priorities)))
