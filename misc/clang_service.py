import threading
import clang_helper
from clang import cindex


class TranslationUnitCtx:

    def __init__(self, bufname):
        self.__bufname = bufname
        self.__tu = None

    def get_cursor(self, location):
        if self.__tu is None:
            return None

        (row, col) = location
        cursor = cindex.Cursor.from_location(self.__tu, cindex.SourceLocation.from_position(
            self.__tu, self.__tu.get_file(self.__bufname), row, col + 1))

        return cursor if cursor.location.line == row and cursor.location.column <= col + 1 < cursor.location.column + len(clang_helper.get_spelling_or_displayname(cursor)) else None

    def parse(self, idx, args, unsaved):
        self.__tu = idx.parse(
            self.__bufname, args, unsaved, options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

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
        self.__translation_ctx = {}
        self.__thread = None
        self.__is_running = False
        self.__compile_args = []

        # for internal use, to sync the parsing worker
        self.__change_tick = 1
        self.__parse_tick = 0

        self.__cond = threading.Condition()
        self.__parse_lock = threading.Lock()
        self.__unsaved = set()
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

        self.__compile_args = list(arg)

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

        self.__translation_ctx.clear()

    def remove_tu(self, list):
        for name in list:
            if name in self.__translation_ctx.keys():
                del self.__translation_ctx[name]

    def create_tu(self, list):
        for name in list:
            if name in self.__translation_ctx.keys():
                continue

            self.__translation_ctx[name] = TranslationUnitCtx(name)

        self.__increase_tick()

    def update_unsaved_dict(self, dict, increase_tick=True):
        for name, buffer in dict.items():
            for file in self.__unsaved:
                if file[0] == name:
                    self.__unsaved.discard(file)
                    break

            self.__unsaved.add((name, buffer))

        if increase_tick:
            self.__increase_tick()

    def update_unsaved(self, name, buffer, increase_tick=True):
        for file in self.__unsaved:
            if file[0] == name:
                self.__unsaved.discard(file)
                break

        self.__unsaved.add((name, buffer))

        if increase_tick:
            self.__increase_tick()

    def parse(self, tu_ctx):
        with self.__parse_lock:
            tu_ctx.parse(
                self.__idx, self.__compile_args, self.__unsaved)

    def get_tu_ctx(self, name):
        return self.__translation_ctx.get(name)

    def __parsing_worker(self):
        while self.__is_running:
            try:
                # has parse all unsaved files
                if self.__parse_tick == self.__change_tick:
                    with self.__cond:
                        self.__cond.wait()

                    if self.__parse_tick == self.__change_tick:
                        continue

                last_change_tick = self.__change_tick

                for tu_ctx in self.__translation_ctx.values():
                    self.parse(tu_ctx)

                self.__parse_tick = last_change_tick
            except:
                pass

    def __increase_tick(self):
        with self.__cond:
            self.__change_tick += 1
            self.__cond.notify()
