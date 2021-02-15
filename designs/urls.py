from django.urls import path

from . import views
from .views import uploadDesign
app_name = 'designs'

urlpatterns = [

    path('', views.index, name='index'),
    path('upload', views.uploadDesign, name='uploadDesign')  

]