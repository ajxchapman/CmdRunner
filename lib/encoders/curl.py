from lib.base import CmdEncoder

class CurlEncoder(CmdEncoder):
    help = """
    Curl encoder.
    """
    args = ("url", "data")
    default_args = {
        "replace" : "***"
    }

    def encode(self, cmd):
        cmd = urllib.parse.quote_plus(cmd)
        data = self.data.replace(self.replace, cmd)
        return "curl -s -k  -X POST --data-binary \"{}\" \"{}\"".format(data, self.url)
