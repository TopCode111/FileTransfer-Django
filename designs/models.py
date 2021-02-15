from django.db import models
import uuid
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import Count
import mimetypes
# Create your models here.

class Design(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField("dashboard.Project", on_delete=models.CASCADE)
    pub_date = models.DateTimeField(_("Date published"),editable=False, auto_now_add=True)
    due_date = models.DateField(_("Date needed by"),null=True,blank=True,default=None)
    description = models.TextField(_("Design description"),default=None,null=True,blank=True)
    last_updated = models.DateTimeField(_("Last updated"), editable=False, auto_now=True)

    def __str__(self):
        return self.project.title

    @property
    def last_version(self):
        return self.versiongroup_set.count()
    
    @property
    def latest_version(self):
        return self.versiongroup_set.annotate(version_count=Count("version")).filter(version_count__gt=0).first()

    @property
    def imageset(self):
        return [i for i in self.designfile_set.all() if i.content_type and "image/" in i.content_type]

    @property
    def fileset(self):
        return [i for i in self.designfile_set.all() if not i.content_type or not "image/" in i.content_type]

    @property
    def no_of_files(self):
        return self.designfile_set.count()

    
    def delete(self, *args, **kwargs):
        if not hasattr(self.project, 'ticket'):
            self.project.delete()
        super(Design, self).delete(*args, **kwargs)

class DesignFile(models.Model):
    file = models.FileField(upload_to="design_assets")
    filename = models.CharField(_("Original filename"), max_length=1000)
    design = models.ForeignKey(Design, on_delete=models.CASCADE)

    @property
    def content_type(self):
        return mimetypes.guess_type(self.filename, strict=True)[0]

    @property
    def file_size(self):
        return (self.file.size/1000000)

class VersionGroupManager(models.Manager):
    def get_queryset(self):
        return super(VersionGroupManager, self).get_queryset().annotate(version_count=Count("version")).filter(version_count__gt=0)

class VersionGroup(models.Model):
    class Meta:
        ordering = ['-version_no']
    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    version_no = models.IntegerField(_("Version #"), editable=False)
    pub_date = models.DateTimeField(_("Date uploaded"),editable=False, auto_now_add=True)
    objects = VersionGroupManager()

    def __str__(self):
        return f"{self.design.project.title} : VersionGroup {self.version_no }"

    def increment_version_number(self):
        last_version = self.design.versiongroup_set.first()
        if not last_version:
            return 1
        version_no = last_version.version_no
        new_version_no = version_no + 1
        return new_version_no

    def save(self, *args, **kwargs):
        if self.version_no is None:
            self.version_no = self.increment_version_number()
        super(VersionGroup, self).save(*args, **kwargs)    

class Version(models.Model):
    class Meta:
        ordering = ['version_label']
    version_group = models.ForeignKey(VersionGroup, on_delete=models.CASCADE)
    version_label = models.CharField(_("Version Label"), max_length=256, blank=True)
    asset = models.ImageField(_("Design Asset"), upload_to="design_assets")
    upload_date = models.DateTimeField(_("Date uploaded"),editable=False, auto_now_add=True)

    def __str__(self):
        return f"{self.version_group.design.project.title} : Version {self.version_group.version_no } {self.version_label}"

    def save(self, *args, **kwargs):
        if not self.version_label:
            self.version_label = self.increment_version_label()
        super(Version, self).save(*args, **kwargs)

    def increment_version_label(self):
        last_version = self.version_group.version_set.all().order_by('id').last()
        if not last_version:
            return "A"
        version_label = last_version.version_label
        new_version_label = chr(ord(version_label) + 1)
        return new_version_label

