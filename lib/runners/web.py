import requests
import urllib.parse

from lib.base import CmdRunner

class WebRunner(CmdRunner):
    args = ("url", "data")
    default_args = {
        "replace" : "***"
    }

    def run(self, cmd):
        data = self.data.replace(self.replace, cmd)
        r = requests.post(self.url, headers={"Content-Type" : "application/x-www-form-urlencoded"}, data=data)
        return r.text

    def encode(self, cmd):
        return urllib.parse.quote_plus(cmd)
