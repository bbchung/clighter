import vim
import string
import clighter_helper
import clang_service
import highlight
import refactor


libclang_file = vim.eval('g:clighter_libclang_file')
if libclang_file:
    clang_service.ClangService.set_libclang_file(
        libclang_file)

__clang_service = clang_service.ClangService()

# def bfs(c, top, bottom, queue):
# if c.location.line >= top and c.location.line <= bottom:
#__draw_token(c)

# queue.put(c.get_children())

# while not queue.empty():
# curs = queue.get()
# for cur in curs:
# if cur.location.line >= top and cur.location.line <= bottom:
#__draw_token(cur)

# queue.put(cur.get_children())


# def dfs(cursor):
#    print cursor.location, cursor.spelling
#    for c in cursor.get_children():
#        dfs(c)

def clear_symbol_ref():
    highlight.clear_symbol_ref()


def clear_highlight():
    highlight.clear_highlight()


def highlight_window():
    highlight.highlight_window(__clang_service)


def refactor_rename():
    refactor.rename(__clang_service)


def on_FileType():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        register_buffer(vim.current.buffer.name)
        __clang_service.switch(vim.current.buffer.name)
    else:
        unregister_buffer(vim.current.buffer.name)
        clear_highlight()


def register_buffer(bufname):
    __clang_service.register([bufname])


def register_allowed_buffers():
    list = []
    for buf in vim.buffers:
        if clighter_helper.is_vim_buffer_allowed(buf):
            list.append(buf.name)

    __clang_service.register(list)


def unregister_buffer(bufname):
    __clang_service.unregister([bufname])


def clang_start_service():
    return __clang_service.start(vim.eval('g:ClighterCompileArgs'))


def clang_stop_service():
    return __clang_service.stop()


def clang_set_compile_args(args):
    __clang_service.compile_args = list(args)  # list() is need to copy


def clang_switch_to_current():
    __clang_service.switch(vim.current.buffer.name)
    vim.current.window.vars['hl_tick'] = -1


def update_buffer_if_allow():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        __clang_service.update_buffers(
            [(vim.current.buffer.name,
              '\n'.join(vim.current.buffer),
              string.atoi(vim.eval('b:changedtick')))])
