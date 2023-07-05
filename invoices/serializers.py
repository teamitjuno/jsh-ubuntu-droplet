from rest_framework import serializers
from .models import ElectricInvoice, KundenData, Position


class ElectricInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricInvoice
        fields = "__all__"


class KundenDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = KundenData
        fields = "__all__"


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"
