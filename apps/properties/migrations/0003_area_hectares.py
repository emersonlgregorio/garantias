from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0002_fazenda_area_matricula"),
    ]

    operations = [
        migrations.AddField(
            model_name="area",
            name="hectares",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=14,
                null=True,
                verbose_name="hectares",
            ),
        ),
    ]
