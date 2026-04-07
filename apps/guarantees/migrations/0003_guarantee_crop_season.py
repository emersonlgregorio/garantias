import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crops", "0001_initial"),
        ("guarantees", "0002_guarantee_property_verbose"),
    ]

    operations = [
        migrations.AddField(
            model_name="guarantee",
            name="crop_season",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="guarantees",
                to="crops.cropseason",
                verbose_name="safra",
            ),
        ),
    ]
