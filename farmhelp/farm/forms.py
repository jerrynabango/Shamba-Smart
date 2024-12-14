from django import forms
from .models import Comment, CustomUser, BlogPost, MarketListing, DirectMessage, Order
from django.contrib.auth.forms import UserChangeForm, UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2',
                  'profile_picture']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']


class ProfileEditForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone_number', 'profile_picture',
                  'bio', 'location', 'linkedin', 'x', 'facebook', 'whatsapp']

    phone_number = forms.CharField(max_length=15, required=False)
    profile_picture = forms.ImageField(required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    location = forms.CharField(max_length=255, required=False)
    linkedin = forms.URLField(required=False)
    x = forms.URLField(required=False)
    facebook = forms.URLField(required=False)
    whatsapp = forms.CharField(max_length=15, required=False)


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content']


# forms.py
class MarketListingForm(forms.ModelForm):
    class Meta:
        model = MarketListing
        fields = ['image', 'product_name', 'description', 'price', 'currency',
                  'status']

    currency = forms.ChoiceField(
        choices=[('USD', 'USD'), ('KES', 'KES'), ('EUR', 'EUR')],
        required=True,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-md'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and not self.instance.pk:
            self.fields['currency'].initial = 'KES'


class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['quantity', 'name', 'location', 'phone_number']
