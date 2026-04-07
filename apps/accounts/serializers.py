from rest_framework import serializers

from apps.accounts.models import Company, User


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "cnpj", "plan", "status", "created_at"]
        read_only_fields = ["created_at"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "company",
            "role",
            "first_name",
            "last_name",
            "is_active",
            "password",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        r = self.context.get("request")
        if r and r.user.is_authenticated and not r.user.is_superuser:
            self.fields["company"].read_only = True

    def validate(self, attrs):
        r = self.context["request"]
        if self.instance is None and r.user.is_superuser and not attrs.get("company"):
            raise serializers.ValidationError({"company": "Obrigatório ao criar usuário como superusuário."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        request = self.context["request"]
        if not request.user.is_superuser:
            validated_data["company"] = request.user.company
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
