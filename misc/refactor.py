import vim
import string
import clighter_helper


def rename(clang_service):
    clang_service.update_buffers(__get_bufctx_list())
    clang_service.parse_all(vim.eval('g:clighter_compile_args'))

    cc = clang_service.get_cc(vim.current.buffer.name)
    if not cc:
        return

    tu = cc.current_tu
    if not tu:
        return

    symbol = clighter_helper.get_vim_symbol(
        clighter_helper.get_vim_cursor(tu))

    if not symbol:
        return

    old_name = clighter_helper.get_spelling_or_displayname(symbol)
    vim.command("echohl WildMenu")
    new_name = vim.eval(
        "input(' Rename {0} : ', '{1}')".format(old_name, old_name))
    vim.command("echohl None")

    if not new_name or old_name == new_name:
        return

    print ' '

    pos = vim.current.window.cursor

    tobeReplace = set()
    tobeReplace.add((symbol.location.line, symbol.location.column,
                     symbol.location.file.name))
    clighter_helper.search_referenced_tokens(
        tu,
        symbol,
        tobeReplace)

    prompt = string.atoi(vim.eval('g:clighter_rename_prompt_level'))

    __vim_multi_replace(
        tobeReplace,
        old_name,
        new_name,
        prompt)

    if clighter_helper.is_global_symbol(
            symbol) and vim.eval('g:clighter_enable_cross_rename') == '1':
        __cross_buffer_rename(
            clang_service,
            symbol.get_usr(),
            new_name,
            prompt)

    vim.current.window.cursor = pos

    clang_service.update_buffers(__get_bufctx_list())
    clang_service.switch(vim.current.buffer.name)


def __cross_buffer_rename(clang_service, symbol_usr, new_name, prompt):
    call_bufnr = vim.current.buffer.number

    vim.command("bn!")
    while vim.current.buffer.number != call_bufnr:
        cc = clang_service.get_cc(vim.current.buffer.name)
        if cc:
            try:
                __search_symbol_and_rename(
                    cc.current_tu, symbol_usr, new_name, prompt)
            except:
                pass

        vim.command("bn!")


def __search_symbol_and_rename(tu, symbol_usr, new_name, prompt):
    if not tu:
        return

    symbols = []
    clighter_helper.search_cursors_by_usr(tu.cursor, symbol_usr, symbols)

    if not symbols:
        return

    # all symbols with the same name
    old_name = clighter_helper.get_spelling_or_displayname(symbols[0])

    toBeReplace = set()
    for sym in symbols:
        clighter_helper.search_referenced_tokens(tu, sym, toBeReplace)

    if len(toBeReplace):
        if prompt >= 1:
            if vim.eval(
                'confirm("found symbols in {0}, rename them?", "&Yes\n&No", 1)'.format(
                    vim.current.buffer.name)) == "2":
                return

        __vim_multi_replace(
            toBeReplace,
            old_name,
            new_name,
            prompt)


def __vim_multi_replace(toBeReplace, old, new, prompt):
    if not toBeReplace:
        return

    pattern = ""

    for line, column, bufname in toBeReplace:
        if not bufname or bufname != vim.current.buffer.name:
            continue

        if pattern:
            pattern += r'\|'

        pattern += r'\%' + str(line) + 'l' + r'\%>' + str(
            column - 1) + r'c\%<' + str(column + len(old)) + 'c' + old

    if not pattern:
        return

    cmd = '%s/' + pattern + '/' + new + '/gI'

    if prompt >= 2:
        cmd = cmd + 'c'

    vim.command(cmd)


def __get_bufctx_list():
    buf_list = []

    for buf in vim.buffers:
        if not clighter_helper.is_vim_buffer_allowed(buf):
            continue

        if len(buf) == 1 and not buf[0]:
            continue

        buf_list.append(
            (buf.name,
             '\n'.join(buf),
             string.atoi(vim.eval("b:changedtick"))))

    return buf_list
