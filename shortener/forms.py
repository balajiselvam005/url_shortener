from django import forms

from shortener.models import ShortURL

class ShortenForm(forms.Form):
    url = forms.URLField(
        label="Long URL",
        max_length=200,
        error_messages={
            "required": "URL is required",
            "invalid": "Enter a valid URL (e.g. https://example.com)."
        },
        widget=forms.URLInput(attrs={
            "placeholder": "https://example.com/very/long/url"
        })
    )
    custom_alias = forms.CharField(
        label="Custom Alias",
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. mylink"
        })
    )

    def clean_custom_alias(self):
        alias = self.cleaned_data.get("custom_alias", "").strip()
        if alias:
            if not alias.isalnum():
                raise forms.ValidationError("Alias must be alphanumeric only.")
            if ShortURL.objects.filter(short_code=alias).exists():
                raise forms.ValidationError("This alias is already taken.")
        return alias