# Generated manually — normaliza status legado e aplica choices.

from django.db import migrations, models


def normalize_guarantee_status(apps, schema_editor):
    Guarantee = apps.get_model("guarantees", "Guarantee")
    valid = {"SOLICITADO", "ATIVO", "BAIXADO"}
    for g in Guarantee.objects.all():
        s = (g.status or "").strip()
        if not s:
            new_v = "SOLICITADO"
        elif s in valid:
            new_v = s
        else:
            low = s.lower()
            if low == "ativo":
                new_v = "ATIVO"
            elif low == "baixado":
                new_v = "BAIXADO"
            elif low == "solicitado":
                new_v = "SOLICITADO"
            else:
                new_v = "SOLICITADO"
        if g.status != new_v:
            g.status = new_v
            g.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("guarantees", "0004_guarantee_business_partner_guarantee_cpr_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_guarantee_status, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="guarantee",
            name="status",
            field=models.CharField(
                choices=[
                    ("SOLICITADO", "Solicitado"),
                    ("ATIVO", "Ativo"),
                    ("BAIXADO", "Baixado"),
                ],
                default="SOLICITADO",
                max_length=16,
                verbose_name="status",
            ),
        ),
    ]
