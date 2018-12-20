from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from calendar import monthrange
from datetime import date, datetime, timedelta
from django.shortcuts import render
from robotron_app.models import Session, Translator, Project
from robotron_app.views import get_navbar_data
import json


# SOON™- replace ordinary copy-paste with proper classes

def is_roboto(user):
    if user.is_superuser:
        return True
    # return user.groups.filter(name='Roboto Users').exists()
    try:
        validator = user.userprofile.studio.name
    except AttributeError:
        validator = ''
    if validator == 'ROBOTO' or validator == 'ROBOTO Translators':
        return True
    return False


def get_sessions_for_range(start_date, end_date, pk=None):
    if pk is None:
        range_sessions = Session.active.filter(day__range=(start_date, end_date)).order_by('day').order_by('hour')
    else:
        selected_project = Project.objects.get(id=pk)
        range_sessions = Session.active.filter(batch__project=selected_project).filter(
            day__range=(start_date, end_date)).order_by('day').order_by('hour')

    # only sessions with actual content
    range_sessions = range_sessions.filter(character__actor__isnull=False).filter(duration_blocks__gt=0)

    test_hours = range_sessions.filter(hour__hour__lt=7).count()
    print(f'EARLY SESSIONS COUNT: {test_hours}')

    if(test_hours > 0):
        has_rare = True
    else:
        has_rare = False

    # empty for all weekdays
    events_dict = {
        1: {},
        2: {},
        3: {},
        4: {},
        5: {},
        6: {},
        7: {}
    }

    print(f'[DEBUG]: found {range_sessions.count()} sessions')
    for m in range_sessions:
        # day = m.day.day
        weekday = m.day.isoweekday()
        project = m.batch.project.name
        character = m.character.name
        actor = m.character.actor.name
        batch = m.batch.name
        start_time = datetime.combine(m.day, m.hour)
        end_time = start_time + timedelta(minutes=(m.duration_blocks * 15))
        # timeblocks = m.duration * 60 / 15
        timeblocks = m.duration_blocks
        if m.translator is None:
            category = 0
            translator = 'UNASSIGNED'
        else:
            category = m.translator_id
            translator = m.translator.name

        content = {
            'event_project': project,
            'event_character': character,
            'event_batch': batch,
            'event_start': str(start_time),
            'event_end': str(end_time),
            'event_duration': start_time.strftime("%H:%M") + '-' + end_time.strftime("%H:%M"),
            'event_translator': translator,
            'event_actor': actor,
            'event_category': category,
            'event_timeblocks': timeblocks,
            'event_hour': m.hour,
            'event_id': m.id
        }

        try:
            elem = len(events_dict[weekday].keys())
            events_dict[weekday][elem + 1] = content

        except KeyError:
            events_dict[weekday] = {}
            events_dict[weekday][1] = content
            pass
    # print(json.dumps(events_dict, indent=4, sort_keys=True))

    result = {
        'events_dict': events_dict,
        'has_rare': has_rare
    }

    return result


def get_sessions_for_month(month, pk=None):
    if pk is None:
        month_sessions = Session.active.filter(day__month=month).filter(day__isnull=False).order_by('day', 'hour')
    else:
        selected_project = Project.objects.get(id=pk)
        month_sessions = Session.active.filter(batch__project=selected_project).filter(day__month=month).filter(
            day__isnull=False).order_by('day', 'hour')

    # only sessions with actual content
    month_sessions = month_sessions.filter(character__actor__isnull=False).filter(duration_blocks__gt=0)

    events_dict = {}

    for m in month_sessions:
        day = m.day.day
        project = m.batch.project.name
        character = m.character.name
        actor = m.character.actor.name
        batch = m.batch.name
        start_time = datetime.combine(m.day, m.hour)
        end_time = start_time + timedelta(minutes=(m.duration_blocks * 15))
        if m.translator is None:
            category = 0
            translator = 'UNASSIGNED'
        else:
            category = m.translator_id
            translator = m.translator.name

        content = {
            'event_category': category,
            'event_title': translator,
            'event_start': str(start_time),
            'event_end': str(end_time),
            'event_body': f'Project: {project}<br>Batch: {batch}<br>Character: {character}<br>Actor: {actor}',
            'event_duration': start_time.strftime("%H:%M") + '-' + end_time.strftime("%H:%M"),
            'event_id': m.id
        }

        try:
            elem = len(events_dict[day].keys())
            # print(len(elem))
            events_dict[day][elem + 1] = content

        except KeyError:
            # print(f'adding first event for day: {day}')
            events_dict[day] = {}
            events_dict[day][1] = content
            pass

    # print(events_dict)
    # print(json.dumps(events_dict, indent=4, sort_keys=True))

    return events_dict


