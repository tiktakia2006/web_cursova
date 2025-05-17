from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0003_maplocation'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MapLocation',
        ),
    ]
