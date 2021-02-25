from dashboard.forms import UserCreateForm, ProfiledAuthenticationForm
from django.views.decorators.http import require_POST
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
from dashboard.models import Profile, Project, RejectUser ,Batch, BatchFile,PaymentHistory
import os
import zipfile
from io import StringIO
from io import BytesIO
import requests
from django.views.decorators.csrf import csrf_exempt
import stripe

class DashboardView(auth_views.LoginView):
    template_name = "dashboard/home.html"
    form_class = ProfiledAuthenticationForm
    def get(self, request, *args, **kwargs):
        # context = {'form': self.form_class()}
        context = self.get_context_data()
        context['form'] = self.form_class()

        if request.user.is_authenticated:
            maxfilesize = request.user.profile.remaining_space / 1000000
            context['maxfilesize'] = maxfilesize
        
        users = User.objects.all()
        reject_users = RejectUser.objects.all()
        user_all_num = int(users.count()) + int(reject_users.count())
        context['users'] = users
        context['reject_users'] = reject_users
        context['user_all_num'] = user_all_num
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

@login_required
def payment(request):
    return render(request, 'dashboard/payment.html', context={})

@login_required
def payment_history(request):
    payment_history = PaymentHistory.objects.all()
    return render(request, 'dashboard/payment_history.html', context={'payment_history':payment_history})

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        plan_id = request.GET.get('plan_id')
        user = request.user
        name = ''
        if plan_id=='1':
            name = 'Free'
            price = 0
            user = request.user
            user.profile.file_size = user.profile.file_size + 4000
            user.profile.save()
            user.save()
            payment = PaymentHistory()
            payment.user = user
            payment.storage = 4000
            payment.price = 0
            payment.save()
            return JsonResponse({'success':True})
        if plan_id=='2':
            name = '100￥'
            price = 100
        # domain_url = 'http://localhost:8003/'
        domain_url = request.scheme+'://'+request.META['HTTP_HOST']+'/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}&plan_id='+plan_id,
                cancel_url=domain_url + 'payment/cancelled/',
                payment_method_types=['card'],
                customer_email=request.user.email,
                mode='payment',
                line_items=[
                    {
                        'name': name,
                        'quantity': 1,
                        'currency': 'JPY',
                        'amount': int(price),
                    }
                ],
                metadata={'plan_id':plan_id},
                client_reference_id = request.user.id
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':

        data = event['data']['object']
        user_id = data['client_reference_id']
        user = User.objects.get(id=user_id)
        plan_id = int(data['metadata']['plan_id'])

        if int(plan_id) == 2:
            user.profile.file_size = user.profile.file_size + 5368706371
            user.profile.save()
            user.save()
            payment = PaymentHistory()
            payment.user = user
            payment.storage = 5368706371
            payment.price = 100
            payment.save()


    return HttpResponse(status=200)

class SuccessView(generic.TemplateView):
    template_name = 'dashboard/payment_success.html'

    def get(self, request, *args, **kwargs):
        plan_id = request.GET.get('plan_id')
        if plan_id == '1':
            file_space = 4000
        elif plan_id == '2':
            file_space = 5368706371
        return render(request,self.template_name,{'file_space':file_space})

class CancelledView(generic.TemplateView):
    template_name = 'dashboard/payment_cancelled.html'

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

@require_POST
def upload_files(request):
    batch = Batch()
    batch.user = request.user
    batch.save()

    for file in request.FILES:
        file = request.FILES[file]
        batch_file = BatchFile(file=file)
        batch_file.batch = batch
        batch_file.size = file.size
        batch_file.save()

    remaining_space_in_mb = request.user.profile.remaining_space / 1000000
    remaining_space = request.user.profile.remaining_space

    resp = HttpResponse(f'{{"message": "Uploaded successfully...", "id": "{batch.id}","remaining_space_in_mb": "{remaining_space_in_mb}","remaining_space": "{remaining_space}"}}')
    resp.status_code = 200
    resp.content_type = "application/json"
    return resp

@require_POST
def set_zipfile_name(request):
    batch_id = request.POST.get('batch_id')
    name = request.POST.get('name')
    batch = Batch.objects.get(id=batch_id)
    batch.name = name
    batch.save()
    url = request.scheme+'://'+request.get_host()+'/'+str(batch.id)
    return JsonResponse({'success':True,'url':url})

def get_batch(request,batch_id):
    batch = Batch.objects.get(id=batch_id)
    return render(request, 'dashboard/batch.html', context={'batch': batch})

def get_files_as_zip(request):
    batch_id = request.GET.get('batch_id')
    batch = Batch.objects.get(id=batch_id)
    zip_filename = batch.name + '.zip'

    if "AWS_STORAGE_BUCKET_NAME" in os.environ:
        s3files =[]
        for file in batch.batchfile_set.all():
            s3files.append(file.file.url)

        byte_data = BytesIO()
        zip_file = zipfile.ZipFile(byte_data, "w")
        for s3file in s3files:
            filename = s3file.split('/')[-1]
            response = requests.get(s3file)
            zip_file.writestr(filename, response.content)
        zip_file.close()
    else:
        filenames = []
        for file in batch.batchfile_set.all():
            filenames.append(file.file.path)

        byte_data = BytesIO()
        zip_file = zipfile.ZipFile(byte_data, "w")
        for file in filenames:
            filename = os.path.basename(os.path.normpath(file))
            zip_file.write(file, filename)
        zip_file.close()

    response = HttpResponse(byte_data.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return response

def get_remaining_space(request):
    remaining_space_in_mb = request.user.profile.remaining_space / 1000000
    remaining_space = request.user.profile.remaining_space
    return JsonResponse({'remaining_space':remaining_space,'remaining_space_in_mb':remaining_space_in_mb})