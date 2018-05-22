from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    song_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    mark = forms.IntegerField(widget=forms.HiddenInput(), required=False, initial=-1)

    class Meta:
        model = Feedback
        fields = ('song_name', 'mark',)
