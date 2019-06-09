from lib.base import CmdRunner

class EchoRunner(CmdRunner):
    def run(seld, cmd):
        """
        Simple CmdRunner which just echos the command.
        """
        return cmd
