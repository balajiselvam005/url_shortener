from rest_framework import serializers
from .models import ShortURL

class ShortenSerializer(serializers.Serializer):
    url = serializers.URLField(
        max_length=2000,
        error_messages={
            "invalid": "Enter a valid URL.",
            "required": "URL is required."
        }
    )
    custom_alias = serializers.CharField(
        max_length=6,
        required=False,
        allow_blank=True
    )
    expires_in_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=365
    )

    def validate_custom_alias(self, value):
        value = value.strip()
        if value:
            if not value.isalnum():
                raise serializers.ValidationError("Alias must be alphanumeric only.")
            if ShortURL.objects.filter(short_code=value).exists():
                raise serializers.ValidationError("This alias is already taken.")
        return value