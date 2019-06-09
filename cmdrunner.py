import argparse
import json
import os
import re
import readline
import sys

from lib.base import InteractiveCmd, CmdRunnerException, CmdRunner, CmdEncoder, CmdDecoder, execute
import lib.utils
from lib.runners import *
from lib.encoders import *
from lib.decoders import *


class HelpCmd(InteractiveCmd):
    tag = "help"

    @classmethod
    def run(cls, args, session):
        cmd = args.strip().lstrip("$")
        if len(cmd):
            try:
                cls = InteractiveCmd.get_command(cmd)
                print("Help for command ${}".format(cls.tag))
                print("\n".join("\t" + x for x in cls.get_help().splitlines()))
            except CmdRunnerException as e:
                print(str(e))
            return
        print("Available commands:")
        for icmd in InteractiveCmd.get_subclasses():
            if icmd == cls:
                continue
            print("\t{:20s} {}".format(icmd.tag, icmd.description))

class PrintSessionCmd(InteractiveCmd):
    tag = "print_session"
    description = "Print session information"
    help = """
        Print session information.
    """

    @classmethod
    def run(cls, args, session):
        print("Runner:")
        print("\n".join("\t{}".format(x) for x in session["runner"].get_instance().splitlines()))
        if len(session["encoders"]):
            print("Encoders:")
            for index, encoder in enumerate(session["encoders"]):
                print("[{}]: {}".format(index, "\n".join("\t{}".format(x) for x in encoder.get_instance().splitlines())))
        if len(session["decoders"]):
            print("Decoders:")
            for index, decoder in enumerate(session["decoders"]):
                print("[{}]: {}".format(index, "\n".join("\t{}".format(x) for x in decoder.get_instance().splitlines())))

class LoadSessionCmd(InteractiveCmd):
    tag = "load_session"
    description = "Load session from saved json file"
    help = """
        Load session data from saved json file.
            $load_session <session_file>
    """

    @classmethod
    def run(cls, args, session):
        session_file = args.strip()
        if len(session_file) == 0:
            raise CmdRunnerException("$load_session requires <session_file> argument")
        if not os.path.isfile(session_file):
            raise CmdRunnerException("Session file '{}' does not exist".format(session_file))
        with open(session_file) as f:
            _session = json.load(f)
        available_runners = {x.__name__ : x for x in CmdRunner.get_subclasses()}
        available_encoders = {x.__name__ : x for x in CmdEncoder.get_subclasses()}
        available_decoders = {x.__name__ : x for x in CmdDecoder.get_subclasses()}
        try:
            runner = available_runners[_session["runner"]["__classname__"]].load(_session["runner"])
            encoders = [available_encoders[x["__classname__"]].load(x) for x in _session["encoders"]]
            decoders = [available_decoders[x["__classname__"]].load(x) for x in _session["decoders"]]
        except KeyError:
            raise CmdRunnerException("Invalid session")
        session["runner"] = runner
        session["encoders"] = encoders
        session["decoders"] = decoders
        PrintSessionCmd.run(None, session)

class SaveSessionCmd(InteractiveCmd):
    tag = "save_session"
    description = "Save session data to json file"
    help = """
        Save session data to json file.
            $save_session <session_file>
    """

    @classmethod
    def run(cls, args, session):
        session_file = args.strip()
        if len(session_file) == 0:
            raise CmdRunnerException("$save_session requires <session_files> argument")
        _session = {
          "runner" : session["runner"].save(),
          "encoders" : [x.save() for x in session["encoders"]],
          "decoders" : [x.save() for x in session["decoders"]],
        }
        with open(session_file, "w") as f:
            json.dump(_session, f)

class ListRunnersCmd(InteractiveCmd):
    tag = "list_runners"
    description = "List available command runners"
    help = """
        List available command runners.
    """

    @classmethod
    def run(cls, args, session):
        print("Runners:")
        for runner in sorted(CmdRunner.get_subclasses(), key=lambda x: x.__name__):
            print("\t{}".format(runner.__name__))

class ListEncodersCmd(InteractiveCmd):
    tag = "list_encoders"
    description = "List available command encoders"
    help = """
        List available command encoders.
    """

    @classmethod
    def run(cls, args, session):
        print("Encoders:")
        for encoder in sorted(CmdEncoder.get_subclasses(), key=lambda x: x.__name__):
            print("\t{}".format(encoder.__name__))

