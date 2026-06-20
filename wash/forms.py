from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Booking, Review, ServicePackage


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service_package', 'vehicle_type', 'appointment_date', 'appointment_time', 'notes']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.Select(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_appointment_date(self):
        date = self.cleaned_data['appointment_date']
        if date < timezone.now().date():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return date


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your experience with us (optional)...',
            }),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
