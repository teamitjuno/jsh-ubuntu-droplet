from django.db import models


class Datenblatter(models.Model):
    solar_module_1 = models.FileField(upload_to="uploads/", blank=True, null=True)
    solar_module_2 = models.FileField(upload_to="uploads/", blank=True, null=True)
    solar_module_3 = models.FileField(upload_to="uploads/", blank=True, null=True)
    solar_module_4 = models.FileField(upload_to="uploads/", blank=True, null=True)
    speicher_module = models.FileField(upload_to="uploads/", blank=True, null=True)
    speicher_module_huawei7 = models.FileField(upload_to="uploads/", blank=True, null=True)
    speicher_module_viessmann = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    wall_box = models.FileField(upload_to="uploads/", blank=True, null=True)
    wall_box_viessman = models.FileField(upload_to="uploads/", blank=True, null=True)
    wechselrichter = models.FileField(upload_to="uploads/", blank=True, null=True)
    wechselrichter_viessman = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    backup_box = models.FileField(upload_to="uploads/", blank=True, null=True)
    backup_box_viessmann = models.FileField(upload_to="uploads/", blank=True, null=True)
    optimizer = models.FileField(upload_to="uploads/", blank=True, null=True)
    huawei_smartmeter_dtsu = models.FileField(upload_to="uploads/", blank=True, null=True)
    huawei_smartmeter_emma = models.FileField(upload_to="uploads/", blank=True, null=True)
    huawei_smart_energie_controller = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    optimizer_viessmann = models.FileField(upload_to="uploads/", blank=True, null=True)
    viessmann_tigo = models.FileField(upload_to="uploads/", blank=True, null=True)
    viessmann_allgemeine_bedingungen = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    viessmann_versicherung_ausweis = models.FileField(
        upload_to="uploads/", blank=True, null=True
    )
    ac_thor = models.FileField(upload_to="uploads/", blank=True, null=True)
