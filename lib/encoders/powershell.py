import base64

from lib.base import CmdEncoder

class PowerShellEncoder(CmdEncoder):
    def encode(self, cmd):
        cmd = base64.b64encode(cmd.encode("UTF-16")[2:]).decode()
        return "powershell -NoProfile –ExecutionPolicy Bypass -EncodedCommand {}".format(cmd)
