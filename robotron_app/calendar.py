from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from calendar import monthrange
from datetime import date, datetime, timedelta
from django.shortcuts import render
from robotron_app.models import Session, Translator
import json

def is_roboto(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name='Roboto Users').exists()

def get_sessions_for_range(start_date,end_date):
    range_sessions = Session.objects.filter(day__range=(start_date,end_date )).order_by('hour')
    # empty for all weekdays
    events_dict = {
        1:{},
        2:{},
        3:{},
        4:{},
        5:{},
        6:{},
        7:{}
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
        end_time = start_time + timedelta(hours=m.duration)
        timeblocks = m.duration * 60 / 15
        if m.translator == None:
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
                'event_actor':actor,
                'event_category': category,
                'event_timeblocks': timeblocks,
                'event_hour': m.hour
            }

        try:
            elem = len(events_dict[weekday].keys())
            events_dict[weekday][elem+1] = content

        except KeyError:
            events_dict[weekday] = {}
            events_dict[weekday][1] = content
            pass
    # print(json.dumps(events_dict, indent=4, sort_keys=True))
    return events_dict


def get_sessions_for_month(month):
    month_sessions = Session.objects.filter(day__month=month).filter(day__isnull=False).order_by('day','hour')
    events_dict = {}

    for m in month_sessions:
        day = m.day.day
        project = m.batch.project.name
        character = m.character.name
        actor = m.character.actor.name
        batch = m.batch.name
        start_time = datetime.combine(m.day, m.hour)
        end_time = start_time + timedelta(hours=m.duration)
        if m.translator == None:
            category = 0
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
    if int == 0:
        return 'badge-secondary'
    return 'badge-dark'


def generate_day_events(day, event_list):
#     content that goes inside event-container
    event_text = ''
    if day in event_list.keys():
    #     iterate over list
        for k in event_list[day].values():
            category = color_pill(k['event_category'])+' t-'+str(k['event_category'])
            title = k['event_title']
            body = k['event_duration']+' '+k['event_body']

            # link = k['event_link']
            link = '#'
            # event_text += f'<a href="{link}" class="m-0 badge badge-pill {category}"> </a>\n'
            event_text += f'<a tabindex="0" data-toggle="popover" data-placement="bottom" data-trigger="focus"' \
                          f' title="{title}" data-content="{body}" class="m-0 event-pill badge badge-pill {category}"> </a>\n'

    return event_text


