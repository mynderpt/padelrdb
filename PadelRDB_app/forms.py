from django import forms
from .models import Review, Brand, Racket, CustomUser

class ReviewForm(forms.ModelForm):
    brand = forms.ModelChoiceField(queryset=Brand.objects.all(), empty_label="Select Brand", widget=forms.Select(attrs={'id': 'id_brand'}))
    racket = forms.ModelChoiceField(queryset=Racket.objects.none(), empty_label="Select Model", widget=forms.Select(attrs={'id': 'id_model'}))

    class Meta:
        model = Review
        fields = ['power', 'control', 'comfort', 'agility', 'spin', 'hard', 'exit', 'comment', 'racket']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your review...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['racket'].queryset = Racket.objects.filter(brand_id=brand_id).order_by('name')
            except (ValueError, TypeError):
                pass  
        elif self.instance.pk:
            self.fields['racket'].queryset = self.instance.racket.brand.racket_set.all().order_by('name')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_image']