from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from django.shortcuts import render, redirect
from authentication.models import User
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from vertrieb_interface.telegram_logs_sender import send_message_to_bot
import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse


def log_and_notify(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    send_message_to_bot(message)


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


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    def get(self, request):
        # Check if 'next' parameter is present in the URL
        next_page = request.GET.get("next", "/")
        if not next_page:
            # If 'next' is not present, redirect to the login URL with 'next' parameter
            return HttpResponseRedirect(f"{reverse('login')}?next=/")
        # If 'next' is present, render the login page normally
        return render(request, "pages-login.html")

    def post(self, request):
        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(request, username=email, password=password)

        if not user:
            log_and_notify(f"Authentication failed for email:, {email}")
        else:
            log_and_notify(f"User authenticated:, {user.beruf}, {user.kuerzel}")

        if user is not None and user.beruf == "Elektriker" and user.kuerzel == "TW":  # type: ignore
            login(request, user)
            return redirect("invoices:tom")

        elif user is not None and user.beruf == "Elektriker":  # type: ignore
            login(request, user)
            return redirect("invoices:home")
        elif user is not None and user.beruf == "Vertrieb":  # type: ignore
            login(request, user)
            return redirect("vertrieb_interface:user_redirect")
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
