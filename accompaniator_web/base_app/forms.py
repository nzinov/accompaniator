from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    song_name = forms.CharField()
    rating = forms.Select()

    class Meta:
        model = Feedback
        fields = ('song_name', 'rating',)
