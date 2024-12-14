import sys
import os
import zipfile

class VirtualFS:
    def __init__(self, zip_path):
        self.zip_file = zipfile.ZipFile(zip_path)
        self.cwd = "/"

    def cat(self, args):
        if not args:
            return "cat: missing operand"

        filepath = args[0]
        if filepath.startswith("/"):
            filepath = filepath[1:]
        else:
            filepath = os.path.normpath(os.path.join(self.cwd[1:], filepath))

        if filepath in self.zip_file.namelist() and not filepath.endswith("/"):
            try:
                with self.zip_file.open(filepath, 'r') as f:
                    content = f.read().decode('utf-8')
                return content
            except UnicodeDecodeError:
                return "cat: binary file"
        else:
            return f"cat: {args[0]}: No such file"

    def ls(self, args):
        path = self.cwd
        if args:
            path = os.path.normpath(os.path.join(self.cwd, args[0]))
        if path.startswith("/"):
            path = path[1:]

        files = []
        for name in self.zip_file.namelist():
            if name.startswith(path):
                rel_path = os.path.relpath(name, path)
                if not rel_path or (os.path.sep not in rel_path and not rel_path.endswith('/') or rel_path.count("/") == 1):
                    if name.endswith("/"):
                        files.append(rel_path.rstrip("/") + "/")
                    else:
                        files.append(rel_path)

        return "\n".join(sorted(files))

    def cd(self, args):
        if not args:
            self.cwd = "/"
            return

        new_path = args[0]

        if new_path == "..":
            if self.cwd == "/":
                return
            self.cwd = "/" + os.path.dirname(self.cwd[1:])
            if not self.cwd.endswith("/"):
                path_exists = False
                for name in self.zip_file.namelist():
                    if name == self.cwd:
                        path_exists = True
                if not path_exists:
                    self.cwd += "/"
            return

        if new_path.startswith("/"):
            target_path = new_path[1:]
        else:
            target_path = os.path.normpath(os.path.join(self.cwd[1:], new_path))

        if any(name == target_path or name.startswith(target_path + "/") for name in self.zip_file.namelist()):
            self.cwd = "/" + target_path
        else:
            return "cd: no such file or directory: " + args[0]

    def execute_command(self, command):
        cmd, *args = command.split()
        if cmd == "ls":
            return self.ls(args)
        elif cmd == "cd":
            return self.cd(args)
        elif cmd == "cat":
            return self.cat(args)
        elif cmd == "exit":
            return ""

        elif cmd == "uniq":

            if not args:  # если нет аргументов
                return "uniq: missing operand"  # ошибка ничего не ввели

            if args[0] == "-":
                input_lines = sys.stdin.readlines()
                return "\n".join(sorted(set(line.strip() for line in input_lines)))
            elif len(args) > 1:
                return "uniq: extra operand `" + args[1] + "'"
            else:
                filepath = args[0]
                if not filepath.startswith("/"):
                    filepath = os.path.normpath(os.path.join(self.cwd[1:], filepath))

                if filepath in self.zip_file.namelist() and not filepath.endswith("/"):
                    try:
                        with self.zip_file.open(filepath, 'r') as f:
                            return "\n".join(sorted({line.decode('utf-8').strip() for line in f}))
                    except UnicodeDecodeError:
                        return "uniq: " + args[0] + ": No such file"
                else:
                    return "uniq: " + args[0] + ": No such file"


        elif cmd == "tac":

            if not args:  # ничего не ввели
                return "tac: missing operand"

            elif args[0] == "-":  # ввод с клавиатуры
                lines = sys.stdin.readlines()
                return "".join(lines[::-1])
            elif len(args) > 1:
                return "tac: extra operand `" + args[1] + "'"
            else:
                filepath = args[0]
                if not filepath.startswith("/") or not filepath.startswith("/"):
                    filepath = os.path.normpath(os.path.join(self.cwd[1:], filepath))

                if filepath in self.zip_file.namelist() and not filepath.endswith("/"):
                    try:
                        with self.zip_file.open(filepath, 'r') as f:
                            lines = f.readlines()
                            decoded_lines = [line.decode("utf-8") for line in lines]
                            reversed_lines = decoded_lines[::-1]
                            return "".join(reversed_lines)
                    except UnicodeDecodeError:
                        return "tac: " + args[0] + ": No such file"
                else:
                    return "tac: " + args[0] + ": No such file"


        else:
            return f"command not found: {cmd}"




class ShellEmulator:
    def __init__(self, username, zip_path):
        self.vfs = VirtualFS(zip_path)
        self.username = username

        if "/" in self.vfs.zip_file.namelist():
            self.vfs.cd(["/"])
        else:
            first_dir = next((name for name in self.vfs.zip_file.namelist() if name.endswith("/")), None)
            if first_dir:
                self.vfs.cd([first_dir.rstrip("/")])

    def run(self):
        while True:
            command = input(f"{self.username}:{self.vfs.cwd} $ ")
            if not command.strip():
                continue

            if command.strip() == "exit":
                break
            output = self.vfs.execute_command(command)
            if output:
                print(output)


if __name__ == "__main__":
    username = "User123"
    zip_path = "test_fs.zip"

    emulator = ShellEmulator(username, zip_path)
    emulator.run()