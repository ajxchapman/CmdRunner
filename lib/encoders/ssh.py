from lib.base import CmdEncoder, CmdArgument

class SSHEncoder(CmdEncoder):
    help = """
        Encoder which runs the given command on the target SSH server.
    """
    username = CmdArgument(arg_type=str, description="The SSH user")
    host = CmdArgument(arg_type=str, description="The SSH host")
    identity = CmdArgument(arg_type=str, default=None, required=False, description="Path to the identity file to use")

    def encode(self, cmd):
        cmd = cmd.replace("\\", "\\\\").replace("\"", "\\\"").replace("|", "\\|")
        ssh_options = []
        if self.identity is not None:
            ssh_options.append("-i {}".format(self.identity))
        ssh_options.append("-o \"StrictHostKeyChecking no\"")
        ssh_options.append("-o \"UserKnownHostsFile /dev/null\"")
        ssh_options = " ".join(ssh_options)
        return "ssh {} {}@{} \"{}\"".format(ssh_options, self.username, self.host, cmd)
