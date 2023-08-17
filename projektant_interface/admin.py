from django.contrib import admin
from .models import Elektriktermin, Bautermine, Module1, Wallbox1, Wechselrichter1, Speicher, Project

@admin.register(Elektriktermin)
class ElektrikterminAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Elektriktermin._meta.fields]

@admin.register(Bautermine)
class BautermineAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Bautermine._meta.fields]

@admin.register(Module1)
class Module1Admin(admin.ModelAdmin):
    list_display = [field.name for field in Module1._meta.fields]

@admin.register(Wallbox1)
class Wallbox1Admin(admin.ModelAdmin):
    list_display = [field.name for field in Wallbox1._meta.fields]

@admin.register(Wechselrichter1)
class Wechselrichter1Admin(admin.ModelAdmin):
    list_display = [field.name for field in Wechselrichter1._meta.fields]

@admin.register(Speicher)
class SpeicherAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Speicher._meta.fields]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Project._meta.fields]

