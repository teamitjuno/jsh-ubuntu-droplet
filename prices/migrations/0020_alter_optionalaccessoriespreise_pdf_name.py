# Generated by Django 5.0.2 on 2024-08-21 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0019_alter_optionalaccessoriespreise_pdf_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="optionalaccessoriespreise",
            name="pdf_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