class ListDecodersCmd(InteractiveCmd):
    tag = "list_decoders"
    description = "List available output decoders"
    help = """
        List available output decoders.
    """

    @classmethod
    def run(cls, args, session):
        print("Decoders:")
        for decoder in sorted(CmdDecoder.get_subclasses(), key=lambda x: x.__name__):
            print("\t{}".format(decoder.__name__))

class PushEncoder(InteractiveCmd):
    tag = "push_encoder"
    description = "Add an encoder to the encoders list"
    help = """
        Add an encoder to the encoders list.
            $push_encoder [index] <encoder_name> [encoder_arguments]

        Encoder arguments should be supplied in either a json form (e.g. {"key" : "value"})
        or a python funcion call form (e.g. (1, 2, key="value")).
    """

    @classmethod
    def run(cls, args, session):
        available_encoders = {x.__name__.lower() : x for x in CmdEncoder.get_subclasses()}
        match = re.match("([0-9]+)? *([A-Za-z0-9_]+)(.*)", args)
        if match is None:
            raise CmdRunnerException("$push_encoder requires arguments: [index] <encoder_name> [encoder_arguments]")

        index, encoder_arg, args = match.groups()
        index = int(index) if index is not None else len(session["encoders"])
        encoder_cls = available_encoders.get(encoder_arg.lower(), available_encoders.get(encoder_arg.lower() + "encoder"))
        args = args.strip()

        if encoder_cls is None:
            raise CmdRunnerException("Unknown encoder '{}'".format(encoder_arg))

        try:
            if args.startswith("(") and args.endswith(")"):
                try:
                    args, kwargs = lib.utils.get_args(args[1:-1])
                    encoder = encoder_cls(*args, **kwargs)
                except lib.utils.ArgsException as e:
                    raise CmdRunnerException(str(e))
            elif args.startswith("{") and args.endswith("}"):
                try:
                    encoder = encoder_cls(**json.loads(args))
                except json.decoder.JSONDecodeError:
                    raise CmdRunnerException("Invalid json arguments")
            elif len(args):
                raise CmdRunnerException("Invalid arguments '{}'".format(args))
            else:
                encoder = encoder_cls()
        except TypeError as e:
            raise CmdRunnerException("{}\n{}".format(e, encoder_cls.get_help()))
        session["encoders"].insert(index, encoder)

class PopEncoder(InteractiveCmd):
    tag = "pop_encoder"
    description = "Remove encoder from encoders list"
    help = """
        Remove encoder from encoders list.
            $pop_encoder <index>
    """

    @classmethod
    def run(cls, args, session):
        if len(args.strip()) > 0:
            try:
                index = int(args.strip())
            except ValueError:
                raise CmdRunnerException("Invalid index '{}'".format(args))
        else:
            index = -1
        if index >= len(session["encoders"]):
            raise CmdRunnerException("Invalid index '{}' for encoder list length {}".format(args, len(session["encoders"])))
        session["encoders"].pop(index)

class PushDecoder(InteractiveCmd):
    tag = "push_decoder"
    description = "Add a decoder to the decoders list"
    help = """
        Add a decoder to the decoders list.
            $push_decoder [index] <decoder_name> [decoder_arguments]

        Decoder arguments should be supplied in either a json form (e.g. {"key" : "value"})
        or a python funcion call form (e.g. (1, 2, key="value")).
    """

    @classmethod
    def run(cls, args, session):
        available_decoders = {x.__name__.lower() : x for x in CmdDecoder.get_subclasses()}
        match = re.match("([0-9]+)? *([A-Za-z0-9_]+)(.*)", args)
        if match is None:
            raise CmdRunnerException("$push_decoder requires arguments: [index] <decoder_name> [decoder_arguments]")

        index, decoder_arg, args = match.groups()
        index = int(index) if index is not None else len(session["decoders"])
        decoder_cls = available_decoders.get(decoder_arg.lower(), available_decoders.get(decoder_arg.lower() + "decoder"))
        args = args.strip()

        if decoder_cls is None:
            raise CmdRunnerException("Unknown decoder '{}'".format(decoder_arg))

        try:
            if args.startswith("(") and args.endswith(")"):
                try:
                    args, kwargs = lib.utils.get_args(args[1:-1])
                    decoder = decoder_cls(*args, **kwargs)
                except lib.utils.ArgsException as e:
                    raise CmdRunnerException(str(e))
            elif args.startswith("{") and args.endswith("}"):
                try:
                    decoder = decoder_cls(**json.loads(args))
                except json.decoder.JSONDecodeError:
                    raise CmdRunnerException("Invalid json arguments")
            elif len(args):
                raise CmdRunnerException("Invalid arguments '{}'".format(args))
            else:
                decoder = decoder_cls()
        except TypeError as e:
            raise CmdRunnerException("{}\n{}".format(e, decoder_cls.get_help()))
        session["decoders"].insert(index, decoder)

