from django.contrib import admin

from .models import ProductivityProfile, User

admin.site.register(User)
admin.site.register(ProductivityProfile)
