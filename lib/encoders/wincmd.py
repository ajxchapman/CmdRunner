from lib.base import CmdEncoder

class WinCmdEncoder(CmdEncoder):
    def encode(self, cmd):
        return "cmd /S /C {}".format(cmd.replace("^", "^^").replace("&", "^&").replace(">", "^>").replace("(", "^(").replace(")", "^)").replace("|", "^|"))
