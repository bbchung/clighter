import os
import json

USEFUL_OPTS = ['-D', '-I', '-isystem', '-include', '-x']
USEFUL_FLAGS = ['-std']


def startswith_list(str, prefix_list):
    for prefix in prefix_list:
        if str.startswith(prefix):
            return True

    return False


class CompilationDatabase(object):

    def __init__(self, file_path, jdata, heuristic):
        self.__heuristic = heuristic
        self.__file_path = file_path
        self.__jdata = jdata
        self.__cdb_cache = {}

    @staticmethod
    def from_dir(dir, heuristic):
        file_path = dir + '/compile_commands.json'
        json_file = open(file_path)
        jdata = json.load(json_file)
        json_file.close()

        if not isinstance(jdata, list):
            raise Exception()

        cdb = CompilationDatabase(file_path, jdata, heuristic)
        # cdb.build_cdb_cache()
        return cdb

    def get_useful_args(self, abs_path):
        if not self.__cdb_cache:
            self.build_cdb_cache()

        if not self.__cdb_cache.get(abs_path):
            self.__cdb_cache[abs_path] = {'abs_path': abs_path}

        if self.__cdb_cache[abs_path].get('arg_list'):
            return self.__cdb_cache[abs_path]['arg_list']

        command = self.get_commands(abs_path)
        if not command:
            return []

        args = command.replace('\"', '').replace('\'', '').split()

        useful_opts = []
        useful_flags = []

        while (args):
            arg = args.pop(0)

            if startswith_list(arg, USEFUL_FLAGS):
                useful_flags.append(arg)
                continue

            if arg in USEFUL_OPTS:
                if args and args[0] and not args[0].startswith('-'):
                    useful_opts.append(arg)
                    useful_opts.append(args.pop(0))

                continue

            if startswith_list(arg, USEFUL_OPTS):
                useful_opts.append(arg)
                continue

        self.__cdb_cache[abs_path]['arg_list'] = useful_flags + useful_opts
        return self.__cdb_cache[abs_path]['arg_list']

    def get_commands(self, abs_path):
        if not self.__cdb_cache:
            self.build_cdb_cache()

        context = self.__cdb_cache.get(abs_path)

        if not context:
            return None

        if context.get('command'):
            return context['command']

        if not self.__heuristic:
            return None

        command = ""
        for key, value in self.__cdb_cache.iteritems():
            if os.path.splitext(
                    os.path.basename(abs_path))[0] == os.path.splitext(
                    os.path.basename(key))[0] and value.get('command'):
                if value.get('command'):
                    command += value['command']

        return command

    def clean_cdb_cache(self):
        self.__cdb_cache.clear()

    def build_cdb_cache(self):
        for entry in self.__jdata:
            if not entry.get('directory') or not entry.get(
                    'command') or not entry.get('file'):
                continue

            abs_path = os.path.join(
                entry['directory'].encode('utf-8'),
                entry['file'].encode('utf-8'))

            self.__cdb_cache[abs_path] = {
                'abs_path': abs_path,
                'command': entry['command'].encode('utf-8')}

    @property
    def file_path(self):
        return self.__file_path
