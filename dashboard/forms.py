from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Project
from django.utils.translation import ugettext, ugettext_lazy as _
from django.forms import formset_factory
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.template import loader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

from django.contrib.auth.forms import (
    AuthenticationForm,PasswordResetForm,UsernameField
)

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(label="メールアドレス", required=True)
    
    password1 = forms.CharField(label='パスワード', required=True, strip=False, widget=forms.PasswordInput())
    password2 = forms.CharField(label='パスワード確認', required=True, strip=False, widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def clean(self):
        super(UserCreateForm, self).clean()
        try:
            user = User.objects.get(email=self.cleaned_data['email'])
            raise forms.ValidationError("A user with this E-mail address already exists.")
        except User.DoesNotExist:
            pass

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        
        user.save()
        return user

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("title",)

class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("title", )

class ProfiledAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        label=_("メールアドレス"),
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True,'placeholder': 'メールアドレス'}),
    )
    password = forms.CharField(
        label=_("パスワード"),
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'パスワード'}),
    )
    #remember_me = forms.BooleanField(required=False,widget=forms.CheckboxInput(attrs={'class':'scalero-checkbox','id':'remember-me'}))
    profile_error_messages = {
        "invalid_profile": _("メールアドレスまたはパスワードが正しくありません。"
        )
    }

    def clean(self):
        super(ProfiledAuthenticationForm, self).clean()
        if self.user_cache:
            if not self.user_cache.profile.can_login:
                raise forms.ValidationError(
                    self.profile_error_messages['invalid_profile'],
                    code='invalid_profile',
                    params={'username': self.username_field.verbose_name},
                )
class PasswordResetFormUpdate(PasswordResetForm):
    email = UsernameField(
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True,'placeholder': 'メールアドレス'}),
    )
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        subject = "パスワード再設定"
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        #message = Mail(from_email=settings.EMAIL_FROM,to_emails=to_email,subject=subject,html_content=body)
        url = reverse_lazy('dashboard:password_reset_confirm',kwargs={'uidb64':context['uid'],'token':context['token']})        
        confirm_url = str(context['protocol'])+'://'+str(context['domain'])+str(url)
        html_body = render_to_string("registration/password_reset_email.html", {'url':confirm_url})
        
        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
        except Exception as e:
            print(e)