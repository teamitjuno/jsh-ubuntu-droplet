from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from django.shortcuts import render, redirect
from authentication.models import User
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

def handler500(request):
    return render(request, "500.html", status=500)


def handler403(request, exception):
    return render(request, "403.html", status=403)


def handler404(request, exception):
    return render(request, "404.html", status=404)


# User's profession check decorators
def elektriker_check(user):
    return User.objects.filter(id=user.id, beruf="Elektriker").exists()

def projektant_check(user):
    return User.objects.filter(id=user.id, beruf="Projektant").exists()

def verkaufer_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class ElektrikerCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return elektriker_check(self.request.user)  # type: ignore



@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    def get(self, request):
        return render(request, "pages-login.html")

    def post(self, request):
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, email=email, password=password)

        if user is not None and user.beruf == "Elektriker" and user.kuerzel == "TW":  # type: ignore
            login(request, user)
            return redirect("invoices:tom")

        elif user is not None and user.beruf == "Elektriker":  # type: ignore
            login(request, user)
            return redirect("invoices:home")
        elif user is not None and user.beruf == "Vertrieb":  # type: ignore
            login(request, user)
            return redirect("vertrieb_interface:home")
        elif user is not None and user.beruf == "Projektant":  # type: ignore
            login(request, user)
            return redirect("projektant_interface:home")
        elif user is not None and user.is_staff == True:  # type: ignore
            login(request, user)
            return redirect("/admin")
        else:
            return render(request, "pages-login.html", {"error": "Invalid credentials"})


class LogoutView(APIView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return render(request, "logout.html", {"message": "Logout successful"})

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("authentication:logout")
