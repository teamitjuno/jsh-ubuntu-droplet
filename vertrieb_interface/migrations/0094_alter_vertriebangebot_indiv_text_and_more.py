# Generated by Django 5.0.2 on 2025-04-16 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "vertrieb_interface",
            "0093_vertriebangebot_indiv_text_vertriebticket_indiv_text",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="vertriebangebot",
            name="indiv_text",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="vertriebticket",
            name="indiv_text",
            field=models.TextField(blank=True, null=True),
        ),
    ]
