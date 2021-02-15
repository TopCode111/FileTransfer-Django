from django.conf import settings
from rest_framework import serializers
from dashboard.models import Profile

def validate_file_size(file, request):
    file_size = request.user.profile.file_size
    if file.size > file_size:
        raise serializers.ValidationError('File size is bigger')