from lib.base import CmdEncoder

import lib.encoders.wincmd

class EchoEncoder(CmdEncoder):
    help = """
        Simple encoder which encodes the command within an 'echo' command, used for debugging.
    """
    def encode(self, cmd):
        return lib.encoders.wincmd.WinCmdEncoder().encode("echo {}".format(cmd))
