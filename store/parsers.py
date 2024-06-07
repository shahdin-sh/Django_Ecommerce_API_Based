from rest_framework import parsers


class PlainTextParser(parsers.BaseParser):
    media_type = 'plain text'

    def parse(self, stream, media_type=None, parser_context=None):
        # return a string representing the body of the request
        return stream.read().decode('utf-8')
