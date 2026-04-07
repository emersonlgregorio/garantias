# Generated manually — Fazenda (descrição + cidade); área com matrícula no mapa.

from django.db import migrations, models


def forwards_property(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    for p in Property.objects.all():
        parts = [
            getattr(p, "registration_number", "") or "",
            getattr(p, "registry_office", "") or "",
        ]
        desc = " — ".join(x for x in parts if x).strip() or "Fazenda (legado)"
        p.description = desc[:2000]
        p.save(update_fields=["description"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="property",
            name="uniq_property_company_registration_office",
        ),
        migrations.AddField(
            model_name="property",
            name="description",
            field=models.TextField(default="", verbose_name="descrição"),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_property, noop_reverse),
        migrations.RemoveField(model_name="property", name="registration_number"),
        migrations.RemoveField(model_name="property", name="registry_office"),
        migrations.RemoveField(model_name="property", name="state"),
        migrations.AlterField(
            model_name="property",
            name="city",
            field=models.CharField(max_length=120, verbose_name="cidade"),
        ),
        migrations.AlterField(
            model_name="property",
            name="description",
            field=models.TextField(verbose_name="descrição"),
        ),
        migrations.AlterModelOptions(
            name="property",
            options={"verbose_name": "Fazenda", "verbose_name_plural": "Fazendas"},
        ),
        migrations.RenameField(
            model_name="area",
            old_name="name",
            new_name="matricula",
        ),
        migrations.AlterField(
            model_name="area",
            name="matricula",
            field=models.CharField(max_length=120, verbose_name="matrícula"),
        ),
    ]
