from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import Company
from apps.crops.models import Commitment, CropSeason
from apps.guarantees.models import Guarantee
from apps.properties.models import Property


class CommitmentLimitTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Cia", cnpj="12.345.678/0001-90")
        self.prop = Property.objects.create(
            company=self.company,
            description="Fazenda exemplo",
            city="Cáceres",
        )
        self.g1 = Guarantee.objects.create(
            company=self.company,
            property=self.prop,
            type=Guarantee.Type.CEDULA_RURAL,
            value=Decimal("1000.00"),
            issue_date="2024-01-01",
            status="ativo",
        )
        self.g2 = Guarantee.objects.create(
            company=self.company,
            property=self.prop,
            type=Guarantee.Type.PENHOR,
            value=Decimal("2000.00"),
            issue_date="2024-01-02",
            status="ativo",
        )
        self.g3 = Guarantee.objects.create(
            company=self.company,
            property=self.prop,
            type=Guarantee.Type.BARTER,
            value=Decimal("3000.00"),
            issue_date="2024-01-03",
            status="ativo",
        )
        self.g4 = Guarantee.objects.create(
            company=self.company,
            property=self.prop,
            type=Guarantee.Type.OUTROS,
            value=Decimal("4000.00"),
            issue_date="2024-01-04",
            status="ativo",
        )
        self.season = CropSeason.objects.create(
            company=self.company,
            name="2024/2025",
            start_date="2024-07-01",
            end_date="2025-06-30",
        )

    def test_fourth_commitment_same_property_season_fails(self):
        for g in (self.g1, self.g2, self.g3):
            Commitment.objects.create(
                guarantee=g,
                crop_season=self.season,
                value=Decimal("1.00"),
            )
        with self.assertRaises(ValidationError):
            c4 = Commitment(
                guarantee=self.g4,
                crop_season=self.season,
                value=Decimal("1.00"),
            )
            c4.full_clean()
            c4.save()
