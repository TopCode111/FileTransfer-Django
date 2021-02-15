from dashboard.forms import UserCreateForm, ProfiledAuthenticationForm
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect, reverse, HttpResponseRedirect, render, HttpResponse
from django.http import JsonResponse
import json
from django.utils.http import urlencode
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.contrib.auth import update_session_auth_hash
from dashboard.models import Project, Profile
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe
from urllib.parse import urlencode

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
#from django.core.mail import send_mail
#from django.core.mail import EmailMultiAlternatives

from django.db import transaction
from django.views.generic import TemplateView,FormView
from django.views.generic.base import View
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.loader import render_to_string
from django.template import RequestContext
import datetime
from django.utils import timezone
from django.contrib.auth import views as auth_views
from dashboard.models import Profile, Project, RejectUser

class DashboardView(auth_views.LoginView):
    template_name = "dashboard/home.html"
    form_class = ProfiledAuthenticationForm
    def get(self, request, *args, **kwargs):
        # context = {'form': self.form_class()}
        context = self.get_context_data()
        context['form'] = self.form_class()
        return render(request, self.template_name, context)

class DashboardInfiniteScroll(View):

    def get(self, request, *args, **kwargs):
        #limit = int(self.request.GET.get('limit'))
        page = self.request.GET.get('page')
        sort = self.request.GET.get('sort')
        available_item = self.request.GET.get('available_item')

        _projects=[]
        start = 1
        if page == '1':
            start = 0
        else:
            start = int(available_item)

        _projects = _projects

        #projects = _projects[start:start+limit]

        html = render_to_string("dashboard/home.html",{'projects':_projects,'start':start,'user':self.request.user},request=request)
        return JsonResponse({'status':'success','html':html,'total_items': len(_projects)})

class SignUp(generic.CreateView):
    redirect_authenticated_user = True
    form_class = UserCreateForm
    template_name = 'registration/signup.html'
    
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, 'Your account was created successfully! Please log in to continue.')
        if self.request.GET.get("next", None):
            return reverse('dashboard:login') + "?" + urlencode({"next": self.request.GET.get('next')})
        return reverse('dashboard:login')

    def get_initial(self):
        email = self.request.GET.get("email")
        first_name = self.request.GET.get("first_name")
        last_name = self.request.GET.get("last_name")
        return { 'email': email, 'first_name': first_name, 'last_name': last_name }
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:homepage')
        return super(SignUp, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'form': self.form_class()}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            
            user = form.save()
            if 'user_avatar' in request.FILES:
                avatar = request.FILES.get('user_avatar')
                user.profile.avatar = avatar
                user.profile.save()
                
            return HttpResponseRedirect(self.get_success_url())

        return render(request, self.template_name, {'form': form})

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfiledAuthenticationForm
    template_name = 'dashboard/profile.html'

    def get_success_url(self):
        return reverse('dashboard:profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(ProfileUpdateView, self).get_context_data(**kwargs)
        if 'pw_form' not in context:
            context['pw_form'] = PasswordChangeForm(user=self.request.user)
        context['form'] = self.form_class(instance=self.get_object())
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        ctxt = {}
        if 'profile_form' in request.POST:
            print("Checking profile form")
            form = self.form_class(request.POST, instance=self.object)
            if form.is_valid():
                messages.add_message(self.request, messages.SUCCESS, 'Profile updated successfully.')
                user=form.save()
                if 'user_avatar' in request.FILES:
                    avatar = request.FILES.get('user_avatar')
                    user.profile.avatar = avatar
                    user.profile.save()
            else:
                ctxt['form'] = form

        elif 'pw_form' in request.POST:
            print("Checking pw form")
            pw_form = PasswordChangeForm(user=request.user, data=request.POST)
            if pw_form.is_valid():
                print("pw_form is valid")
                messages.add_message(self.request, messages.SUCCESS, 'Password changed successfully.')
                pw_form.save()
                update_session_auth_hash(self.request, pw_form.user)
            else:
                print(pw_form.errors)
                ctxt['pw_form'] = pw_form
        
        return render(request, self.template_name, self.get_context_data(**ctxt))


class PasswordUpdateView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'dashboard/profile.html'

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, 'Password changed successfully.')
        return reverse('dashboard:profile')

    def form_invalid(self, form):
        if form.errors:
            pass
        return redirect('dashboard:profile')

@require_http_methods(["POST"])
@login_required
def get_acquaintances(request):
    res = []
    members = request.user.profile.acquaintances
    for member in members:
        attrs = []
        if member == request.user:
            attrs.append("Yourself")
        else:
            attrs.append("New Member")
        
        attr = " | ".join(attrs)
        name = member.profile.display_name
        email = member.email
        u = {
            "username": email,
            "fullname": name,
            "status": attr
        }
        res.append(u)
    return HttpResponse(json.dumps(res), content_type="application/json")


class ProjectDeleteView(generic.DeleteView):
    http_method_names = ['post']
    model = Project
    pk_url_kwarg = "project_id"

    def get_success_url(self):
        return reverse("dashboard:homepage")

@login_required
def filesizeupdate(request):
    users = {}
    users = User.objects.all()
    return render(request, 'dashboard/volumn.html', context={'users': users})

@login_required
def save_filesizeupdate(request):
    file_size = request.POST.get('file_size')
    profile = request.POST.get('profile_id')
    
    data = Profile.objects.get(id = profile)
    data.file_size = file_size
    data.save()
    return JsonResponse({'success': True})

@login_required
def userreject(request):
    reject_user = RejectUser.objects.all()
    return render(request, 'dashboard/userreject.html', context={"RejectUser": reject_user})

@require_http_methods(["POST"])
@login_required
def add_userreject(request):
    email = request.POST.get('email')
    if email:
        try:
            reject_user = RejectUser.objects.filter(email=email)
            if reject_user.exists():
                messages.add_message(request, messages.ERROR, "登録簿に既に追加されました。")
            else:
                reject_user = RejectUser()
                reject_user.email = email
                reject_user.save()
                messages.add_message(request, messages.SUCCESS, "追加が成功しました。")
        except RejectUser.DoesNotExist:
            messages.add_message(request, messages.ERROR, "ERROR")
            #url = reverse("dashboard:userreject")
            #kwargs = {
            #    "email": email
            #}
            #params = urlencode(kwargs)
            #return HttpResponseRedirect(url+ "?" +params)
    else:
        messages.add_message(request, messages.ERROR, "メールアドレスをインプットしてください。")
    return redirect("dashboard:userreject")

@login_required
def delete_userreject(request):
    rejectuser_id = request.POST.get('id')
    
    if rejectuser_id is not None:
        email = RejectUser.objects.get(id=rejectuser_id)
        email.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})
