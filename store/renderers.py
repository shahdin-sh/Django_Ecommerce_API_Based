from rest_framework import renderers
from django.utils.encoding import smart_str


class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return smart_str(data, encoding=self.charset)