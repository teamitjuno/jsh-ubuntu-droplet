# Generated by Django 5.0.2 on 2024-04-25 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vertrieb_interface", "0049_alter_editierbarer_text_content"),
    ]

    operations = [
        migrations.AlterField(
            model_name="editierbarer_text",
            name="x",
            field=models.FloatField(default=0.0, help_text="x-Koordinate"),
        ),
        migrations.AlterField(
            model_name="editierbarer_text",
            name="y",
            field=models.FloatField(default=0.0, help_text="y-Koordinate"),
        ),
    ]
