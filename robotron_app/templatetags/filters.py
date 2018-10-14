import datetime
from django import template
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