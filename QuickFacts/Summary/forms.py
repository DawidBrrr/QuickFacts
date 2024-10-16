from django import forms

class LinkForm(forms.Form):
    link = forms.URLField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Wprowadź link',
            'class': 'form-control',
        }),
        required=True,
        error_messages={
            'required': 'To pole jest wymagane.',  
            'invalid': 'Wprowadź prawidłowy adres URL.',  
            'max_length': 'Maksymalna długość wynosi 255 znaków.',  
        }  
    )