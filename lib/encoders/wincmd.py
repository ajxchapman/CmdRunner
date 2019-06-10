from lib.base import CmdEncoder

class WinCmdEncoder(CmdEncoder):
    help = """
        Encoder to run the given command in a windows cmd.exe shell.
    """
    
    def encode(self, cmd):
        return "cmd /S /C {}".format(cmd.replace("^", "^^").replace("&", "^&").replace(">", "^>").replace("(", "^(").replace(")", "^)").replace("|", "^|"))
