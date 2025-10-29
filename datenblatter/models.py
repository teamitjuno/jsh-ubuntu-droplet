from django.db import models


class Datenblatter(models.Model):
    speicher_module = models.FileField(upload_to="uploads/", blank=True, null=True)
    speicher_module_huawei7 = models.FileField(upload_to="uploads/", blank=True, null=True)
    speicher_module_atmoce = models.FileField(upload_to="uploads/", blank=True, null=True)
    speicher_module_viessmann = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    wechselrichter = models.FileField(upload_to="uploads/", blank=True, null=True)
    wechselrichter_map0 = models.FileField(upload_to="uploads/", blank=True, null=True)
    wechselrichter_mb0 = models.FileField(upload_to="uploads/", blank=True, null=True)
    wechselrichter_viessman = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    backup_box = models.FileField(upload_to="uploads/", blank=True, null=True)
    backup_box_viessmann = models.FileField(upload_to="uploads/", blank=True, null=True)
    smartguard =  models.FileField(upload_to="uploads/", blank=True, null=True)
    optimizer = models.FileField(upload_to="uploads/", blank=True, null=True)
    huawei_smartmeter_dtsu = models.FileField(upload_to="uploads/", blank=True, null=True)
    huawei_smartmeter_emma = models.FileField(upload_to="uploads/", blank=True, null=True)
    huawei_smart_energie_controller = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    smartmeter_atmoce = models.FileField(upload_to="uploads/", blank=True, null=True)
    optimizer_viessmann = models.FileField(upload_to="uploads/", blank=True, null=True)
    viessmann_tigo = models.FileField(upload_to="uploads/", blank=True, null=True)
    viessmann_allgemeine_bedingungen = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    viessmann_versicherung_ausweis = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    ac_thor = models.FileField(upload_to="uploads/", blank=True, null=True)
    ac_elwa = models.FileField(upload_to="uploads/", blank=True, null=True)
    finanzierung = models.FileField(upload_to="uploads/", blank=True, null=True)
