from django import template
from django.core.exceptions import ObjectDoesNotExist
import numpy as np;

register = template.Library()

@register.filter(name='add')
def add(a, b):
    return a+b
    
