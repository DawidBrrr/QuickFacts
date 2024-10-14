from django import forms

class LinkForm(forms.Form):
    link = forms.URLField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter a link...',
            'class': 'form-control',
        }),
        required=True  
    )