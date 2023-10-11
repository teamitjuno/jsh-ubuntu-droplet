from django.http import HttpResponse

class MalformedRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            print("Error:", e)
            print("Headers:", request.headers)
            return HttpResponse(status=400)
