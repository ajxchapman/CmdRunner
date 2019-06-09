from lib.base import CmdEncoder

class EchoEncoder(CmdEncoder):
    def encode(self, cmd):
        return WinCmdEncoder().encode("echo {}".format(cmd))
