from lib.base import CmdEncoder

class XpCmdShellEncoder(CmdEncoder):
    help = """
        Encoder to run the given command in a Mircosoft SQL Server xp_cmdshell stored procedure.
    """

    def encode(self, cmd):
        cmd = cmd.replace("'", "''")
        return "EXEC xp_cmdshell '{}';".format(cmd)
