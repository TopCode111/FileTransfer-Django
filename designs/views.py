from django.shortcuts import render, Http404, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .forms import DesignForm, VersionForm, VersionGroupForm, UpdateVersionForm
from .models import *
from designs.forms import ProjectDesignForm
from dashboard.forms import ProjectForm, ProjectAdminForm
from dashboard.models import Project
import json
from techup.utils import user_can_access
from django.core.exceptions import PermissionDenied

from django.http import JsonResponse, Http404

class JSONResponseMixin:
    def render_to_json_response(self, context, **response_kwargs):
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )
    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        return context

    def form_valid(self, form, comment=None, reply=None):
        if self.request.is_ajax():
            data = form.data.copy()
            

            print(data)
            return HttpResponse(json.dumps(data), content_type='application/json')
        return super(JSONResponseMixin, self).form_valid(form)

    def form_invalid(self, form):
        print("MIXIN FORM_INVALid")
        if self.request.is_ajax():
            return HttpResponse(json.dumps(form.errors), content_type='application/json', status=400)
        return super(JSONResponseMixin, self).form_valid(form)

# Create your views here.
def index(request):
    return render(request, 'designs/base.html', context={"project_form": ProjectAdminForm()})

@require_POST
def uploadDesign(request):
    is_admin = request.user.profile.is_admin
    is_staff = request.user.profile.is_staff
    design_form = DesignForm(request.POST)
    
    version_group_form = VersionGroupForm(request.POST)
    
    if is_admin or is_staff:
        project_form = ProjectAdminForm(request.POST)
    else:
        project_form = ProjectForm(request.POST)
    # Flow # 1: Direct design upload
    if design_form.is_valid() and version_group_form.is_valid() and project_form.is_valid() and request.FILES:
        # Create project
        project_form.instance.user = request.user
        if not is_admin | is_staff:
            project_form.instance.team = request.user.profile.team
        project = project_form.save()
        # Create design
        design_form.instance.project = project
        design = design_form.save()
        # Create Version Group
        version_group_form.instance.design = design
        version_group = version_group_form.save()
        # Create versions from files
        for file in request.FILES:
            file = request.FILES[file]
            version = Version(asset=file)
            version.version_group = version_group
            version.save()
        resp = HttpResponse(f'{{"message": "Uploaded successfully...", "id": "{design.id}"}}')
        resp.status_code = 200
    else:
        resp = HttpResponse(json.dumps(design_form.errors))
        resp.status_code = 400
    resp.content_type = "application/json"
    return resp