class PopDecoder(InteractiveCmd):
    tag = "pop_decoder"
    description = "Remove decoder from decoders list"
    help = """
        Remove decoder from decoders list.
            $pop_decoder <index>
    """

    @classmethod
    def run(cls, args, session):
        if len(args.strip()) > 0:
            try:
                index = int(args.strip())
            except ValueError:
                raise CmdRunnerException("Invalid index '{}'".format(args))
        else:
            index = -1
        if index >= len(session["decoders"]):
            raise CmdRunnerException("Invalid index '{}' for decoder list length {}".format(args, len(session["decoders"])))
        session["decoders"].pop(index)

class SetRunner(InteractiveCmd):
    tag = "set_runner"
    description = "Set the command runner"
    help = """
        Set the command runner.
            $set_runner <runner_name> [runner_arguments]

        Runner arguments should be supplied in either a json form (e.g. {"key" : "value"})
        or a python funcion call form (e.g. (1, 2, key="value")).
    """

    @classmethod
    def run(cls, args, session):
        available_runners = {x.__name__.lower() : x for x in CmdRunner.get_subclasses()}
        match = re.match("([A-Za-z0-9_]+)(.*)", args.strip())
        if match is None:
            raise CmdRunnerException("$set_runner requires arguments: <runner_name> [runner_arguments]")
        runner_arg, args = match.groups()
        args = args.strip()

        if not runner_arg.lower() in available_runners:
            raise CmdRunnerException("'{}' is not a valid runner".format(runner_arg))
        runner_cls = available_runners[runner_arg.lower()]

        try:
            if args.startswith("(") and args.endswith(")"):
                try:
                    args, kwargs = lib.utils.get_args(args[1:-1])
                    runner = runner_cls(*args, **kwargs)
                except lib.utils.ArgsException as e:
                    raise CmdRunnerException(str(e))
            elif args.startswith("{") and args.endswith("}"):
                try:
                    runner = runner_cls(**json.loads(args))
                except json.decoder.JSONDecodeError:
                    raise CmdRunnerException("Invalid json arguments")
            elif len(args):
                raise CmdRunnerException("Invalid arguments '{}'".format(args))
            else:
                runner = runner_cls()
        except TypeError as e:
            raise CmdRunnerException("{}\n{}".format(e, runner_cls.get_help()))
        session["runner"] = runner

class QuitCmd(InteractiveCmd):
    tag = "quit"
    description = "Quit CmdRunner"
    help = "Quit CmdRunner"

    @classmethod
    def run(cls, args, session):
        print("Quitting...")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="cmdrunner")
    parser.add_argument("--session", "-s", type=str, default=None)
    parser.add_argument("--quiet", "-q", action="store_true", default=False)
    parser.add_argument('cmd', default=[], nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.session is not None:
        LoadSessionCmd.run(args.session, session)
        if not args.quiet:
            PrintSessionCmd.run(None, session)
    else:
        session = {
            "runner" : bash.BashRunner(),
            "encoders" : [],
            "decoders" : [],
        }
        ListRunnersCmd.run(None, session)
        ListEncodersCmd.run(None, session)

    if len(args.cmd):
        print(execute(" ".join(args.cmd), session))
    else:
        while True:
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

                if cmd.startswith("$"):
                    cmd, args = (cmd.lstrip("$").split(" ", 1) + [""])[:2]
                    cls = InteractiveCmd.get_command(cmd)
                    cls.run(args, session)
                else:
                    output = execute(cmd, session)
                    print("\n".join("<<< {}".format(x) for x in output.splitlines()))
            except KeyboardInterrupt:
                print()
            except CmdRunnerException as e:
                print(e)
