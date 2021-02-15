from django.contrib import admin
from .models import Project, Profile
from django.contrib.auth.models import User

from django.contrib.auth.admin import UserAdmin

# Register your models here.

admin.site.unregister(User)

class ProfileInline(admin.TabularInline):
    model = Profile

class MyUserAdmin(UserAdmin):
    inlines = [
        ProfileInline,
    ]

admin.site.register(User, MyUserAdmin)

admin.site.register(Project)
