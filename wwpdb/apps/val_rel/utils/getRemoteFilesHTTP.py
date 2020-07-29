import os
import wget


class GetRemoteFiles:

    def __init__(self, output_path):
        self.output_path = output_path

    def get_url(self, url):
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        return wget.download(url, out=self.output_path)