def generate_weekday_events(weekday, event_list):
    # generate column of event and dummy blocks

    # ==== HELPERS
    def get_start_block(start_hour):
        minutes = (start_hour.hour * 60) + start_hour.minute
        blocks = minutes / 15
        # offset for 7:00
        start_block = blocks - 28
        # print(f'start: {start_hour}, minutes: {minutes}, blocks: {blocks}, start_block: {start_block}')
        return start_block

    def generate_event_padded(column_start,column_end,event):
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
        return text

    def generate_event_block(event):
        text = ''
        height = event['event_timeblocks'] * 20
        time = event['event_duration']
        translator = event['event_translator']
        character = event['event_character']
        actor = event['event_actor']
        category = 't-'+str(event['event_category'])

        text += f'<div class="card text-center small {category}" style="height:{height}px">\n'
        text += '<div class="card-body event-body">\n'
        text += f'<p class="card-title">{time}</p>\n'
        text += f'<p class="card-subtitle">{translator}</p>\n'
        text += '<hr class="slim-hr">\n'
        text += f'<p class="card-text">{character}<br>{actor}</p>\n'
        text += '</div></div>\n'
        return text

    def generate_event_column(num,ids,startblock,endblock):
        # generate column split into num parts, for listed events
        print(f'[DEBUG]: num:{num} ids:{ids} start:{startblock} end:{endblock}')
        text = ''
        col_i = 1
        height = (endblock - startblock) * 20
        text += f'<div class="row flex-nowrap pl-3 pr-3" style="height{height}:px">\n'
        while col_i <= num:
            # make column, generate padded content
            event = weekday_events[ids[col_i-1]]
            print(f'[DEBUG]: generating event {ids[col_i-1]} in column {num}')
            text += '<div class="col p-0 event-holder">\n'
            text += generate_event_padded(startblock,endblock,event)
            text += '</div>\n'
            col_i = col_i +1
        text += '</div>\n'
        return text


    # pajiiti quick way, to fix tomorrow
    def unique(list1):
        lset = set(list1)
        unique_list = (list(lset))
        return unique_list

    def conflict_duo(range1, range2):
        # returns start / end of split column or 0 if no overlap
        ranges = []
        ranges += range1
        ranges += range2

        elems = len(ranges)
        unique_elems = len(unique(ranges))

        if elems == unique_elems:
            return 0
        else:
            result = []
            result.append(range1[0])
            result.append(range2[-1])
            return result

    def conflict_duo_ev(event1, event2):
        start1 = int(get_start_block(event1['event_hour']))
        start2 = int(get_start_block(event2['event_hour']))
        end1 = int(start1 + event1['event_timeblocks'])
        end2 = int(start2 + event2['event_timeblocks'])
        range1 = range(start1, end1)
        range2 = range(start2, end2)
        return conflict_duo(range1,range2)

    def conflict_loop(i, j):
        # for j events, check for conflicts starting with i-th event
        main_e = weekday_events[i]
        events_left = j-i
        split_column = [-1, 0]
        while i < j:
            comp_e = weekday_events[i+1]
            collide = conflict_duo_ev(main_e, comp_e)
            if collide > 0:
                start1 = int(get_start_block(main_e['event_hour']))
                start2 = int(get_start_block(comp_e['event_hour']))
                end1 = int(start1 + main_e['event_timeblocks'])
                end2 = int(start2 + comp_e['event_timeblocks'])
                if end2 > end1:
                    # if comp ends later, switch places
                    main_e = weekday_events[j]
                    i = j
                else:
                    i = i+1


        return split_column

    def conflict_check():
        ranges = []

        for w in weekday_events:
            w = weekday_events[w]
            startblock = int(get_start_block(w['event_hour']))
            endblock = int(startblock + w['event_timeblocks'])

            # should be inclusive?
            # endblock = endblock + 1

            taken_blocks = range(startblock,endblock)
            print(f'event takes following blocks: {taken_blocks}')
            ranges += taken_blocks

        elems = len(ranges)
        unique_elems = len(unique(ranges))

        print(f'[DEBUG] list elements: {elems}, unique: {unique_elems}')
        # if all are unique, there is no conflict
        if(elems == unique_elems):
            return False

        return True

    column = ''
    weekday_events = event_list[weekday]
    event_num = len(weekday_events.keys())
    print(f'[DEBUG] found {event_num} events for day-{weekday}')

    blocks_left = 56
    # case 0: no events for that day
    if (event_num == 0):
        column += generate_empty_block(56)

    # case 1: single event, no conflicts
    elif (event_num == 1):
        e = weekday_events[1]
        # print(e)
        pad_block = get_start_block(e['event_hour'])

        if pad_block != 0:
            column +=generate_empty_block(pad_block)
            blocks_left = blocks_left - pad_block

        column += generate_event_block(e)
        blocks_left = blocks_left - e['event_timeblocks']

        column +=generate_empty_block(blocks_left)

    # case 2: multiple events, conflicts present
    elif(conflict_check()):
        # padding the first block
        e = weekday_events[1]
        pad_block = get_start_block(e['event_hour'])

        if pad_block != 0:
            column += generate_empty_block(pad_block)
            blocks_left = blocks_left - pad_block

        # each event has to be checked with all following events, except the last one
        collider = -1
        for w in weekday_events:
            if collider < w < len(weekday_events):
                print(f'[DEBUG] running checks for {w}')
                event_ids = []
                event_ids.append(w)
                e = weekday_events[w]
                events_left = event_num - w
                split_column = [-1,0]
                i = 1
                while i <= events_left:
                    e_next = weekday_events[w+i]
                    collide = conflict_duo_ev(e,e_next)
                    # print(collide)
                    if collide == 0:
                        print(f'[DEBUG]: NO CONFLICT between {w} and {w+i}')
                        print(f'last found column blocks: {split_column}, collider: {collider}')
                        i = i + 1
                        # if no column blocks, event can be built alone else chained
                        break
                    else:
                        print(f'[DEBUG]: {w} COLLIDES with {w+i}')
                        collider = w+i
                        event_ids.append(w+i)
                        if split_column[0] == -1:
                            split_column[0] = collide[0]
                        elif collide[0] < split_column[0]:
                            split_column[0] = collide[0]

                        if collide[1] > split_column[1]:
                            split_column[1] = collide[1]
                        # swap places?
                        if i+1 <=events_left:
                            start1 = int(get_start_block(e['event_hour']))
                            start2 = int(get_start_block(e_next['event_hour']))
                            end1 = int(start1 + e['event_timeblocks'])
                            end2 = int(start2 + e_next['event_timeblocks'])
                            if end2 > end1:
                            # nested additional check
                                collide2 = conflict_duo_ev(e_next,weekday_events[w+i+1])
                                if collide2 != 0:
                                    print(f'[DEBUGDEBUG]: {w+i} COLLIDES with {w+i+1}')
                                    collider = w+i+1
                                    event_ids.append(w + i+1)
                                    if collide2[0] < split_column[0]:
                                        split_column[0] = collide2[0]

                                    if collide2[1] > split_column[1]:
                                        split_column[1] = collide2[1]
                        i = i + 1

                    print(f'current column blocks: {split_column}')
                # do we need empty block before anything?

                # clear ids to be sure
                event_ids = (list(set(event_ids)))

                print(f'[DEBUG]: we are at {int(56 - blocks_left)} block')
                if (collider > 1):
                    # content inside column is padded, but no column itself
                    diff = split_column[0] - int(56 - blocks_left)
                    print(f'[DEBUG] column diff is {diff}')
                    if diff > 0:
                        column += generate_empty_block(diff)
                        blocks_left = blocks_left - diff
                    column += generate_event_column(len(event_ids), event_ids, split_column[0], split_column[1])
                    blocks_left = blocks_left - (split_column[1]+1 - split_column[0])
                else:
                    # single event, needs manual padding?

                    start = get_start_block(e['event_hour'])
                    diff = int(56 - blocks_left) - start
                    print(f'[DEBUG] diff is {diff}')
                    if diff == 0:
                        column += generate_event_block(e)
                        blocks_left = blocks_left - e['event_timeblocks']
                    elif diff < 0:
                        # should not happen
                        print('[ERROR] wrong event order')
                        raise KeyError
                    else:
                        column += generate_empty_block(diff)
                        blocks_left = blocks_left - diff
                        column += generate_event_block(e)
                        blocks_left = blocks_left - e['event_timeblocks']

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
            prev_endblock = 56 - blocks_left
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
            i = i+1

    return column



