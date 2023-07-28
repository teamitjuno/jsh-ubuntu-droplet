from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import SolarModulePreise
from .forms import SolarModulePreiseForm

class SolarModulePreiseCreateView(CreateView):
    model = SolarModulePreise
    form_class = SolarModulePreiseForm
    template_name = 'solar_module_preise_form.html'
    success_url = reverse_lazy('solar_module_preise_list')

class SolarModulePreiseUpdateView(UpdateView):
    model = SolarModulePreise
    form_class = SolarModulePreiseForm
    template_name = 'solar_module_preise_form.html'
    success_url = reverse_lazy('solar_module_preise_list')

class SolarModulePreiseDeleteView(DeleteView):
    model = SolarModulePreise
    template_name = 'solar_module_preise_confirm_delete.html'
    success_url = reverse_lazy('solar_module_preise_list')
