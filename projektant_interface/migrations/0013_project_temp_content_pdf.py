# Generated by Django 4.2.2 on 2023-08-11 06:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projektant_interface", "0012_project_current_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="temp_content_pdf",
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
