# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sshkm', '0004_auto_20170407_1131'),
    ]

    operations = [
        migrations.AlterField('Host', 'status', models.IntegerField(null=True, blank=True))
    ]
