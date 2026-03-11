from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django_registration.forms import RegistrationForm
from .models import CustomUser, Profile
from django.contrib.auth.models import Group

class CustomUserCreationForm(AdminUserCreationForm):

    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name")

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ("username", "email")
        
from django import forms
from django.contrib.auth.models import Group
from .models import CustomUser, Profile

class CustomRegistrationForm(forms.ModelForm):
    DoB = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    campus = forms.CharField(required=False)
    phone_number = forms.CharField(required=False)
    school = forms.CharField(required=False)
    workplace = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "username")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["username"]

        if commit:
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.DoB = self.cleaned_data["DoB"]
            profile.campus = self.cleaned_data.get("campus", "")
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.school = self.cleaned_data.get("school", "")
            profile.workplace = self.cleaned_data.get("workplace", "")
            profile.save()

            member_group, _ = Group.objects.get_or_create(name="Member")
            user.groups.add(member_group)

        return user