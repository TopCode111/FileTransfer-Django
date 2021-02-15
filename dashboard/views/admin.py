from dashboard.models import User
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.contrib import messages
from django.shortcuts import render, redirect, HttpResponse
import json
from django.contrib.auth.decorators import user_passes_test

from django.views.decorators.http import require_http_methods
from django.urls import reverse_lazy


def is_admin(user):
    return user.profile.is_admin

   