from lib.base import CmdRunner

class EchoRunner(CmdRunner):
    help = """
        Simple runner which echos the provided command without actually running it.
    """

    def run(seld, cmd):
        return cmd
