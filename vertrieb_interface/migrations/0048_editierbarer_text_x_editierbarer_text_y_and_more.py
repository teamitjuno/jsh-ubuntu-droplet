# Generated by Django 5.0.2 on 2024-04-25 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vertrieb_interface", "0047_editierbarer_text_dokument_pdf"),
    ]

    operations = [
        migrations.AddField(
            model_name="editierbarer_text",
            name="x",
            field=models.IntegerField(default=0, help_text="x-Koordinate"),
        ),
        migrations.AddField(
            model_name="editierbarer_text",
            name="y",
            field=models.IntegerField(default=0, help_text="y-Koordinate"),
        ),
        migrations.AlterField(
            model_name="editierbarer_text",
            name="content",
            field=models.TextField(
                default="<<kein editierbarer text>>", help_text="Schrift"
            ),
        ),
        migrations.AlterField(
            model_name="editierbarer_text",
            name="font",
            field=models.CharField(
                default="JUNO Solar Lt", help_text="Schrift", max_length=100
            ),
        ),
        migrations.AlterField(
            model_name="editierbarer_text",
            name="font_size",
            field=models.IntegerField(default=11, help_text="Schriftgröße"),
        ),
    ]
