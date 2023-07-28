from django import forms
from .models import SolarModulePreise

class SolarModulePreiseForm(forms.ModelForm):
    name = forms.CharField(required=True, initial="Solar Module", widget=forms.TextInput(attrs={'class': 'form-control', 'id' : 'id_name', }))
    price = forms.IntegerField(
        required=True, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'id' : 'id_price'}))
    actual_price = forms.IntegerField(
        required=False,
        initial=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'id' : 'id_actual_price'}))
    old_price = forms.IntegerField(
        required=False,
        initial=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'id' : 'id_old_price'}))
    in_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "custom-control-input", "id" : 'id_in_stock'}))
    class Meta:
        model = SolarModulePreise
        fields = ['name', 'price', 'actual_price', 'old_price', 'in_stock']
