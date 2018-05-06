from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    rating = forms.Select()

    class Meta:
        model = Feedback
        fields = ('rating',)
