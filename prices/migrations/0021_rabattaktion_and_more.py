# Generated by Django 5.0.2 on 2024-11-06 12:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0020_alter_optionalaccessoriespreise_pdf_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="RabattAktion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("prozentsatz", models.DecimalField(decimal_places=2, max_digits=10)),
                ("fixbetrag", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.RenameField(
            model_name="prices",
            old_name="modul_garantie_preise",
            new_name="wr_garantie_preise",
        ),
        migrations.AddField(
            model_name="prices",
            name="rabatt_aktion",
            field=models.ForeignKey(
                default=42,
                on_delete=django.db.models.deletion.CASCADE,
                to="prices.rabattaktion",
            ),
            preserve_default=False,
        ),
    ]