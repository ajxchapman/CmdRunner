import os
import signal
import subprocess
import time

from lib.base import CmdRunner, CmdArgument

class BashRunner(CmdRunner):
    timeout = CmdArgument(default=30, arg_type=int, description="Number of seconds to wait for the command to complete")
    help = """
        Basic runner to run commands in a bash shell.
    """

    def run(self, cmd):
        """
        Simple CmdRunner which just executes the command.
        """
        starttime = time.time()
        proc = subprocess.Popen(["/bin/bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        while proc.poll() is None:
            if self.timeout is not None and time.time() - starttime > self.timeout:
                print("[!] Command timed out")
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            time.sleep(0.2)
        return proc.communicate()[0].decode()
