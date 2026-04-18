from rest_framework import serializers


class LicenseGenerateSerializer(serializers.Serializer):
    licence_number = serializers.CharField(max_length=255, required=True)
    validity_from = serializers.CharField(max_length=255, required=True)
    name_of_licensee = serializers.CharField(max_length=255, required=True)
    type_of_premise = serializers.CharField(max_length=255, required=True)
    license_category = serializers.CharField(max_length=255, required=True)
    address_of_premise = serializers.CharField(required=True)

    def validate(self, attrs):
        cleaned = {}
        for key, value in attrs.items():
            if isinstance(value, str):
                value = value.strip()
            if not value:
                raise serializers.ValidationError({key: "This field is required."})
            cleaned[key] = value
        return cleaned
