# Generated by Django 5.0.2 on 2024-08-14 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0014_rename_modulepreise_kwppreise"),
    ]

    operations = [
        migrations.AddField(
            model_name="wallboxpreise",
            name="pdf_text",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
