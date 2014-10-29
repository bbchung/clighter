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
    __translation_ctx = {}
    __thread = None
    __is_running = False
    __compile_arg = []

    # for internal use, to sync the parsing worker
    __change_tick = 1
    __parse_tick = 0

    __cond = threading.Condition()
    __parse_lock = threading.Lock()
    __unsaved = set()
    __idx = None

    @staticmethod
    def init(arg):
        if ClangService.__idx is None:
            try:
                ClangService.__idx = cindex.Index.create()
            except:
                return False

        if ClangService.__thread is not None:
            return True

        ClangService.__compile_arg = list(arg)

        ClangService.__is_running = True
        ClangService.__thread = threading.Thread(
            target=ClangService.__parsing_worker)
        ClangService.__thread.start()

        return True

    @staticmethod
    def set_compile_arg(arg):
        __compile_arg = arg

    @staticmethod
    def release():
        if ClangService.__thread is not None:
            ClangService.__is_running = False
            with ClangService.__cond:
                ClangService.__cond.notify()
            ClangService.__thread.join()
            ClangService.__thread = None

        ClangService.__translation_ctx.clear()

    @staticmethod
    def remove_tu(list):
        for name in list:
            if name in ClangService.__translation_ctx.keys():
                del ClangService.__translation_ctx[name]

    @staticmethod
    def create_tu(list):
        for name in list:
            if name in ClangService.__translation_ctx.keys():
                continue

            ClangService.__translation_ctx[name] = TranslationUnitCtx(name)

        ClangService.__increase_tick()

    @staticmethod
    def update_unsaved_dict(dict, increase_tick=True):
        for name, buffer in dict.items():
            for file in ClangService.__unsaved:
                if file[0] == name:
                    ClangService.__unsaved.discard(file)
                    break

            ClangService.__unsaved.add((name, buffer))

        if increase_tick:
            ClangService.__increase_tick()

    @staticmethod
    def update_unsaved(name, buffer, increase_tick=True):
        for file in ClangService.__unsaved:
            if file[0] == name:
                ClangService.__unsaved.discard(file)
                break

        ClangService.__unsaved.add((name, buffer))

        if increase_tick:
            ClangService.__increase_tick()

    @staticmethod
    def parse(tu_ctx, args):
        with ClangService.__parse_lock:
            tu_ctx.parse(
                ClangService.__idx, args, ClangService.__unsaved)

    @staticmethod
    def get_tu_ctx(name):
        return ClangService.__translation_ctx.get(name)

    @staticmethod
    def __parsing_worker():
        while ClangService.__is_running:
            try:
                # has parse all unsaved files
                if ClangService.__parse_tick == ClangService.__change_tick:
                    with ClangService.__cond:
                        ClangService.__cond.wait()

                    if ClangService.__parse_tick == ClangService.__change_tick:
                        continue

                last_change_tick = ClangService.__change_tick

                for tu_ctx in ClangService.__translation_ctx.values():
                    ClangService.parse(tu_ctx, ClangService.__compile_arg)

                ClangService.__parse_tick = last_change_tick
            except:
                pass

    @staticmethod
    def __increase_tick():
        with ClangService.__cond:
            ClangService.__change_tick += 1
            ClangService.__cond.notify()
