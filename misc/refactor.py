import vim
import clighter_helper
import clang_service


def rename(clang_service):
    tu_ctx = clang_service.get_tu_ctx(vim.current.buffer.name)
    if tu_ctx is None:
        return

    clang_service.update_unsaved_dict(__get_buffer_dict(), False)
    clang_service.parse_all()

    vim_cursor, def_cursor = clighter_helper.get_vim_cursor_and_def(tu_ctx)

    if vim_cursor is None or def_cursor is None:
        return

    old_name = clighter_helper.get_spelling_or_displayname(def_cursor)
    vim.command("echohl WildMenu")
    new_name = vim.bindeval(
        "input(' Rename {0} : ', '{1}')".format(old_name, old_name))
    vim.command("echohl None")

    if not new_name or old_name == new_name:
        return

    print ' '

    pos = vim.current.window.cursor

    locs = set()
    locs.add((def_cursor.location.line, def_cursor.location.column,
              def_cursor.location.file.name))
    clighter_helper.search_ref_tokens(tu_ctx.translation_unit, def_cursor, locs)
    __vim_multi_replace(locs, old_name, new_name)

    if clighter_helper.is_symbol_cursor(def_cursor) and vim.vars['clighter_enable_cross_rename'] == 1:
        __cross_buffer_rename(clang_service, def_cursor.get_usr(), new_name)

    vim.current.window.cursor = pos

    clang_service.update_unsaved_dict(__get_buffer_dict(), True)


def __cross_buffer_rename(clang_service, usr, new_name):
    call_bufnr = vim.current.buffer.number

    vim.command("bn!")
    while vim.current.buffer.number != call_bufnr:
        tu_ctx = clang_service.get_tu_ctx(vim.current.buffer.name)
        if tu_ctx is not None:
            try:
                __search_usr_and_rename_refs(
                    tu_ctx.translation_unit, usr, new_name)
            except:
                pass

        vim.command("bn!")


def __search_usr_and_rename_refs(tu, usr, new_name):
    if tu is None:
        return

    symbols = []
    clighter_helper.find_cursors_by_usr(tu.cursor, usr, symbols)

    if not symbols:
        return

    # all symbols with the same name
    old_name = clighter_helper.get_spelling_or_displayname(symbols[0])

    locs = set()
    for sym in symbols:
        clighter_helper.search_ref_tokens(tu, sym, locs)

    if len(locs):
        if vim.vars['clighter_rename_prompt_level'] >= 1:
            cmd = "let l:choice = confirm(\"found symbols in {0}, rename them?\", \"&Yes\n&No\", 1)".format(
                vim.current.buffer.name)
            vim.command(cmd)

            if vim.bindeval('l:choice') == 2:
                return

        __vim_multi_replace(locs, old_name, new_name)


def __vim_multi_replace(locs, old, new):
    if locs is None:
        return

    pattern = ""

    for line, column, file in locs:
        if file is None or file != vim.current.buffer.name:
            continue

        if pattern:
            pattern += "\|"

        pattern += "\%" + str(line) + "l" + "\%>" + str(
            column - 1) + "c\%<" + str(column + len(old)) + "c" + old

    if not pattern:
        return

    cmd = "%s/" + pattern + "/" + new + "/gI"

    if vim.vars['clighter_rename_prompt_level'] >= 2:
        cmd = cmd + "c"

    vim.command(cmd)


def __get_buffer_dict():
    dict = {}

    for buf in vim.buffers:
        if not clighter_helper.is_vim_buffer_allowed(buf):
            continue

        if len(buf) == 1 and not buf[0]:
            continue

        dict[buf.name] = '\n'.join(buf)

    return dict