def color_pill(int):
    if int == 0:
        return 'badge-secondary'
    return 'badge-dark'


def generate_day_events(day, event_list):
    #     content that goes inside event-container
    event_text = ''
    if day in event_list.keys():
        #     iterate over list
        for k in event_list[day].values():
            category = color_pill(k['event_category']) + ' t-' + str(k['event_category'])
            title = k['event_duration'] + ' ' + k['event_title']
            body = k['event_body']

            # link = k['event_link']
            link = '#'
            # event_text += f'<a href="{link}" class="m-0 badge badge-pill {category}"> </a>\n'
            event_text += f'<a tabindex="0" data-html="true" data-toggle="popover" data-placement="bottom" data-trigger="focus"' \
                          f' title="{title}" data-content="{body}" class="m-0 event-pill badge badge-pill {category}"> </a>\n'

    return event_text


def generate_weekday_events(weekday, event_list, rare_hours=True):
    # generate column of event and dummy blocks

    # ==== HELPERS
    def get_start_block(start_hour):
        minutes = (start_hour.hour * 60) + start_hour.minute
        blocks = minutes / 15
        # offset for 7:00
        # #disabling offset for 0-23 calendar
        if rare_hours:
            start_block = blocks #- 28
        else:
            start_block = blocks - 28
        # print(f'start: {start_hour}, minutes: {minutes}, blocks: {blocks}, start_block: {start_block}')
        return start_block

    def generate_event_padded(column_start, column_end, event):
        text = ''
        column_blocks = column_end - column_start
        event_start = int(get_start_block(event['event_hour']))
        event_blocks = int(event['event_timeblocks'])
        diff = event_start - column_start
        column_blocks_left = column_blocks
        if diff == 0:
            # no empty at start
            text += generate_event_block(event)
            column_blocks_left = column_blocks_left - event_blocks
        elif diff < 0:
            # should not happen
            print('[ERROR] wrong event order in column')
            raise KeyError
        else:
            text += generate_empty_block(diff)
            column_blocks_left = column_blocks_left - diff
            text += generate_event_block(event)
            column_blocks_left = column_blocks_left - event_blocks

        if column_blocks_left > 0:
            text += generate_empty_block(column_blocks_left)

        return text

    def generate_empty_block(time_blocks):
        text = ''
        height = time_blocks * 20
        text += f'<div class="card bg-transparent border-0" style="height:{height}px"></div>\n'
        print(f'[BUILDER] making empty card of {int(time_blocks)} blocks')
        return text

    def generate_event_block(event):
        text = ''
        height = event['event_timeblocks'] * 20
        time = event['event_duration']
        translator = event['event_translator']
        character = event['event_character']
        actor = event['event_actor']
        category = 't-' + str(event['event_category'])
        sid = event['event_id']

        tooltip_text = f'<p><strong>{time}</strong></p><p>Translator: {translator}</p><p>Actor: {actor}<br>Character: {character}</p>'
        # tooltip_text = mark_safe(tooltip_text)
        text += f'<div class="card text-center small {category}" data-session="{sid}" onclick="sess_quickedit({sid})" data-html="true" data-toggle="tooltip" title="{tooltip_text}" style="height:{height}px">\n'
        text += '<div class="card-body event-body">\n'
        text += f'<p class="b" style="height:{str(height*0.8)}px; overflow: hidden;">{time}<br><br>Translator: <strong>{translator}</strong><br>Actor: <strong>{actor}</strong><br>Character: <strong>{character}</strong></p></div></div>\n'
        print(f'[BUILDER] making event card of {int(event["event_timeblocks"])} blocks')
        return text

    def generate_event_column(events, startblock, endblock):
        # generate column split into num parts, for listed events
        text = ''
        height = (endblock - startblock) * 20
        text += f'<div class="row flex-nowrap pl-3 pr-3" style="height{height}:px">\n'
        for event in events:
            # make column, generate padded content
            text += '<div class="col p-0 event-holder">\n'
            text += generate_event_padded(startblock, endblock, event)
            text += '</div>\n'
        text += '</div>\n'
        return text

    # pajiiti quick way, to fix 'tomorrow'
    def unique(list1):
        lset = set(list1)
        unique_list = (list(lset))
        return unique_list

    def conflict_check_pc(events):
        global_events = []

        for i in range(0, 96):
            global_events.append({'events_count': 0,
                                  'start_block': 0,
                                  'end_block': 0,
                                  'events': [],
                                  'colliding_events': []})

        global_event_start, global_event_stop, min_global_event_start = 0, 0, 0

        for e in events:
            local_event_start = int(get_start_block(events[e]['event_hour']))
            local_event_stop = local_event_start + events[e]['event_timeblocks']

            for h in range(local_event_start, local_event_stop):
                print(e)
                global_events[h]['events'].append(events[e])

                global_events[h]['colliding_events'].append(events[e])

            if global_events[local_event_start]['events_count'] == 0:
                start_block = local_event_start
                global_event_start = local_event_start
                global_event_stop = local_event_stop
                min_global_event_start = local_event_start
            else:
                for g in range(0, local_event_start):
                    if global_events[g]['events_count'] != 0:
                        global_event_start = g
                        break

                for g in range(global_event_start, 96):
                    if global_events[g]['events_count'] == 0:
                        global_event_stop = g
                        break

            if min_global_event_start > global_event_start:
                global_event_start = min_global_event_start

            if global_event_stop < local_event_stop:
                global_event_stop = local_event_stop

            end_block = global_event_stop

            new_global_even_count = global_events[global_event_start]['events_count'] + 1

            for g in range(global_event_start, global_event_stop):
                global_events[g]['events_count'] = new_global_even_count
                global_events[g]['start_block'] = start_block
                global_events[g]['end_block'] = end_block

        # add collinding events to each node
        for x in global_events:
            local_events = []
            for k in range(x['start_block'], x['end_block']):
                for ev in global_events[k]['events']:
                    if ev not in local_events:
                        local_events.append(ev)
            for a in local_events:
                if a not in x['colliding_events']:
                    x['colliding_events'].append(a)

        # create only events
        global_mini_table = []
        i = 0
        while i < 96:
            if len(global_events[i]['colliding_events']) > 0:
                global_mini_table.append({'colliding_events': global_events[i]['colliding_events'],
                                          'start_block': global_events[i]['start_block'],
                                          'end_block': global_events[i]['end_block']})
                i += global_events[i]['end_block'] - global_events[i]['start_block']
            else:
                i += 1

        return global_mini_table

    def conflict_check():
        ranges = []

        for w in weekday_events:
            w = weekday_events[w]
            startblock = int(get_start_block(w['event_hour']))
            endblock = int(startblock + w['event_timeblocks'])

            # should be inclusive?
            # endblock = endblock + 1

            taken_blocks = range(startblock, endblock)
            ranges += taken_blocks

        elems = len(ranges)
        unique_elems = len(unique(ranges))

        # if all are unique, there is no conflict
        if elems == unique_elems:
            return False
        return True

    column = ''
    weekday_events = event_list[weekday]
    event_num = len(weekday_events.keys())
    print(f'[DEBUG] found {event_num} events for day-{weekday}')

    # 56 for 7-20, 96 for 0-23
    if rare_hours:
        blocks_total = 96
    else:
        blocks_total = 56

    blocks_left = blocks_total
    # case 0: no events for that day
    if (event_num == 0):
        column += generate_empty_block(blocks_total)

    # case 1: single event, no conflicts
    elif (event_num == 1):
        e = weekday_events[1]
        # print(e)
        pad_block = get_start_block(e['event_hour'])

        if pad_block != 0:
            column += generate_empty_block(pad_block)
            blocks_left = blocks_left - pad_block

        column += generate_event_block(e)
        blocks_left = blocks_left - e['event_timeblocks']

        column += generate_empty_block(blocks_left)

    # case 2: multiple events, conflicts present
    elif conflict_check():
        # padding the first block
        e = weekday_events[1]
        pad_block = get_start_block(e['event_hour'])

        if pad_block != 0:
            column += generate_empty_block(pad_block)

        # each event has to be checked with all following events, except the last one
        mini_weekday_events_map = conflict_check_pc(weekday_events)

        old_end_block = 0
        for w in mini_weekday_events_map:
            start_block = w['start_block']
            end_block = w['end_block']

            if old_end_block == 0:
                old_end_block = end_block

            if old_end_block < start_block:
                column += generate_empty_block(start_block - old_end_block)
                old_end_block = end_block

            column += generate_event_column(w['colliding_events'], start_block, end_block)

    # case 3: multiple events, no conflict found
    else:
        # building the first block
        e = weekday_events[1]
        # print(f'[DEBUG]: {e}')
        pad_block = get_start_block(e['event_hour'])

        if pad_block != 0:
            column += generate_empty_block(pad_block)
            blocks_left = blocks_left - pad_block

        column += generate_event_block(e)
        blocks_left = blocks_left - e['event_timeblocks']

        # checking diff between endblock 1 and startblock
        i = 2
        while (i <= event_num):
            e = weekday_events[i]
            prev_endblock = blocks_total - blocks_left
            startblock = get_start_block(e['event_hour'])
            diff = startblock - prev_endblock
            if diff == 0:
                # no padding needed
                column += generate_event_block(e)
                blocks_left = blocks_left - e['event_timeblocks']
            elif diff < 0:
                # wrong ordering, should not happen
                print(f'[ERROR]: wrong block order')
                raise KeyError
            else:
                # padding with empty block then making proper one
                column += generate_empty_block(diff)
                blocks_left = blocks_left - diff
                column += generate_event_block(e)
                blocks_left = blocks_left - e['event_timeblocks']
            i = i + 1

    return column


