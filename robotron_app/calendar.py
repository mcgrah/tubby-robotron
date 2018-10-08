from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from itertools import groupby
from calendar import HTMLCalendar, monthrange
from datetime import date, datetime
from django.shortcuts import render


def generate_month_manual(year_number=(datetime.now().year), month_number=(datetime.now().month)):

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

    for i in range(start_day, 7):
        # if (day in month_events.keys()):
        #     month_text += insert_event(day, month_events[day][0], month_events[day][1], month_events[day][2])
        # else:
        day_id = str(year_number)+'-'+str(month_number)+'-'+str(day)
        month_text += '<td class="day day-clickable" id="'+day_id+'">' + str(day) + '</td>' + '\n'
        day += 1

    month_text += '</tr>' + '\n'

    number_of_rows = 1
    while (number_of_rows < 6):
        month_text += '<tr class="row_clickable">' + '\n'
        number_of_rows += 1

        for i in range(0, 7):
            if (day <= month_length):
                day_id = str(year_number) + '-' + str(month_number) + '-' + str(day)
                month_text += '<td class="day day-clickable" id="' + day_id + '">' + str(day) + '</td>' + '\n'
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

# DARKLANDS BELOW
#
# def start(request):
#     """
#     Show calendar of events this month
#     """
#     lToday = datetime.now()
#     return calendar(request, lToday.year, lToday.month)
#
#
# def calendar(request, year, month):
#     """
#     Show calendar of events for specified month and year
#     """
#     lYear = int(year)
#     lMonth = int(month)
#     lCalendarFromMonth = datetime(lYear, lMonth, 1)
#     lCalendarToMonth = datetime(lYear, lMonth, monthrange(lYear, lMonth)[1])
#
#     lEvents = []
#     lCalendar = RoboCalendar(lEvents).formatmonth(lYear, lMonth)
#
#     lPreviousYear = lYear
#     lPreviousMonth = lMonth - 1
#     if lPreviousMonth == 0:
#         lPreviousMonth = 12
#         lPreviousYear = lYear - 1
#     lNextYear = lYear
#     lNextMonth = lMonth + 1
#     if lNextMonth == 13:
#         lNextMonth = 1
#         lNextYear = lYear + 1
#     lYearAfterThis = lYear + 1
#     lYearBeforeThis = lYear - 1
#
#     manual_calendar = generate_month_manual()
#
#     context = {
#         'CalendarManual':mark_safe(manual_calendar),
#         'Calendar': mark_safe(lCalendar),
#         'Month': lMonth,
#         'MonthName': named_month(lMonth),
#         'Year': lYear,
#         'PreviousMonth': lPreviousMonth,
#         'PreviousMonthName': named_month(lPreviousMonth),
#         'PreviousYear': lPreviousYear,
#         'NextMonth': lNextMonth,
#         'NextMonthName': named_month(lNextMonth),
#         'NextYear': lNextYear,
#         'YearBeforeThis': lYearBeforeThis,
#         'YearAfterThis': lYearAfterThis,
#     }
#
#     return render(request, 'calendar.html', context=context)