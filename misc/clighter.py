import vim
import string
import clighter_helper
import clang_service
import highlighting


def on_filetype():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        clang_service.ClangService().register([vim.current.buffer.name])
    else:
        clang_service.ClangService().unregister([vim.current.buffer.name])

    clang_service.ClangService().switch(vim.current.buffer.name)
    highlighting.clear_all()


def register_allowed_buffers():
    tobe_reg = set()
    for buf in vim.buffers:
        if clighter_helper.is_vim_buffer_allowed(buf):
            tobe_reg.add(buf.name)

    clang_service.ClangService().register(tobe_reg)


def update_buffer_if_allow():
    if not clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        return

    clang_service.ClangService().update_buffers(
        [(vim.current.buffer.name,
          '\n'.join(vim.current.buffer),
          string.atoi(vim.eval('b:changedtick')))])

    clang_service.ClangService().switch(vim.current.buffer.name)


def get_vim_cursor_info():
    cc = clang_service.ClangService().get_cc(vim.current.buffer.name)
    if not cc:
        return None

    tu = cc.current_tu
    if not tu:
        return None

    vim_cursor = clighter_helper.get_vim_cursor(tu)

    if vim_cursor:
        return vim_cursor.kind, vim_cursor.type.kind, vim_cursor.spelling
    else:
        return None


def show_information():
    cc = clang_service.ClangService().get_cc(vim.current.buffer.name)

    print "Enable clighter: %s" % ('Enable' if vim.eval('s:clighter_enabled') == '1' else 'Disable')
    print "Current context: %s" % (cc.name if cc else None)
    print "Highlight occurrences: %s" % ('On' if vim.eval('g:ClighterOccurrences') == '1' else 'Off')
    print "Compilation database: %s" % ((clang_service.ClangService().compilation_database.file_path) if clang_service.ClangService().compilation_database else None)
    print "Compile args: ", cc.compile_args if cc else None
    print 'Cursor info:', get_vim_cursor_info()
