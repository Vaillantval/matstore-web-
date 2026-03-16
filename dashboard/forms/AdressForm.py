from django import forms
from dashboard.models.Adress import Adress

PLACEHOLDER = {
    'name':         'Ex : Domicile, Bureau…',
    'full_name':    'Prénom et nom',
    'street':       'Numéro et nom de rue',
    'code_postal':  'Code postal',
    'city':         'Ville',
    'country':      'Pays',
    'more_details': 'Appartement, étage, instructions de livraison…',
}

class AdressForm(forms.ModelForm):
    class Meta:
        model  = Adress
        fields = ('name', 'full_name', 'street', 'code_postal', 'city', 'country', 'more_details', 'adress_type')
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'ds-input', 'placeholder': PLACEHOLDER['name'], 'list': 'label-list', 'autocomplete': 'off'}),
            'full_name':    forms.TextInput(attrs={'class': 'ds-input', 'placeholder': PLACEHOLDER['full_name']}),
            'street':       forms.TextInput(attrs={'class': 'ds-input', 'placeholder': PLACEHOLDER['street']}),
            'code_postal':  forms.TextInput(attrs={'class': 'ds-input', 'placeholder': PLACEHOLDER['code_postal']}),
            'city':         forms.TextInput(attrs={'class': 'ds-input', 'placeholder': PLACEHOLDER['city']}),
            'country':      forms.TextInput(attrs={'class': 'ds-input', 'placeholder': PLACEHOLDER['country'], 'list': 'country-list', 'autocomplete': 'off'}),
            'more_details': forms.Textarea(attrs={'class': 'ds-input ds-textarea', 'placeholder': PLACEHOLDER['more_details'], 'rows': 3}),
            'adress_type':  forms.Select(attrs={'class': 'ds-input ds-select'}),
        }
        labels = {
            'name':         'Libellé',
            'full_name':    'Nom complet',
            'street':       'Adresse',
            'code_postal':  'Code postal',
            'city':         'Ville',
            'country':      'Pays',
            'more_details': 'Complément',
            'adress_type':  'Type d\'adresse',
        }
