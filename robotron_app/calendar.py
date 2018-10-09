from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from itertools import groupby
from calendar import HTMLCalendar, monthrange
from datetime import date, datetime, timedelta
from django.shortcuts import render
from robotron_app.models import Session
import json


def get_sessions_for_month(month):
    month_sessions = Session.objects.filter(day__month=month).filter(day__isnull=False)
    events_dict = {}
    i = 1
    for m in month_sessions:
        day = m.day.day
        project = m.batch.project.name
        character = m.character.name
        actor = m.character.actor.name
        batch = m.batch.name
        start_time = datetime.combine(m.day, m.hour)
        end_time = start_time + timedelta(hours=m.duration)
        if m.translator == None:
            category = -1
            translator = 'UNASSIGNED'
        else:
            category = m.translator_id
            translator = m.translator.name
        # director = m.director.name
        try:
            elem = len(events_dict[day].keys())
            # print(len(elem))
            events_dict[day][elem+1] = {
                'event_category': category,
                'event_title': f'{project}: {character}({batch})',
                'event_start': str(start_time),
                'event_end': str(end_time),
                'event_body': translator,
                'event_duration':start_time.strftime("%H:%M")+'-'+end_time.strftime("%H:%M")
            }

        except KeyError:
            # print(f'adding first event for day: {day}')
            events_dict[day] = {}
            events_dict[day][1] = {
                'event_category': category,
                'event_title': f'{project}: {character} ({batch})',
                'event_start': str(start_time),
                'event_end': str(end_time),
                'event_body': translator,
                'event_duration': start_time.strftime("%H:%M") + '-' + end_time.strftime("%H:%M")
            }
            pass

    # print(events_dict)
    # print(json.dumps(events_dict, indent=4, sort_keys=True))
    return events_dict


        # print('=====')
        # print(f'{project}: {character}({batch})')
        # print('---------------')
        # print('{:%a %d-%m-%Y }' .format(start_time))
        # print('{:%H:%M}' .format(start_time), '-{:%H:%M}'.format(end_time))
        # print(f'tanslator: {translator}')
        # print(f'actor: {actor}')


def color_pill(int):
    if int == -1:
        return 'badge-secondary'
    if int == 0:
        return 'badge-primary'
    elif int == 1:
        return 'badge-info'
    elif int == 2:
        return 'badge-success'
    elif int == 3:
        return 'badge-danger'
    elif int == 4:
        return 'badge-warning'
    elif int == 5:
        return 'badge-info'
    else:
        return 'badge-dark'


def generate_day_events(day, event_list):
#     content that goes inside event-container
    event_text = ''
    if day in event_list.keys():
    #     iterate over list
        for k in event_list[day].values():
            category = color_pill(k['event_category'])
            title = k['event_title']
            body = k['event_duration']+' '+k['event_body']

            # link = k['event_link']
            link = '#'
            # event_text += f'<a href="{link}" class="m-0 badge badge-pill {category}"> </a>\n'
            event_text += f'<a tabindex="0" data-toggle="popover" data-placement="bottom" data-trigger="focus"' \
                          f' title="{title}" data-content="{body}" class="m-0 event-pill badge badge-pill {category}"> </a>\n'

    return event_text


