import random

import lib.encoders.wincmd

from lib.base import CmdEncoder

class WmicEncoder(CmdEncoder):
    args = ("host", "username", "password")
    default_args = {
        "host" : None,
        "username" : None,
        "password" : None,
        "delay" : 2,
        "output" : True
    }

    def ready(self, index, encoders):
        # Calculate the delay and encoding requirements based on other encoders in the chain
        self._delay = sum([getattr(x, "delay", 0) for x in encoders[index + 1:]]) + self.delay
        self._skipencoding = sum([1 if x.__class__ == self.__class__ else 0 for x in encoders[:index + 1]]) == 1

    def encode(self, cmd):
        host = self.host or "localhost"
        wmic_args = []
        if self.host is not None:
            wmic_args.append("/NODE:\"{}\"".format(self.host))
            wmic_args.append("/User:\"{}\"".format(self.username))
            wmic_args.append("/Password:\"{}\"".format(self.password))
        wmic_args = " ".join(wmic_args)

        if self.output:
            alphabet = "ABCDEFGHJIKLMNOPQRSTUVWXYZabcdefghjiklmnopqrstuvwxyz0123456789"
            tmp_dir = "".join(random.choice(alphabet) for x in range(8))
            tmp_path = "{}\\{}.log".format(tmp_dir, "".join(random.choice(alphabet) for x in range(8)))
            # TODO: This is a bit of a mess and only works with 2 levels of recursion
            if self._skipencoding:
                remote_cmd = "cmd /S /C ({}) > C:\\{}".format(cmd, tmp_path).replace("\"", "\\\"")
            else:
                remote_cmd = lib.encoders.wincmd.WinCmdEncoder().encode("({}) > C:\\{}".format(cmd, tmp_path)).replace("\"", "\\\"")
            cmd = " && ".join([
              "mkdir \\\\{}\\C$\\{}".format(host, tmp_dir),
              "wmic {} process call create \"{}\" >nul".format(wmic_args, remote_cmd),
              "ping -n {} 127.0.0.1 >nul".format(self._delay),
              "type \\\\{}\\C$\\{}".format(host, tmp_path),
              "rmdir /S /Q \\\\{}\\C$\\{}".format(host, tmp_dir)
            ])
            return cmd

        cmd = cmd.replace("\"", "\\\"")
        return "wmic {} process call create \"{}\"".format(wmic_args, cmd)
