from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User, Visitor


class AddUserForm(forms.ModelForm):
    """
    New User Form. Requires password confirmation.
    """
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Confirm password', widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'email_notifications', 'is_staff')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UpdateUserForm(forms.ModelForm):
    """
    Update User Form. Doesn't allow changing password in the Admin.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'email', 'password', 'first_name', 'last_name', 'is_active',
            'is_staff', 'email_notifications'
        )

    def clean_password(self):
        # Password can't be changed in the admin
        return self.initial["password"]


@admin.action(description='Disable email notification for the selected users')
def disable_email(modeladmin, request, queryset):
    for user in queryset:
        user.email_notifications = False
        user.save()


@admin.action(description='Enable email notification for the selected users')
def enable_email(modeladmin, request, queryset):
    for user in queryset:
        user.email_notifications = True
        user.save()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UpdateUserForm
    add_form = AddUserForm
    actions = [disable_email, enable_email]
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'email_notifications')
    list_filter = ('is_staff', )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'email_notifications')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email', 'first_name', 'last_name', 'password1',
                    'password2'
                )
            }
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email', 'first_name', 'last_name')
    filter_horizontal = ()

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    def get_list_display(self, *args, **kwargs):
        return super().get_list_display(*args, **kwargs)+('page_visited','timestamp',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True#False
