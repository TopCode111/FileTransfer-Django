from django import forms
from .models import *

class DesignForm(forms.ModelForm):
    class Meta:
        model = Design
        fields = []

class ProjectDesignForm(forms.ModelForm):
    class Meta:
        model = Design
        fields = ['project']

class VersionGroupForm(forms.ModelForm):
    class Meta:
        model = VersionGroup
        fields = []

class VersionForm(forms.ModelForm):
    class Meta:
        model = Version
        fields = ['asset']

class UpdateVersionForm(forms.ModelForm):
    class Meta:
        model = VersionGroup
        fields = ['design']