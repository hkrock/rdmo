# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-03 15:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('questions', '0027_remove_question_entity_and_question'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='QuestionItem',
            new_name='Question',
        ),
    ]
