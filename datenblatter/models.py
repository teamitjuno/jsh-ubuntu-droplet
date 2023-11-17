from django.db import models

class Datenblatter(models.Model):
    solar_module_1 = models.FileField(upload_to='uploads/', blank=True, null=True)
    solar_module_2 = models.FileField(upload_to='uploads/', blank=True, null=True)
    solar_module_3 = models.FileField(upload_to='uploads/', blank=True, null=True)
    speicher_module = models.FileField(upload_to='uploads/', blank=True, null=True)
    wall_box = models.FileField(upload_to='uploads/', blank=True, null=True)
    wechselrichter = models.FileField(upload_to='uploads/', blank=True, null=True)
    backup_box = models.FileField(upload_to='uploads/', blank=True, null=True)