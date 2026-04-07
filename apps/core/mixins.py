"""Mixins para ViewSets com isolamento por empresa."""


class CompanyScopedQuerysetMixin:
    """Filtra queryset por `request.user.company` usando `company_field`."""

    company_field = "company"

    def get_company_id(self):
        user = self.request.user
        if user.is_superuser:
            return None
        return user.company_id

    def scope_queryset(self, qs):
        cid = self.get_company_id()
        if cid is None:
            return qs
        return qs.filter(**{self.company_field: cid})


class CompanyScopedPropertyQuerysetMixin(CompanyScopedQuerysetMixin):
    company_field = "property__company"


class CompanyScopedGuaranteeQuerysetMixin(CompanyScopedQuerysetMixin):
    company_field = "guarantee__company"
