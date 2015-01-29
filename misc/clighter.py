import vim
from clang import cindex
import string
import clighter_helper
import clang_service
import highlighting


def on_FileType():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        clang_service.ClangService().register([vim.current.buffer.name])
        clang_service.ClangService().switch(vim.current.buffer.name)
    else:
        clang_service.ClangService().unregister([vim.current.buffer.name])
        highlighting.clear_highlight()


def register_allowed_buffers():
    list = []
    for buf in vim.buffers:
        if clighter_helper.is_vim_buffer_allowed(buf):
            list.append(buf.name)

    clang_service.ClangService().register(list)


def clang_switch_to_current():
    clang_service.ClangService().switch(vim.current.buffer.name)
    vim.current.window.vars['hl_tick'] = -1


def update_buffer_if_allow():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        clang_service.ClangService().update_buffers(
            [(vim.current.buffer.name,
              '\n'.join(vim.current.buffer),
              string.atoi(vim.eval('b:changedtick')))])
