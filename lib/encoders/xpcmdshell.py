from lib.base import CmdEncoder

class XpCmdShellEncoder(CmdEncoder):
    help = """
    XpCmdShell encoder.
    """

    def encode(self, cmd):
        cmd = cmd.replace("'", "''")
        return "EXEC xp_cmdshell '{}';".format(cmd)
