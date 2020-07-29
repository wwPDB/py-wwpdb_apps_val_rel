import wget


class GetRemoteFiles:

    def __init__(self, output_path):
        self.output_path = output_path

    def get_url(self, url):
        ret = wget.download(url, out=self.output_path)

