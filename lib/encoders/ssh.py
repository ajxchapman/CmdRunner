from lib.base import CmdEncoder

class SSHEncoder(CmdEncoder):
    help = """
    SSH encoder.
    """
    args = ("username", "host")
    default_args = {
        "identity" : None
    }

    def encode(self, cmd):
        cmd = cmd.replace("\\", "\\\\").replace("\"", "\\\"").replace("|", "\\|")
        ssh_options = []
        if self.identity is not None:
            ssh_options.append("-i {}".format(self.identity))
        ssh_options.append("-o \"StrictHostKeyChecking no\"")
        ssh_options.append("-o \"UserKnownHostsFile /dev/null\"")
        ssh_options = " ".join(ssh_options)
        return "ssh {} {}@{} \"{}\"".format(ssh_options, self.username, self.host, cmd)
