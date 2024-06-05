from django import forms
from .models import SolarModulePreise
from .models import WallBoxPreise
from .models import OptionalAccessoriesPreise
from .models import AndereKonfigurationWerte


class AndereKonfigurationWerteForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "id_andere_konfiguration_name"}
        ),
    )
    value = forms.DecimalField(
        required=True,
        initial=0.00,
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "id_andere_konfiguration_value"}
        ),
    )

    class Meta:
        model = AndereKonfigurationWerte
        fields = ["name", "value"]


class OptionalAccessoriesPreiseForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "id_optional_accessories_name"}
        ),
    )
    price = forms.DecimalField(
        required=True,
        initial=0.00,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "id_optional_accessories_price"}
        ),
    )

    class Meta:
        model = OptionalAccessoriesPreise
        fields = ["name", "price"]


class SolarModulePreiseForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        initial="Solar Module",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_name",
            }
        ),
    )
    price = forms.IntegerField(
        required=True,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_price"}),
    )
    quantity = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_old_price"}),
    )
    in_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "custom-control-input", "id": "id_in_stock"}
        ),
    )

    class Meta:
        model = SolarModulePreise
        fields = ["name", "price", "in_stock", "quantity"]


class WallBoxPreiseForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "id_wallbox_name"}
        ),
    )
    price = forms.DecimalField(
        required=True,
        initial=0.00,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "id_wallbox_price"}
        ),
    )
    in_stock = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "custom-control-input", "id": "id_wallbox_in_stock"}
        ),
    )

    class Meta:
        model = WallBoxPreise
        fields = ["name", "price", "in_stock"]
