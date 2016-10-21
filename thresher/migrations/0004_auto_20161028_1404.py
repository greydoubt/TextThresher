# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-28 14:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thresher', '0003_auto_20161021_0848'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[(b'mc', b'Multiple Choice'), (b'dt', b'Date Time'), (b'tb', b'Textbox'), (b'cl', b'Checklist')], default='', max_length=2),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('topic', 'question_text', 'type')]),
        ),
    ]