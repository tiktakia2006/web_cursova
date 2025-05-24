from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from .models import Post, Profile, Comment, Route

User = get_user_model()

class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 2,
        'placeholder': 'Залишити коментар...'
    }), label='')

    class Meta:
        model = Comment
        fields = ['content']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['caption', 'image']

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Введіть дійсний email")
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['avatar']

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['start_location', 'end_location', 'description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class SettingsForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Новий пароль', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Підтвердження пароля', widget=forms.PasswordInput, required=False)

    class Meta:
        model = Profile
        fields = ['avatar']

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("password1")
        pw2 = cleaned_data.get("password2")

        if pw1 or pw2:
            if pw1 != pw2:
                raise forms.ValidationError("Паролі не співпадають.")
        return cleaned_data

