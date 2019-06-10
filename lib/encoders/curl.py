from lib.base import CmdEncoder, CmdArgument

class CurlEncoder(CmdEncoder):
    help = """
    Encoder which encodes the command within a Curl POST request command.
    """
    url = CmdArgument(arg_type=str, description="The URL to connect to")
    data = CmdArgument(arg_type=str, description="The POST data to send in the HTTP request")
    replace = CmdArgument(arg_type=str, default="***", description="The string to replace with the encoded command")

    def encode(self, cmd):
        cmd = urllib.parse.quote_plus(cmd)
        data = self.data.replace(self.replace, cmd)
        return "curl -s -k  -X POST --data-binary \"{}\" \"{}\"".format(data, self.url)