def generate_month_manual(year_number=(datetime.now().year), month_number=(datetime.now().month), pk=None):
    # get_sessions_for_month(month_number)

    start_day = monthrange(year_number, month_number)[0]
    month_length = monthrange(year_number, month_number)[1]
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    day_titles = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    month_text = ''
    month_text += '<table class="table table-hover table-responsive" id="calendar_month"><thead class="thead-light">' + '\n'
    month_text += '<tr class="text-center align-middle">' + '\n'
    month_text += '<th colspan="1"><a role="button" id="nav_prev" class="btn btn-sm btn-outline-secondary" href="#"> << </a></th>' + '\n'
    month_text += '<th colspan="5" class="month_title">' + month_names[month_number] + ' ' + str(
        year_number) + '</th>' + '\n'
    month_text += '<th colspan="1"><a role="button" id="nav_next" class="btn btn-sm btn-outline-secondary" href="#"> >> </a></th>' + '\n'
    month_text += '</tr>' + '\n'
    month_text += '<tr>' + '\n'

    for day_title in day_titles:
        month_text += '<th scope="col" class="day_title">' + day_title + '</th>' + '\n'

    month_text += '</tr></thead>' + '\n'
    month_text += '<tbody>' + '\n'
    month_text += '<tr class="row_clickable">' + '\n'

    # pre-month empty cells
    for i in range(0, start_day):
        month_text += '<td class="day"></td>' + '\n'

    day = 1
    if pk == None:
        events_list = get_sessions_for_month(month_number)
    else:
        events_list = get_sessions_for_month(month_number, pk)

    for i in range(start_day, 7):
        day_id = str(year_number) + '-' + str(month_number) + '-' + str(day)
        event_text = generate_day_events(day, events_list)
        month_text += '<td class="day day-clickable" id="' + day_id + '">\n<div>' + str(day) + '</div>\n' \
                                                                                               '<div class="event-container justify-content-start m-0">\n' + event_text + '\n</div>\n</td>\n'

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

    month_text += '</tbody></table>' + '\n'

    # print(month_text)
    return month_text


