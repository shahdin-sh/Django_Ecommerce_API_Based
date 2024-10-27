import threading

thread_local = threading.local()

def get_current_request():
    return getattr(thread_local, 'request')


class RequestMiddleware:
    def __init__(self, response):
        self.get_response = response
    
    def __call__(self, request):
        thread_local.request = request
        response = self.get_response(request)
        thread_local.request = None
        return response