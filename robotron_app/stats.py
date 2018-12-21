from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from robotron_app.models import Session, Project, Batch


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


@login_required
@user_passes_test(is_roboto, login_url='403', redirect_field_name=None)
def stats_current(request, pk=None):
    context = {}

    if pk != None:
        project = Project.objects.get(id=pk)

        context['project'] = project
        context['project_stats'] = project_stats(project)
        context['project_details'] = project_details(project)

    return render(request, 'stats.html', context=context)


def project_stats(project):
    def duration_blocks_to_hr_string(duration_block):
        minutes = (int(duration_block) % 4) * 15
        hr = int(int(duration_block) / 4)
        if minutes < 10:
            return f'{hr}:0{minutes}'
        else:
            return f'{hr}:{minutes}'

    def duration_blocks_to_minutes(duration_block):
        return int(duration_block)
        minutes = (int(duration_block) % 4) * 15
        hr = int(int(duration_block) / 4) * 60
        return int(hr + minutes)

    def duration_minutes_to_hours(duration_minutes):
        minutes = (int(duration_minutes) % 60)
        hr = int(int(duration_minutes) / 60)
        if minutes < 10:
            return f'{hr}:0{minutes}'
        else:
            return f'{hr}:{minutes}'


    batches = Batch.objects.filter(project=project)

    stats_json = {'actor': {}, 'translator': {}, 'director': {}}
    for batch in batches:
        sessions = Session.active.filter(batch=batch)

        for idx, session in enumerate(sessions):
            try:
                stats_json['actor'][f'{session.character.actor}'] = int(
                    stats_json['actor'][f'{session.character.actor}']) + duration_blocks_to_minutes(
                    f'{session.duration_blocks}')
            except:
                stats_json['actor'][f'{session.character.actor}'] = duration_blocks_to_minutes(
                    f'{session.duration_blocks}')

            try:
                stats_json['director'][f'{session.director}'] = int(
                    stats_json['director'][f'{session.director}']) + duration_blocks_to_minutes(
                    f'{session.duration_blocks}')
            except:
                stats_json['director'][f'{session.director}'] = duration_blocks_to_minutes(f'{session.duration_blocks}')

            try:
                stats_json['translator'][f'{session.translator}'] = int(
                    stats_json['translator'][f'{session.translator}']) + duration_blocks_to_minutes(
                    f'{session.duration_blocks}')
            except:
                stats_json['translator'][f'{session.translator}'] = duration_blocks_to_minutes(
                    f'{session.duration_blocks}')

    stats_json_out = {'actors': [], 'translators': [], 'directors': []}

    none_item = []
    for actor in stats_json['actor']:
        item = []
        if actor == 'None':
            none_item.append(duration_blocks_to_hr_string(stats_json['actor'][actor]))
            none_item.append(actor)
        else:
            item.append(duration_blocks_to_hr_string(stats_json['actor'][actor]))
            item.append(actor)
            stats_json_out['actors'].append(item)
    if none_item:
        stats_json_out['actors'].append(none_item)

    none_item = []
    for translator in stats_json['translator']:
        item = []
        if translator == 'None':
            none_item.append(duration_blocks_to_hr_string(stats_json['translator'][translator]))
            none_item.append(translator)
        else:
            item.append(duration_blocks_to_hr_string(stats_json['translator'][translator]))
            item.append(translator)
            stats_json_out['translators'].append(item)
    if none_item:
        stats_json_out['translators'].append(none_item)

    none_item = []
    for director in stats_json['director']:
        item = []
        if translator == 'None':
            none_item.append(duration_blocks_to_hr_string(stats_json['director'][director]))
            none_item.append(director)
        else:
            item.append(duration_blocks_to_hr_string(stats_json['director'][director]))
            item.append(director)
            stats_json_out['directors'].append(item)
    if none_item:
        stats_json_out['directors'].append(none_item)

    return stats_json_out


def project_details(project):

    project_det = []

    batches = Batch.objects.filter(project=project)
    project_det.append(len(batches))

    sessions_count = 0
    for batch in batches:
        sessions = Session.active.filter(batch=batch)
        sessions_count += len(sessions)

    project_det.append(sessions_count)

    return project_det
