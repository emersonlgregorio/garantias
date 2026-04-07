from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Company, User
from apps.properties.models import Property


class TenantApiTests(APITestCase):
    def setUp(self):
        self.ca = Company.objects.create(name="Empresa A", cnpj="11.111.111/0001-11")
        self.cb = Company.objects.create(name="Empresa B", cnpj="22.222.222/0001-22")
        self.user_a = User.objects.create_user(
            email="a@test.com",
            password="x",
            company=self.ca,
            role=User.Role.ADMIN,
        )
        self.user_b = User.objects.create_user(
            email="b@test.com",
            password="x",
            company=self.cb,
            role=User.Role.ADMIN,
        )
        self.prop_a = Property.objects.create(
            company=self.ca,
            description="Fazenda Norte",
            city="X",
        )
        Property.objects.create(
            company=self.cb,
            description="Fazenda Sul",
            city="Y",
        )

    def test_properties_list_scoped_to_company(self):
        self.client.force_authenticate(self.user_a)
        url = reverse("property-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        rows = data if isinstance(data, list) else data.get("results", data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "Fazenda Norte")

    def test_cannot_read_other_company_property_detail(self):
        self.client.force_authenticate(self.user_a)
        url = reverse("property-detail", kwargs={"pk": self.prop_a.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # id inexistente na empresa -> outro pk tentando furar
        other = Property.objects.filter(company=self.cb).first()
        url_bad = reverse("property-detail", kwargs={"pk": other.pk})
        res_bad = self.client.get(url_bad)
        self.assertEqual(res_bad.status_code, status.HTTP_404_NOT_FOUND)