def generate_week_manual(week_events):

    debug_empty_events = ''
    mon_events = generate_weekday_events(1,week_events)
    tue_events = generate_weekday_events(2,week_events)
    wed_events = generate_weekday_events(3,week_events)
    thu_events = generate_weekday_events(4,week_events)
    fri_events = generate_weekday_events(5,week_events)
    sat_events = generate_weekday_events(6,week_events)
    sun_events = generate_weekday_events(7,week_events)

    week_text = ''
    return week_text


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

@login_required
@user_passes_test(is_roboto)
def calendar_current(request):

    today = datetime.now()
    return calendar(request, today.year,  today.month)

@login_required
@user_passes_test(is_roboto)
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
        'translators':Translator.objects.all(),
    }
    return render(request, 'calendar.html', context=context)


def calendar_week(request):
    # ids = request.GET.get('ids', '')
    context = {}
    if(request.GET.get('mon')):
        monday = request.GET.get('mon')
        monday_as_date = monday.split('-')
        monday_as_date = date(int(monday_as_date[0]),int(monday_as_date[1]),int(monday_as_date[2]))
        sunday_as_date = monday_as_date + timedelta(days=6)
        sunday = sunday_as_date.isoformat()
        week_events = get_sessions_for_range(monday,sunday)
        # week_text = generate_week_manual(week_events)

        context = {
            'start':monday,
            'end':sunday,
            # 'week_text':week_text,
            'mon_date':monday_as_date,
            'mon_events': mark_safe(generate_weekday_events(1, week_events)),
            'tue_events': mark_safe(generate_weekday_events(2, week_events)),
            'wed_events': mark_safe(generate_weekday_events(3, week_events)),
            'thu_events': mark_safe(generate_weekday_events(4, week_events)),
            'fri_events': mark_safe(generate_weekday_events(5, week_events)),
            'sat_events': mark_safe(generate_weekday_events(6, week_events)),
            'sun_events': mark_safe(generate_weekday_events(7, week_events)),
        }
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