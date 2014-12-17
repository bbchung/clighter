import vim
import clighter_helper
import clang_service


def rename(clang_service):
    cc = clang_service.get_cc(vim.current.buffer.name)
    if cc is None:
        return

    clang_service.update_unsaved(__get_bufctx_list(), False)
    clang_service.parse_all()

    symbol = clighter_helper.get_vim_symbol(cc)

    if symbol is None:
        return

    old_name = clighter_helper.get_spelling_or_displayname(symbol)
    vim.command("echohl WildMenu")
    new_name = vim.bindeval(
        "input(' Rename {0} : ', '{1}')".format(old_name, old_name))
    vim.command("echohl None")

    if not new_name or old_name == new_name:
        return

    print ' '

    pos = vim.current.window.cursor

    locs = set()
    locs.add((symbol.location.line, symbol.location.column,
              symbol.location.file.name))
    clighter_helper.search_referenced_tokens(
        cc.translation_unit,
        symbol,
        locs)
    __vim_multi_replace(
        locs,
        old_name,
        new_name,
        vim.vars['clighter_rename_prompt_level'])

    if clighter_helper.is_global_symbol(
            symbol) and vim.vars['clighter_enable_cross_rename'] == 1:
        __cross_buffer_rename(clang_service, symbol.get_usr(), new_name)

    vim.current.window.cursor = pos

    clang_service.update_unsaved(__get_bufctx_list(), True)


def __cross_buffer_rename(clang_service, symbol_usr, new_name):
    call_bufnr = vim.current.buffer.number

    vim.command("bn!")
    while vim.current.buffer.number != call_bufnr:
        cc = clang_service.get_cc(vim.current.buffer.name)
        if cc is not None:
            try:
                __search_symbol_and_rename(
                    cc.translation_unit, symbol_usr, new_name)
            except:
                pass

        vim.command("bn!")


def __search_symbol_and_rename(tu, symbol_usr, new_name):
    if tu is None:
        return

    symbols = []
    clighter_helper.search_cursors_by_usr(tu.cursor, symbol_usr, symbols)

    if not symbols:
        return

    # all symbols with the same name
    old_name = clighter_helper.get_spelling_or_displayname(symbols[0])

    locs = set()
    for sym in symbols:
        clighter_helper.search_referenced_tokens(tu, sym, locs)

    if len(locs):
        if vim.vars['clighter_rename_prompt_level'] >= 1:
            if vim.bindeval(
                "confirm(\"found symbols in {0}, rename them?\", \"&Yes\n&No\", 1)".format(
                    vim.current.buffer.name)) == 2:
                return

        __vim_multi_replace(
            locs,
            old_name,
            new_name,
            vim.vars['clighter_rename_prompt_level'])


def __vim_multi_replace(locs, old, new, prompt_level):
    if locs is None:
        return

    pattern = ""

    for line, column, bufname in locs:
        if bufname is None or bufname != vim.current.buffer.name:
            continue

        if pattern:
            pattern += "\|"

        pattern += "\%" + str(line) + "l" + "\%>" + str(
            column - 1) + "c\%<" + str(column + len(old)) + "c" + old

    if not pattern:
        return

    cmd = "%s/" + pattern + "/" + new + "/gI"

    if prompt_level >= 2:
        cmd = cmd + "c"

    vim.command(cmd)


def __get_bufctx_list():
    list = []

    for buf in vim.buffers:
        if not clighter_helper.is_vim_buffer_allowed(buf):
            continue

        if len(buf) == 1 and not buf[0]:
            continue

        list.append((buf.name, '\n'.join(buf), vim.bindeval("b:changedtick")))

    return list
