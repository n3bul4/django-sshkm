# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sshkm', '0006_auto_20170407_1301'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='error_msg',
            field=models.TextField(null=True, blank=True),
        ),
    ]
