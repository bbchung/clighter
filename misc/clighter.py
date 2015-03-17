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


def clang_switch_to_current():
    clang_service.ClangService().switch(vim.current.buffer.name)

    if vim.current.window.vars.get('clighter_hl') is None:
        vim.current.window.vars['clighter_hl'] = [
            -1, [], []]  # [hl_tick, syntax_range, symbol_range]
    else:
        vim.current.window.vars['clighter_hl'][0] = -1


def update_buffer_if_allow():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        clang_service.ClangService().update_buffers(
            [(vim.current.buffer.name,
              '\n'.join(vim.current.buffer),
              string.atoi(vim.eval('b:changedtick')))])


def show_information():
    print "Enable clighter: %s" % ('Enable' if vim.eval('s:clang_initialized') == '1' else 'Disable')
    print "Current context: %s" % (clang_service.ClangService().current_cc.name if clang_service.ClangService().current_cc else '')
    print "Highlight occurrences: %s" % ('On' if vim.eval('g:ClighterOccurrences') == '1' else 'Off')
    print "Compilation database: %s" % (clang_service.ClangService().compilation_database.file_path)
    print "Compile args: %s" % (' '.join(clang_service.ClangService().current_cc.compile_args) if clang_service.ClangService().current_cc and clang_service.ClangService().current_cc.compile_args else '')
