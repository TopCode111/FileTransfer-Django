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
from django.db.models import Sum
from django.conf import settings
import uuid

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

    @property
    def occupied_space(self):
        all_batch = self.user.batch_set.all().values_list('id',flat=True)
        occupied_space = BatchFile.objects.filter(batch_id__in=all_batch).aggregate(Sum('size'))
        return occupied_space['size__sum']

    @property
    def remaining_space(self):
        occupied = self.occupied_space
        return (settings.MAX_UPLOAD_SIZE-occupied)


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(_("Project Title"), max_length=256)
    pub_date = models.DateTimeField(_("Date added"),editable=False, auto_now_add=True)

    # class Meta:
    #     ordering = ['id']

class RejectUser(models.Model):
    email = models.EmailField(_('E-mail address'), blank=False)
    applied = models.DateTimeField(auto_now_add=True)

class Batch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255,blank=True,null=True)

class BatchFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='files',blank=True,null=True,default=None)
    batch = models.ForeignKey(Batch,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField(default=0)




@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.save()


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()