import threading
from clang import cindex


class ClangContext(object):

    def __init__(self, name):

        self.__name = name
        self.__buffer = None
        self.__translation_unit = None
        self.__change_tick = 0
        self.__parse_tick = -1
        self.__hl_tick = -1

    def update_buffer(self, buffer, tick):
        self.__buffer = buffer
        self.__change_tick = tick

    def get_cursor(self, row, col):
        tu = self.__translation_unit

        if tu is None:
            return None

        return cindex.Cursor.from_location(
            tu,
            cindex.SourceLocation.from_position(
                tu,
                tu.get_file(self.__name),
                row,
                col + 1))

    def parse(self, idx, args, unsaved, tick):
        self.__translation_unit = idx.parse(
            self.__name,
            args,
            unsaved,
            options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
        self.__parse_tick = tick

    @property
    def name(self):
        return self.__name

    @property
    def buffer(self):
        return self.__buffer

    @property
    def change_tick(self):
        return self.__change_tick

    @property
    def translation_unit(self):
        return self.__translation_unit

    @property
    def parse_tick(self):
        return self.__parse_tick

    @parse_tick.setter
    def parse_tick(self, value):
        self.__parse_tick = value

    @property
    def hl_tick(self):
        return self.__hl_tick

    @hl_tick.setter
    def hl_tick(self, value):
        self.__hl_tick = value


class ClangService(object):

    @staticmethod
    def set_libclang_file(libclang):
        cindex.Config.set_library_file(libclang)

    def __init__(self):
        self.__current_cc = None
        self.__cc_dict = {}
        self.__parsing_thread = None
        self.__is_running = False
        self.__compile_args = []
        self.__cond = threading.Condition()
        self.__libclang_lock = threading.Lock()
        self.__cindex = None

    def start(self, arg):
        if self.__cindex is None:
            try:
                self.__cindex = cindex.Index.create()
            except:
                return False

        if self.__parsing_thread is not None:
            return True

        self.__compile_args = arg

        self.__is_running = True
        self.__parsing_thread = threading.Thread(target=self.__parsing_worker)
        self.__parsing_thread.start()

        return True

    def stop(self):
        if self.__parsing_thread is not None:
            self.__is_running = False
            with self.__cond:
                self.__cond.notify()
            self.__parsing_thread.join()
            self.__parsing_thread = None

        self.__cc_dict.clear()

    def unregister(self, list):
        for name in list:
            if name in self.__cc_dict.keys():
                del self.__cc_dict[name]

    def register(self, list):
        for name in list:
            if name in self.__cc_dict.keys():
                continue

            self.__cc_dict[name] = ClangContext(name)

    def update_buffers(self, update_list, notify=True):
        for name, buffer, tick in update_list:
            cc = self.__cc_dict.get(name)
            if cc is None:
                continue

            cc.update_buffer(buffer, tick)

        if notify:
            with self.__cond:
                self.__cond.notify()

    def switch(self, name):
        cc = self.__cc_dict.get(name)
        if cc is None:
            return

        cc.parse_tick = -1
        cc.hl_tick = -1
        self.__current_cc = cc
        with self.__cond:
            self.__cond.notify()

    def parse_cc(self, cc):
        tick = cc.change_tick

        try:
            unsaved = self.__gen_unsaved()
        except:
            return False

        with self.__libclang_lock:
            cc.parse(
                self.__cindex, self.__compile_args, unsaved, tick)

        return True

    def parse_all(self):
        try:
            tick = {}
            for cc in self.__cc_dict.values():
                tick[cc.name] = cc.change_tick

            unsaved = self.__gen_unsaved()

            for cc in self.__cc_dict.values():
                with self.__libclang_lock:
                    cc.parse(
                        self.__cindex,
                        self.__compile_args,
                        unsaved,
                        tick[cc.name])
        except:
            return False

        return True

    def get_cc(self, name):
        return self.__cc_dict.get(name)

    def __gen_unsaved(self):
        unsaved = []
        for cc in self.__cc_dict.values():
            if cc.buffer is not None:
                unsaved.append((cc.name, cc.buffer))

        return unsaved

    def __parsing_worker(self):
        while self.__is_running:
            cc = self.__current_cc

            if cc is None:
                continue

            if cc.parse_tick == cc.change_tick:
                with self.__cond:
                    self.__cond.wait()

                if cc.parse_tick == cc.change_tick:
                    continue

            self.parse_cc(cc)

    @property
    def compile_args(self):
        return self.__compile_args

    @compile_args.setter
    def compile_args(self, value):
        self.__compile_args = value
