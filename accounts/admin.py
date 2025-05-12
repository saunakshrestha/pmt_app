from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Tenant

# Register your models here.

# --------------------------
# Tenant Admin
# --------------------------

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)


# --------------------------
# Custom User Admin
# --------------------------

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'name', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active')}
        ),
    )