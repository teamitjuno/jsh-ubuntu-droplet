# Django related imports

from django.contrib import messages


from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, get_connection

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView

# Local imports from 'config'
from config.settings import EMAIL_BACKEND

# Local imports from 'datenblatter'
from datenblatter.models import Datenblatter
from prices.models import SolarModulePreise, WallBoxPreise

# Local imports from 'vertrieb_interface'
from vertrieb_interface.forms import (
    VertriebTicketEmailForm,
)
from vertrieb_interface.models import VertriebTicket

import logging

logger = logging.getLogger(__name__)


class DocumentViewTicketNew(LoginRequiredMixin, DetailView):
    model = VertriebTicket
    template_name = "vertrieb/document_ticket_new_view.html"
    context_object_name = "vertrieb_ticket"
    pk_url_kwarg = "ticket_id"
    form_class = VertriebTicketEmailForm

    def dispatch(self, request, *args, **kwargs):
        ticket_id = kwargs.get("ticket_id")
        if not request.user.is_authenticated:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        ticket_id = self.kwargs.get(self.pk_url_kwarg)
        self.object = get_object_or_404(self.model, ticket_id=ticket_id)
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vertrieb_ticket = self.get_object()
        ticket_id = self.kwargs.get("ticket_id")
        pdf_url = reverse("vertrieb_interface:serve_ticket_new_pdf", args=[ticket_id])
        context["pdf_url"] = pdf_url
        context["ticket_id"] = ticket_id
        context["form"] = self.form_class(
            instance=vertrieb_ticket, user=self.request.user
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(
            request.POST, instance=self.get_object(), user=request.user
        )

        if form.is_valid():
            form.save()
            if self._send_email(form.instance):
                messages.success(request, "Email sent successfully")
                return redirect(
                    "vertrieb_interface:document_view_ticket_new", form.instance.ticket_id
                )
        return self.form_invalid(form)

    def _send_email(self, vertrieb_ticket):
        datenblatter = get_object_or_404(Datenblatter)
        email_address = self.request.POST.get("email")
        email_content = self.request.POST.get("text_for_email")
        subject = f"Zusätzliche Vereinbarung Photovoltaikanlage {vertrieb_ticket.ticket_id}"

        user = self.request.user
        body = f"{vertrieb_ticket.salutation}\n\n{email_content}\n\n{user.smtp_body}"
        user_email = user.email

        try:
            connection = get_connection(
                backend=EMAIL_BACKEND,
                host=user.smtp_server,
                port=user.smtp_port,
                username=user.smtp_username,
                password=user.smtp_password,
                use_tls=True,
                fail_silently=False,
            )
            email = EmailMultiAlternatives(
                subject,
                body,
                user.smtp_username,
                [email_address, user_email],
                connection=connection,
                reply_to=[user_email],
            )
            self._attach_files(email, vertrieb_ticket, datenblatter)
            email.send()
            return True
        except Exception as e:
            messages.error(self.request, f"Failed to send email: {str(e)}")
            return False

    def _attach_files(self, email, vertrieb_ticket, datenblatter):
        file_data = vertrieb_ticket.ticket_pdf.tobytes()
        name = replace_spaces_with_underscores(vertrieb_ticket.name)
        email.attach(
            f"{name}_{vertrieb_ticket.ticket_id}.pdf", file_data, "application/pdf"
        )

    def form_invalid(self, form):
        return render(
            self.request, self.template_name, self.get_context_data(form=form)
        )


def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_").replace(",","")