@login_required
@user_passes_test(is_roboto,login_url='403',redirect_field_name=None)
def calendar_current(request, pk=None):
    today = datetime.now()
    if pk == None:
        return calendar(request, today.year, today.month)
    else:
        return calendar(request, today.year, today.month, pk)


@login_required
@user_passes_test(is_roboto,login_url='403',redirect_field_name=None)
def calendar(request, year, month, pk=None):
    if pk == None:
        manual_calendar = generate_month_manual(year, month)
    else:
        manual_calendar = generate_month_manual(year, month, pk)

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
        'calendar': mark_safe(manual_calendar),
        'nav_year_prev': nav_year_prev,
        'nav_year_next': nav_year_next,
        'nav_month_prev': nav_month_prev,
        'nav_month_next': nav_month_next,
        'year': year,
        'month': month,
        'translators': Translator.objects.all(),
    }

    context['navbar_data'] = get_navbar_data()

    if pk != None:
        project = Project.objects.get(id=pk)
        context['project'] = project

    return render(request, 'calendar.html', context=context)


def calendar_week(request, pk=None):
    # ids = request.GET.get('ids', '')
    context = {}
    if (request.GET.get('mon')):
        monday = request.GET.get('mon')
        monday_as_date = monday.split('-')
        monday_as_date = date(int(monday_as_date[0]), int(monday_as_date[1]), int(monday_as_date[2]))
        sunday_as_date = monday_as_date + timedelta(days=6)
        sunday = sunday_as_date.isoformat()
        if pk == None:
            week_events_result = get_sessions_for_range(monday, sunday)
        else:
            week_events_result = get_sessions_for_range(monday, sunday, pk)

        week_events = week_events_result['events_dict']
        rare = week_events_result["has_rare"]
        # check if early sessions exists for given week
        print(f'early hours check: {rare}')

        context = {
            'start': monday,
            'end': sunday,
            'rare_hours':rare,
            'mon_date': monday_as_date,
            'mon_events': mark_safe(generate_weekday_events(1, week_events, rare)),
            'tue_events': mark_safe(generate_weekday_events(2, week_events, rare)),
            'wed_events': mark_safe(generate_weekday_events(3, week_events, rare)),
            'thu_events': mark_safe(generate_weekday_events(4, week_events, rare)),
            'fri_events': mark_safe(generate_weekday_events(5, week_events, rare)),
            'sat_events': mark_safe(generate_weekday_events(6, week_events, rare)),
            'sun_events': mark_safe(generate_weekday_events(7, week_events, rare)),
        }

        if pk != None:
            project = Project.objects.get(id=pk)
            context['project'] = project

    print('week loader called')
    # one_time_gencss()
    return render(request, 'week_loader.html', context=context)


