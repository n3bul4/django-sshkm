# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sshkm', '0003_host_last_status'),
    ]

    operations = [
        migrations.AlterField('Host', 'status', models.IntegerField())
    ]
