# Generated by Django 4.2.2 on 2023-08-10 08:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projektant_interface", "0005_project_bauplan_img_project_bauplan_pdf"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="kunden_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
