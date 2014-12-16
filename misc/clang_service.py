import threading
from clang import cindex


class BufCtx:

    def __init__(self, bufname):

        self.__bufname = bufname
        self.__tu = None
        self.buffer = None
        self.change_tick = 0
        self.parse_tick = -1
        self.hl_tick = -1

    def get_cursor(self, row, col):
        tu = self.__tu

        if self.__tu is None:
            return None

        cursor = cindex.Cursor.from_location(
            tu,
            cindex.SourceLocation.from_position(
                tu,
                tu.get_file(self.__bufname),
                row,
                col + 1))

        return cursor

    def parse(self, idx, args, unsaved, tick):
        self.parse_tick = tick
        self.__tu = idx.parse(
            self.__bufname,
            args,
            unsaved,
            options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

    @property
    def bufname(self):
        return self.__bufname

    @property
    def translation_unit(self):
        return self.__tu


class ClangService:
    __has_set_libclang = False

    @staticmethod
    def set_libclang_file(libclang):
        if ClangService.__has_set_libclang:
            return

        cindex.Config.set_library_file(libclang)
        ClangService.__has_set_libclang = True

    def __init__(self):
        self.__current_buf_ctx = None
        self.__buf_ctx = {}
        self.__thread = None
        self.__is_running = False
        self.__compile_args = []
        self.__cond = threading.Condition()
        self.__libclang_lock = threading.Lock()
        self.__idx = None

    def set_compile_args(self, args):
        self.__compile_args = args

    def start(self, arg):
        if self.__idx is None:
            try:
                self.__idx = cindex.Index.create()
            except:
                return False

        if self.__thread is not None:
            return True

        self.__compile_args = arg

        self.__is_running = True
        self.__thread = threading.Thread(target=self.__parsing_worker)
        self.__thread.start()

        return True

    def stop(self):
        if self.__thread is not None:
            self.__is_running = False
            with self.__cond:
                self.__cond.notify()
            self.__thread.join()
            self.__thread = None

        self.__buf_ctx.clear()

    def unreg_buffers(self, list):
        for bufname in list:
            if bufname in self.__buf_ctx.keys():
                del self.__buf_ctx[bufname]

    def reg_buffers(self, list):
        for bufname in list:
            if bufname in self.__buf_ctx.keys():
                continue

            self.__buf_ctx[bufname] = BufCtx(bufname)

    def update_unsaved(self, buf_list, notify=True):
        for bufname, buffer, tick in buf_list:
            self.__buf_ctx[bufname].buffer = buffer
            self.__buf_ctx[bufname].change_tick = tick

        if notify:
            with self.__cond:
                self.__cond.notify()

    def switch_buffer(self, bufname):
        buf_ctx = self.__buf_ctx.get(bufname)
        if buf_ctx is None:
            return

        buf_ctx.hl_tick = -1
        self.__current_buf_ctx = buf_ctx
        with self.__cond:
            self.__cond.notify()

    def parse(self, buf_ctx):
        current_tick = buf_ctx.change_tick

        try:
            unsaved = self.__get_unsaved_list()
        except:
            return False

        with self.__libclang_lock:
            buf_ctx.parse(
                self.__idx, self.__compile_args, unsaved, current_tick)

        return True

    def parse_all(self):
        try:
            tick = {}
            for buf_ctx in self.__buf_ctx.values():
                tick[buf_ctx.bufname] = buf_ctx.change_tick

            unsaved = self.__get_unsaved_list()

            for buf_ctx in self.__buf_ctx.values():
                with self.__libclang_lock:
                    buf_ctx.parse(
                        self.__idx,
                        self.__compile_args,
                        unsaved,
                        tick[buf_ctx.bufname])
        except:
            return False

        return True

    def get_buf_ctx(self, name):
        return self.__buf_ctx.get(name)

    def __get_unsaved_list(self):
        unsaved = []
        for buf_ctx in self.__buf_ctx.values():
            if buf_ctx.buffer is not None:
                unsaved.append((buf_ctx.bufname, buf_ctx.buffer))

        return unsaved

    def __parsing_worker(self):
        while self.__is_running:
            buf_ctx = self.__current_buf_ctx

            if buf_ctx is None:
                continue

            if buf_ctx.parse_tick == buf_ctx.change_tick:
                with self.__cond:
                    self.__cond.wait()

                if buf_ctx.parse_tick == buf_ctx.change_tick:
                    continue

            if not self.parse(buf_ctx):
                continue
