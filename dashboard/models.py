from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django.apps import apps

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# Create your models here.
from django.contrib.auth.models import User
from django.contrib.auth.models import UserManager

from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(_("Is Admin?"), default=False)
    avatar =  models.ImageField(_("user avatar"), upload_to="user_avatars",blank=True, null=True,default=None)
    file_size = models.IntegerField(default=settings.MAX_UPLOAD_SIZE)

    @property
    def display_name(self):
        name = "Unnamed User"
        #if self.user.first_name:
        #    name = self.user.first_name
        #if self.user.last_name:
        #    name += " " + self.user.last_name + "."
        return name

    @property
    def can_login(self):
        return self.user

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(_("Project Title"), max_length=256)
    pub_date = models.DateTimeField(_("Date added"),editable=False, auto_now_add=True)

    # class Meta:
    #     ordering = ['id']

class RejectUser(models.Model):
    email = models.EmailField(_('E-mail address'), blank=False)
    applied = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.save()


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()