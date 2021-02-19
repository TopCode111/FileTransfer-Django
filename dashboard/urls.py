from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import include
from django.views.generic import TemplateView
from .views.user import (DashboardView, userreject, SignUp, ProfileUpdateView, PasswordUpdateView, ProjectDeleteView,DashboardInfiniteScroll,
                        get_acquaintances, filesizeupdate, save_filesizeupdate, add_userreject, delete_userreject,upload_files,set_zipfile_name,get_batch,get_files_as_zip)
from .forms import ProfiledAuthenticationForm,PasswordResetFormUpdate
from django.urls import reverse_lazy

app_name = "dashboard"

urlpatterns = [
    # path('', TemplateView.as_view(template_name="dashboard/home.html"), name="homepage"),
    path('',DashboardView.as_view(), name="homepage"),
    path('home/infinite-scroll/',DashboardInfiniteScroll.as_view(), name="dashboardInfiniteScroll"),  
    path('userreject/', userreject, name="userreject"),
    path('add_userreject/', add_userreject, name="add_userreject"),
    path('delete_userreject/', delete_userreject, name="delete_userreject"),
    path('volumn/', filesizeupdate, name='volumn'),
    path('update_file_size', save_filesizeupdate, name="save_filesizeupdate"),
    path('upload_files',upload_files,name='upload_files'),
    path('set_zipfile_name',set_zipfile_name,name='set_zipfile_name'),

    path('login/', auth_views.LoginView.as_view(form_class=ProfiledAuthenticationForm, redirect_authenticated_user=True), name="login"),
    path('signup/', SignUp.as_view(), name="signup"),
    path('password_change/', PasswordUpdateView.as_view(), name='password_change'),
    path('password-reset/',auth_views.PasswordResetView.as_view(form_class=PasswordResetFormUpdate,success_url=reverse_lazy('dashboard:password_reset_done')),name='password_reset'),
    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('dashboard:password_reset_complete')),name='password_reset_confirm'),
    path('password-reset/complete/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),
    path('logout/',auth_views.LogoutView.as_view(),name='logout'),
    path('profile/', ProfileUpdateView.as_view(), name="profile"),

    path('acquaintances/', get_acquaintances, name="acquaintances"),
    path('project/<int:project_id>/delete', ProjectDeleteView.as_view(), name="projectDelete"),
    # path('', include('django.contrib.auth.urls'))
    path('<uuid:batch_id>',get_batch,name='get_batch'),
    path('get_files_as_zip',get_files_as_zip,name='get_files_as_zip')
]