def one_time_gencss():
    colorlist = [
        ['t-2', '00C000'],
        ['t-3', 'ffc107'],
        ['t-4', '58C1CD'],
        ['t-5', 'dc3545'],
        ['t-6', 'fd7e14'],
        ['t-7', '6f42c1'],
        ['t-8', '28a745'],
        ['t-9', '20c997'],
        ['t-10', '30A56C'],
        ['t-11', 'D3A907'],
        ['t-12', '1F56A7'],
        ['t-13', 'EE3823'],
        ['t-14', 'F4AFCD'],
        ['t-15', 'FDB825'],
        ['t-16', 'A2BAD2'],
        ['t-17', 'B69FCC'],
        ['t-19', 'ECC083'],
        ['t-20', 'A82A70'],
        ['t-21', 'e83e8c'],
        ['t-22', '6DC066'],
        ['t-23', '7A468C'],
        ['t-24', '7DC734'],
        ['t-25', '84C3AA'],
        ['t-26', '90305D'],
        ['t-27', 'AC8262'],
        ['t-28', '125899'],
        ['t-29', 'C2191F'],
        ['t-30', '17a2b8'],
        ['t-31', '004EFA'],
        ['t-32', '6610f2'],
        ['t-33', '038C67'],
        ['t-34', 'B94278'],
        ['t-35', '18ABCC'],
        ['t-36', 'EA2F28'],
        ['t-37', 'CAAD76'],
        ['t-38', '3E805D'],
        ['t-39', '4272B8'],
        ['t-40', '471F5F']
    ]
    for c in colorlist:
        code = c[0]
        color = c[1]
        base = ''
        base += '.btn-' + code + ' {\n'
        base += '  color: #' + color + ';\n'
        base += '  background-color: transparent;\n'
        base += '  background-image: none;\n'
        base += '  border-color: #' + color + ';\n'
        base += '}\n'
        base += '\n'
        base += '.btn-' + code + ':hover {\n'
        base += '  color: #fff;\n'
        base += '  background-color: #' + color + ';\n'
        base += '  border-color: #' + color + ';\n'
        base += '}\n'
        base += '\n'
        base += '.btn-' + code + ':focus, .btn-' + code + '.focus {\n'
        base += '  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.5);\n'
        base += '}\n'
        base += '\n'
        base += '.btn-' + code + '.disabled, .btn-' + code + ':disabled {\n'
        base += '  color: #' + color + ';\n'
        base += '  background-color: transparent;\n'
        base += '}\n'
        base += '\n'
        base += '.btn-' + code + ':not(:disabled):not(.disabled):active, .btn-' + code + ':not(:disabled):not(.disabled).active,\n'
        base += '.show > .btn-' + code + '.dropdown-toggle {\n'
        base += '  color: #fff;\n'
        base += '  background-color: #' + color + ';\n'
        base += '  border-color: #' + color + ';\n'
        base += '}\n'
        base += '\n'
        base += '.btn-' + code + ':not(:disabled):not(.disabled):active:focus, .btn-' + code + ':not(:disabled):not(.disabled).active:focus,\n'
        base += '.show > .btn-' + code + '.dropdown-toggle:focus {\n'
        base += '  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.5);\n'
        base += '}\n'
        print(f'===PRINTING CSS FOR {code}')
        print(base)
