from django import forms
from .models import WaiterProfile, ClientProfile

class WaiterProfileForm(forms.ModelForm):
    class Meta:
        model = WaiterProfile
        fields = ['first_name', 'last_name', 'workplace', 'goal']

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ['nickname']

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if ClientProfile.objects.filter(nickname=nickname).exists():
            raise forms.ValidationError('Nickname already exists.')
        return nickname

class PaymentMethodForm(forms.Form):
    payment_method_id = forms.CharField(max_length=255, required=True)
