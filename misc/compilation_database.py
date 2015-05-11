import os
import json

USEFUL_OPTS = ['-D', '-I', '-include', '-x']
USEFUL_FLAGS = ['-std']


class CompilationCommand(object):

    def __init__(self, dir, command, file):
        self.__directory = dir
        self.__command = command
        self.__file = file

    @property
    def directory(self):
        return self.__directory

    @property
    def basename(self):
        return self.__file

    @property
    def full_path(self):
        os.path.join(self.__directory, self.__file)

    @property
    def command(self):
        return self.__command

    @property
    def useful_args(self):
        args = self.__command.split()
        num = len(args)
        pos = 0

        useful_opts = []
        useful_flags = []

        while pos < num:
            useful_opt = None
            useful_flag = None

            for opt in USEFUL_OPTS:
                if args[pos].startswith(opt):
                    useful_opt = opt
                    break

            for flag in USEFUL_FLAGS:
                if args[pos].startswith(flag):
                    useful_flag = flag
                    break

            if useful_opt:
                useful_opts.append(args[pos])
                if args[pos] == useful_opt:
                    pos += 1
                    if pos < num:
                        useful_opts.append(args[pos])

            if useful_flag:
                useful_flags.append(args[pos])

            pos += 1

        return useful_flags + useful_opts


class CompilationDatabase(object):

    def __init__(self, file_path, data):
        self.__file_path = file_path
        self.__data = data
        self.__command_cache = {}

    @staticmethod
    def from_dir(dir):
        file_path = dir + '/compile_commands.json'
        json_file = open(file_path)
        data = json.load(json_file)
        json_file.close()

        if not isinstance(data, list):
            raise Exception()

        cdb = CompilationDatabase(file_path, data)
        cdb.build_command_cache()
        return cdb

    def build_command_cache(self):
        self.__command_cache = {}

        for entry in self.__data:
            if not entry.get('directory') or not entry.get(
                    'command') or not entry.get('file'):
                continue

            full_path = os.path.join(entry['directory'], entry['file'])
            if not self.__command_cache.get(full_path):
                self.__command_cache[full_path] = []

            self.__command_cache[full_path].append(
                CompilationCommand(
                    entry['directory'].encode('utf-8'),
                    entry['command'].encode('utf-8'),
                    entry['file'].encode('utf-8')))

    def get_commands(self, full_path, heuristic):
        if not heuristic:
            return self.__command_cache.get(full_path)

        basename = os.path.basename(full_path)

        all_commands = []
        for key, commands in self.__command_cache.items():
            next_basename = os.path.basename(key)

            if os.path.splitext(
                    next_basename)[0] == os.path.splitext(basename)[0]:
                if os.path.dirname(key) == os.path.dirname(full_path):
                    all_commands = commands
                    break
                else:
                    all_commands += commands

        return all_commands

    """
    to be done
    """

    def write_back(self):
        with open(self.__file_path, 'w') as json_file:
            json_file.write(json.dumps(self.__data))

    @property
    def file_path(self):
        return self.__file_path