def generate_month_manual(year_number=(datetime.now().year), month_number=(datetime.now().month)):

    get_sessions_for_month(month_number)

    start_day = monthrange(year_number,month_number)[0]
    month_length = monthrange(year_number,month_number)[1]
    month_names = {
        1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June',
        7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'
    }
    day_titles = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    month_text = ''
    month_text += '<table class="table table-hover table-responsive" id="calendar_month"><thead class="thead-light">'+'\n'
    month_text += '<tr class="text-center align-middle">'+'\n'
    month_text += '<th colspan="1"><a role="button" id="nav_prev" class="btn btn-sm btn-outline-secondary" href="#"> << </a></th>'+'\n'
    month_text += '<th colspan="5" class="month_title">'+month_names[month_number]+' '+str(year_number)+'</th>'+'\n'
    month_text += '<th colspan="1"><a role="button" id="nav_next" class="btn btn-sm btn-outline-secondary" href="#"> >> </a></th>' + '\n'
    month_text += '</tr>'+'\n'
    month_text += '<tr>'+'\n'

    for day_title in day_titles:
        month_text+='<th scope="col" class="day_title">'+day_title+'</th>'+'\n'

    month_text += '</tr></thead>'+'\n'
    month_text += '<tbody>'+'\n'
    month_text += '<tr class="row_clickable">'+'\n'

    # pre-month empty cells
    for i in range(0, start_day):
        month_text += '<td class="day"></td>' + '\n'

    day = 1

    # TEST

    events_list = {
        3: {
            1: {
                'event_category':'badge-primary',
                'event_title':'SomeTitle',
                'event_body':'MoreLettersDesc',
                'event_link':'SomeURL'
            },
            2: {
                'event_category':'badge-success',
                'event_title':'SomeTitle',
                'event_body':'MoreLettersDesc',
                'event_link':'SomeURL'
            },
            3: {
                'event_category':'badge-success',
                'event_title':'SomeTitle3',
                'event_body':'MoreLettersDesc3',
                'event_link':'SomeURL3'
            },
        },
        4: {
            1: {
                'event_category': 'badge-primary',
                'event_title': 'SomeTitle',
                'event_body': 'MoreLettersDesc',
                'event_link': 'SomeURL'
            }
        },
        10: {
            1: {
                'event_category': 'badge-danger',
                'event_title': 'SomeTitle',
                'event_body': 'MoreLettersDesc',
                'event_link': 'SomeURL'
            }
        },
        15: {
            1: {
                'event_category': 'badge-primary',
                'event_title': 'SomeTitle',
                'event_body': 'MoreLettersDesc',
                'event_link': 'SomeURL'
            }
        },
        22: {
            1: {
                'event_category': 'badge-warning',
                'event_title': 'SomeTitle',
                'event_body': 'MoreLettersDesc',
                'event_link': 'SomeURL'
            }
        },
        25: {
            1: {
                'event_category': 'badge-success',
                'event_title': 'SomeTitle',
                'event_body': 'MoreLettersDesc',
                'event_link': 'SomeURL'
            }
        }
    }
    events_list = get_sessions_for_month(month_number)

    for i in range(start_day, 7):
        day_id = str(year_number) + '-' + str(month_number) + '-' + str(day)
        event_text = generate_day_events(day,events_list)
        month_text += '<td class="day day-clickable" id="' + day_id + '">\n<div>' + str(day) + '</div>\n' \
            '<div class="event-container justify-content-start m-0">\n'+event_text+'\n</div>\n</td>\n'

        day += 1

    month_text += '</tr>' + '\n'

    number_of_rows = 1
    while (number_of_rows < 6):
        month_text += '<tr class="row_clickable">' + '\n'
        number_of_rows += 1

        for i in range(0, 7):
            if (day <= month_length):
                day_id = str(year_number) + '-' + str(month_number) + '-' + str(day)
                event_text = generate_day_events(day, events_list)
                month_text += '<td class="day day-clickable" id="' + day_id + '">\n<div>' + str(day) + '</div>\n' \
                               '<div class="event-container justify-content-start m-0">\n' + event_text + '\n</div>\n</td>\n'
                day += 1
            else:
                month_text += '<td class="day"></td>' + '\n'

        month_text += '</tr>' + '\n'

    month_text += '</tbody></table>'+'\n'

    # print(month_text)
    return month_text

def calendar_current(request):

    today = datetime.now()
    return calendar(request, today.year,  today.month)


def calendar(request, year, month):
    manual_calendar = generate_month_manual(year, month)
    nav_year_prev = year
    nav_year_next = year

    nav_month_prev = month - 1
    if nav_month_prev == 0:
        nav_month_prev = 12
        nav_year_prev = year - 1

    nav_month_next = month + 1
    if nav_month_next == 13:
        nav_month_next = 1
        nav_year_next = year + 1

    context = {
        'calendar':mark_safe(manual_calendar),
        'nav_year_prev':nav_year_prev,
        'nav_year_next': nav_year_next,
        'nav_month_prev':nav_month_prev,
        'nav_month_next':nav_month_next,
        'year':year,
        'month':month,
    }
    return render(request, 'calendar.html', context=context)
