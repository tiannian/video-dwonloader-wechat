import re

class UrlLoader:
    def __init__(self, config_file):
        f = open(config_file, "rb")
        self.matchers = []
        for line in f:
            encoded_line = line.decode('utf-8')[:-1]
            if encoded_line == '':
                continue
            self.matchers.append(encoded_line)

    def match(self, url):
        for matcher in self.matchers:
            if re.match(matcher, url) != None:
                return True
        return False

if __name__ == "__main__":
    url_loader = UrlLoader("./urls.conf")
    result = url_loader.match("https://v.pptv.com/show/aLibZF3iclVZP2dNw.html?rcc_src=www_index&spm=www_index_web.sb_2717768.1.0.0.0.0")
    print(result)

