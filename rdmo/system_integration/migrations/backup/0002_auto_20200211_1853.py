# Generated by Django 2.2.7 on 2020-02-11 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_integration', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalog2externaldatamodel',
            name='datamodel',
            field=models.IntegerField(),
        ),
    ]