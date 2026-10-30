from django import forms
from .models import Comment, ContactMessage, Subscriber


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("name", "email", "content")


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")


class SubscriberForm(forms.ModelForm):
    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    class Meta:
        model = Subscriber
        fields = ("email",)
