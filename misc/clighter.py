import vim
import clighter_helper
import clang_service
import highlight
import refactor

if vim.vars['clighter_libclang_file']:
    ClangService.set_libclang_file(vim.vars['clighter_libclang_file'])

__clang_service = clang_service.ClangService()

# def bfs(c, top, bottom, queue):
# if c.location.line >= top and c.location.line <= bottom:
#__draw_token(c)

# queue.put(c.get_children())

# while not queue.empty():
#curs = queue.get()
# for cur in curs:
# if cur.location.line >= top and cur.location.line <= bottom:
#__draw_token(cur)

# queue.put(cur.get_children())


# def dfs(cursor):
#    print cursor.location, cursor.spelling
#    for c in cursor.get_children():
#        dfs(c)

def clear_def_ref():
    highlight.clear_def_ref()

def clear_highlight():
    highlight.clear_highlight()

def highlight_window():
    highlight.highlight_window(__clang_service)


def refactor_rename():
    refactor.rename(__clang_service)


def clang_start_service():
    return __clang_service.start(eval(vim.vars["ClighterCompileArgs"]))


def clang_stop_service():
    return __clang_service.stop()


def clang_set_compile_args(args):
    __clang_service.set_compile_args(args)


def clang_create_all_tu_ctx():
    list = []
    for buf in vim.buffers:
        if clighter_helper.is_vim_buffer_allowed(buf):
            list.append(buf.name)

    __clang_service.create_tu_ctx(list)


def clang_switch_buffer():
    __clang_service.switch_buffer(vim.current.buffer.name)


def update_unsaved_if_allow():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        __clang_service.update_unsaved(
            vim.current.buffer.name, '\n'.join(vim.current.buffer))


def on_FileType():
    if clighter_helper.is_vim_buffer_allowed(vim.current.buffer):
        __clang_service.create_tu_ctx([vim.current.buffer.name])
    else:
        __clang_service.remove_tu_ctx([vim.current.buffer.name])
        clear_highlight()
