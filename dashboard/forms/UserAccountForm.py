from django import forms
from accounts.models.Customer import Customer

class UserAccountForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('username', 'first_name', 'last_name', 'email')
        
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'pf-input', 'autocomplete': 'username'}),
            'first_name': forms.TextInput(attrs={'class': 'pf-input', 'placeholder': 'Votre prénom'}),
            'last_name':  forms.TextInput(attrs={'class': 'pf-input', 'placeholder': 'Votre nom de famille'}),
            'email':      forms.EmailInput(attrs={'class': 'pf-input', 'placeholder': 'votre@email.com', 'autocomplete': 'email'}),
        }
