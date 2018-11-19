import datetime
from django import template
from robotron_app.models import Studio
from math import floor
register = template.Library()

@register.filter
def mult(value, arg):
    return int(value) * int(arg)


@register.filter
def addDays(date,days):
    newDate = date + datetime.timedelta(days=days)
    return newDate

@register.filter
def isRoboto(user):
    if user.is_superuser:
        return True
    try:
        validator = user.userprofile.studio.name
    except AttributeError:
        validator = ''
    if validator == 'ROBOTO' or validator == 'ROBOTO Translators':
        return True
    return False

@register.filter
def isTranslator(user):
    try:
        validator = user.userprofile.studio.name
    except AttributeError:
        validator = ''
    if validator == 'ROBOTO Translators':
        return True
    return False

@register.filter
def hasStudio(user):
    try:
        studio = Studio.objects.get(user=user)
        # print(f'found: {studio}')
        return studio
    except Exception as e:
        # print(e)
        pass
    return None

@register.filter
def durationMin(int):
    h = floor(int/4)
    mins = (int - h*4) * 15
    if mins > 0 and h > 0:
        return f'{h}h {mins} min'
    elif h > 0:
        return f'{h}h'
    elif mins > 0:
        return f'{mins} min'
    else:
        return '--'

@register.filter
def get_range(i):
    return range(i)