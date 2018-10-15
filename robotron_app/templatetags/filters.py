import datetime
from django import template
from robotron_app.models import Studio
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
    return user.groups.filter(name='Roboto Users').exists()

@register.filter
def hasStudio(user):
    try:
        studio = Studio.objects.get(user=user)
        print(f'found: {studio}')
        return studio
    except Exception as e:
        print(e)
        pass
    return None