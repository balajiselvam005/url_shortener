from django.db import models
from django.contrib.auth.models import User
import string, secrets

def generate_code():
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(6))
        if not ShortURL.objects.filter(short_code=code).exists():
            return code

class ShortURL(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length=6, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.short_code