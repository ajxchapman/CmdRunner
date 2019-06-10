import requests
import urllib.parse

from lib.base import CmdRunner, CmdArgument

class WebRunner(CmdRunner):
    help = """
        HTTP runner which POSTS command to the provided URL.
    """
    url = CmdArgument(arg_type=str, description="The URL to connect to")
    data = CmdArgument(arg_type=str, description="The POST data to send in the HTTP request")
    replace = CmdArgument(arg_type=str, default="***", description="The string to replace with the encoded command")

    def run(self, cmd):
        data = self.data.replace(self.replace, cmd)
        r = requests.post(self.url, headers={"Content-Type" : "application/x-www-form-urlencoded"}, data=data)
        return r.text

    def encode(self, cmd):
        return urllib.parse.quote_plus(cmd)
