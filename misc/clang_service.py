import threading
from clang import cindex
import compilation_database


class ClangContext(object):

    def __init__(self, name):

        self.__name = name
        self.__tu_tick = [None, -1]
        self.__buffer_tick = [None, 0]

        self.compile_args = None

    def update_buffer(self, buf, tick):
        self.__buffer_tick = [buf, tick]

    def parse(self, idx, args, unsaved, tick):
        try:
            tu = idx.parse(
                self.__name,
                args,
                unsaved,
                options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
        except:
            tu = None
        finally:
            self.__tu_tick = [tu, tick]

    @property
    def name(self):
        return self.__name

    @property
    def buffer(self):
        return self.__buffer_tick[0]

    @property
    def change_tick(self):
        return self.__buffer_tick[1]

    @property
    def current_tu(self):
        return self.__tu_tick[0]

    @property
    def parse_tick(self):
        return self.__tu_tick[1]

    @parse_tick.setter
    def parse_tick(self, value):
        self.__tu_tick[1] = value


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton,
                cls).__call__(*args,
                              **kwargs)
        return cls._instances[cls]


class ClangService(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.__current_cc = None
        self.__cc_dict = {}
        self.__parsing_thread = None
        self.__is_running = False
        self.__cond = threading.Condition()
        self.__cindex = None
        self.__cdb = None

    def __del__(self):
        self.stop()

    def __get_useful_args(self, cc, heuristic):
        if cc.compile_args is not None:
            return cc.compile_args

        cc.compile_args = []

        if not self.__cdb:
            return None

        ccmds = self.__cdb.get_commands(cc.name, False)

        if not ccmds and heuristic:
            ccmds = self.__cdb.get_commands(cc.name, True)

        if ccmds:
            # if there is more than one commands, take the first one
            cc.compile_args = ccmds[0].useful_args

        return cc.compile_args

    def start(self, cdb_dir, heuristic):
        if not self.__cindex:
            try:
                self.__cindex = cindex.Index.create()
            except:
                return False

        if self.__parsing_thread:
            return True

        if cdb_dir:
            try:
                self.__cdb = compilation_database.CompilationDatabase.from_dir(
                    cdb_dir)
            except:
                pass

        self.__is_running = True
        self.__parsing_thread = threading.Thread(
            target=self.__parsing_worker,
            args=(
                heuristic,
            ))
        self.__parsing_thread.start()

        return True

    def stop(self):
        if self.__parsing_thread:
            self.__is_running = False
            with self.__cond:
                self.__cond.notify()
            self.__parsing_thread.join()
            self.__parsing_thread = None

        self.__cc_dict.clear()
        self.__cindex = None

    def unregister(self, unreg_list):
        for name in unreg_list:
            if name in self.__cc_dict.keys():
                del self.__cc_dict[name]

    def register(self, tobe_reg):
        for name in tobe_reg:
            if name in self.__cc_dict.keys():
                continue

            self.__cc_dict[name] = ClangContext(name)

    def update_buffers(self, update_list, notify=True):
        for name, buf, tick in update_list:
            cc = self.__cc_dict.get(name)
            if not cc:
                continue

            cc.update_buffer(buf, tick)

        if notify:
            with self.__cond:
                self.__cond.notify()

    def switch(self, name):
        self.__current_cc = self.__cc_dict.get(name)

        if self.__current_cc:
            self.__current_cc.parse_tick = -1

        with self.__cond:
            self.__cond.notify()

    def get_cc(self, name):
        return self.__cc_dict.get(name)

    def parse_all(self, heuristic):
        tick = {}
        for cc in self.__cc_dict.values():
            tick[cc.name] = cc.change_tick

        unsaved = self.__gen_unsaved()

        for cc in self.__cc_dict.values():
            cc.parse(
                self.__cindex,
                self.__get_useful_args(cc, heuristic),
                unsaved,
                tick[cc.name])

    def __gen_unsaved(self):
        unsaved = []
        for cc in self.__cc_dict.values():
            buf = cc.buffer

            if buf:
                unsaved.append((cc.name, buf))

        return unsaved

    def __parsing_worker(self, heuristic):
        while self.__is_running:
            cc = self.__current_cc

            if not cc:
                with self.__cond:
                    self.__cond.wait()

                continue

            if cc.parse_tick == cc.change_tick:
                with self.__cond:
                    self.__cond.wait()

                if cc.parse_tick == cc.change_tick:
                    continue

            try:
                tick = cc.change_tick
                unsaved = self.__gen_unsaved()
            except:
                pass

            cc.parse(
                self.__cindex,
                self.__get_useful_args(cc, heuristic),
                unsaved,
                tick)

    @property
    def current_cc(self):
        return self.__current_cc

    @property
    def compilation_database(self):
        return self.__cdb
