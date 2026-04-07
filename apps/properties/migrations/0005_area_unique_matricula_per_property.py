# Normaliza matrículas (trim), resolve duplicatas na mesma fazenda e aplica UNIQUE (property, matricula).

from collections import defaultdict

from django.db import migrations, models


def normalize_and_dedupe_matriculas(apps, schema_editor):
    Area = apps.get_model("properties", "Area")
    for a in Area.objects.iterator():
        s = (a.matricula or "").strip()
        if not s:
            s = f"—{a.pk}"
        if s != a.matricula:
            a.matricula = s
            a.save(update_fields=["matricula"])

    groups = defaultdict(list)
    for a in Area.objects.iterator():
        groups[(a.property_id, a.matricula)].append(a.pk)

    for _key, pks in groups.items():
        if len(pks) <= 1:
            continue
        for pk in sorted(pks)[1:]:
            row = Area.objects.get(pk=pk)
            row.matricula = f"{row.matricula} ({pk})"
            row.save(update_fields=["matricula"])


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0004_property_owner"),
    ]

    operations = [
        migrations.RunPython(normalize_and_dedupe_matriculas, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="area",
            constraint=models.UniqueConstraint(
                fields=("property", "matricula"),
                name="properties_area_prop_matricula_uniq",
            ),
        ),
    ]
