from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from.forms import CustomUserChangeForm, CustomUserCreationForm 

# models admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "first_name", "last_name", "email", "phone_number", "password1", "password2")
            },
        ),
    )
    fieldsets = UserAdmin.fieldsets + (
        ("Addintional informations", {'fields': ('phone_number',),}),
    )

    list_display = ['username', 'email', 'phone_number', 'first_name', 'last_name', 'is_staff', 'get_group']
    list_per_page = 10
    ordering = ['-date_joined']

    @admin.display(description='groups')
    def get_group(self, obj):
        return ','.join([group.name for group in obj.groups.all()])


# # registering models
# admin.site.register(CustomUser, UserAdmin)

