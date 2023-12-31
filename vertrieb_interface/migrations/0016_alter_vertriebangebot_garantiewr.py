# Generated by Django 4.2.2 on 2023-08-16 07:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vertrieb_interface", "0015_vertriebangebot_vorname_nachname"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vertriebangebot",
            name="garantieWR",
            field=models.CharField(
                choices=[
                    ("keine", "keine"),
                    ("10 Jahre", "10 Jahre"),
                    ("15 Jahre", "15 Jahre"),
                    ("20 Jahre", "20 Jahre"),
                ],
                default="10 Jahre",
                max_length=10,
            ),
        ),
    ]
