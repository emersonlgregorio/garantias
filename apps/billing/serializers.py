from rest_framework import serializers

from apps.billing.models import Invoice, Module, Plan, PlanFeature, Subscription


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["id", "key", "name", "description", "is_active"]


class PlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeature
        fields = ["key", "value"]


class PlanSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    features = PlanFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "module",
            "name",
            "price",
            "billing_type",
            "description",
            "is_active",
            "features",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "company",
            "module",
            "plan",
            "status",
            "trial_end_date",
            "start_date",
            "end_date",
            "is_locked",
            "locked_at",
            "lock_reason",
        ]
        read_only_fields = ["company", "is_locked", "locked_at", "lock_reason"]


class InvoiceSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = ["id", "company", "subscription", "amount", "status", "due_date", "created_at"]
        read_only_fields = fields
