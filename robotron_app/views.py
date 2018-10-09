from itertools import islice
from collections import OrderedDict
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.db.models import Sum, Q, Count
from django.http import HttpResponseRedirect, HttpResponse
from robotron_app.models import *
from robotron_app.forms import *
# autocomplete
from dal import autocomplete

from django.forms.models import modelform_factory

class ModelFormWidgetMixin(object):
    def get_form_class(self):
        return modelform_factory(self.model, fields=self.fields, widgets=self.widgets)


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def calendar_view(request):
    return render(request, 'calendar.html')


class StudioListView(LoginRequiredMixin, generic.ListView):
    model = Studio
    paginate_by = 50

    queryset = Studio.objects.annotate(num_projects = Count('project'))


@login_required
def studio_create_view(request):
    if request.method == 'POST':
        form = AddStudioForm(request.POST)
        if form.is_valid():
            Studio.objects.create(
                name=form.cleaned_data['new_studio_name'],
                address=form.cleaned_data['new_studio_address'],
                telephone=form.cleaned_data['new_studio_telephone'],
                email=form.cleaned_data['new_studio_email'],
                note=form.cleaned_data['new_studio_note']
            )
            return HttpResponseRedirect(reverse('studios'))
    else:
        form = AddStudioForm()

    context = {
        'form':form,
    }

    return render(request, 'create_studio.html', context=context)


class ProjectCreateView(LoginRequiredMixin, ModelFormWidgetMixin, generic.CreateView):
    model=Project
    template_name_suffix = '_create'
    fields = [
        'name',
        'director',
        'studio',
        'batch_count',
        'files_count',
        'word_count',
        'char_count',
        'actor_count',
        'sfx_note',
        'tc_note'
    ]
    widgets = {
        'director': autocomplete.ModelSelect2(url='director-autocomplete'),
        'studio': autocomplete.ModelSelect2(url='studio-autocomplete')
    }


class ProjectListView(LoginRequiredMixin, generic.ListView):
    model = Project
    paginate_by = 50

    queryset = Project.objects.annotate(num_batches=Count('batch'))


class StudioDetailView(LoginRequiredMixin, generic.DetailView):
    model = Studio

    def get_context_data(self, **kwargs):
        context = super(StudioDetailView, self).get_context_data(**kwargs)
        context['project_list'] = Project.objects.filter(studio=context['studio'])
        return context


class StudioUpdateView(LoginRequiredMixin, UpdateView):
    model = Studio
    template_name_suffix = '_update'
    fields = [
        'name',
        'address',
        'telephone',
        'email',
        'note'
    ]


class ProjectUpdateView(LoginRequiredMixin, ModelFormWidgetMixin, UpdateView):
    model = Project
    template_name_suffix = '_update'
    fields = [
        'name',
        'director',
        'studio',
        'batch_count',
        'files_count',
        'word_count',
        'char_count',
        'actor_count',
        'sfx_note',
        'tc_note'
    ]
    widgets = {
        'director': autocomplete.ModelSelect2(url='director-autocomplete'),
        'studio': autocomplete.ModelSelect2(url='studio-autocomplete')
    }


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['batch_list'] = Batch.objects.filter(project=context['project'])
        return context


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    batch_list = Batch.objects.annotate(real_chars=Count('character')).filter(project=project)
    # batch_list = Batch.objects.filter(project=project)
    # get existing batch number for auto-naming
    last_batch = 'Batch '+str(len(batch_list) + 1)

    # form handling for adding new batch
    if request.method == 'POST':
        new_batch_form = AddBatchForm(request.POST)
        # create new batch auto assigned to the project
        if new_batch_form.is_valid():
            Batch.objects.create(
                project=project,
                name=new_batch_form.cleaned_data['new_batch_name'],
                start_date=new_batch_form.cleaned_data['new_batch_start_date'],
                deadline=new_batch_form.cleaned_data['new_batch_deadline'],
                files_count=new_batch_form.cleaned_data['new_batch_files_count'],
                word_count=new_batch_form.cleaned_data['new_batch_word_count'],
                char_count=new_batch_form.cleaned_data['new_batch_char_count']
            )
            return HttpResponseRedirect(request.path_info)

    else:
        # default form goes here
        new_batch_form = AddBatchForm(initial={'new_batch_name':last_batch})

    context = {
        'project': project,
        'batch_list': batch_list,
        'form': new_batch_form,
        'total_chars': batch_list.aggregate(total_chars=Sum('char_count'))['total_chars'],
    }
    return render(request, 'robotron_app/project_detail.html', context=context)


class BatchDetailView(LoginRequiredMixin, generic.DetailView):
    model = Batch

    def get_context_data(self, **kwargs):
        context = super(BatchDetailView, self).get_context_data(**kwargs)
        context['session_list'] = Session.objects.filter(batch=context['batch'])
        context['character_list'] = Character.objects.filter(batch=context['batch'])
        context['form'] = AddCharacterForm()

        for c in context['character_list']:
            session_count = Session.objects.filter(character=c).count()
            setattr(c, 'session_count', session_count)

        return context

@login_required
def batch_detail_view(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    error_msg = ''

    # init forms
    new_char_form = AddCharacterForm()
    file_form = UploadCSVForm()
    session_form = AddSessionForm(initial={'new_session_director':Director.objects.get(id=batch.project.director_id)})

    # form handling for adding single character
    if request.method == 'POST':
        if 'single_form' in request.POST:
            print('single_form_key called')
            file_form = UploadCSVForm()  #  clearing file form
            new_char_form = AddCharacterForm(request.POST)
            if new_char_form.is_valid():
                Character.objects.create(
                    batch=batch,
                    name=new_char_form.cleaned_data['new_char_name'],
                    files_count=new_char_form.cleaned_data['new_char_files_count'],
                    delivery_date=new_char_form.cleaned_data['new_char_delivery_date'],
                    delivery_time=new_char_form.cleaned_data['new_char_delivery_time'],
                    actor=new_char_form.cleaned_data['new_char_actor']
                )
                return HttpResponseRedirect(request.path_info)
        # form handling for session generation
        elif 'session_char_ids' in request.POST:
            session_form = AddSessionForm(request.POST)
            print('sessions called')
            if session_form.is_valid():
                char_ids = request.POST['session_char_ids'].split(',')
                print('RECEIVED: ', char_ids)
                bulk_sessions = []
                for char in char_ids:
                    if int(char) >= 0:
                        tmp_session = Session(
                            batch=batch,
                            character=Character.objects.get(id=char),
                            day=session_form.cleaned_data['new_session_day'],
                            hour=session_form.cleaned_data['new_session_hour'],
                            duration=session_form.cleaned_data['new_session_duration'],
                            director=session_form.cleaned_data['new_session_director'],
                            translator=session_form.cleaned_data['new_session_translator'],
                        )
                        bulk_sessions.append(tmp_session)
                Session.objects.bulk_create(bulk_sessions)
                return HttpResponseRedirect(request.path_info)

        # form handling for csv import
        elif 'csv_import_form' in request.POST:
            print('csv_form_key_called')
            file_form = UploadCSVForm(request.POST, request.FILES)
            if file_form.is_valid():
                try:
                    file = request.FILES['file']
                    # if not file.name.endswith('.csv'):
                    #     error_msg = 'file is not CSV type'
                    #     print(error_msg)
                    #     raise file_form.ValidationError(error_msg)
                    #
                    # if file.multiple_chunks():
                    #     error_msg = 'file is too large'
                    #     print(error_msg)
                    #     raise file_form.ValidationError(error_msg)

                    # if error_msg != '':
                    #     print(error_msg)
                    #     raise ValueError(error_msg)
                    # else:
                    file_data = file.read().decode('utf-8')
                    lines = file_data.split("\n")

                    tmp_actor_list = []
                    char_list = OrderedDict()

                    for l in lines:
                        fields = l.split(",")
                        # 1 field for char only, 2 fields for char + actor
                        # anything else is invalid
                        if 0 < len(fields) < 3:
                            if len(fields) == 2:
                                # file with actors
                                tmp_actor = fields[1].strip()
                                if tmp_actor not in tmp_actor_list:
                                    tmp_actor_list.append(tmp_actor)
                                char_list[(fields[0].strip())] = tmp_actor
                            else:
                                # file with chars only
                                char_list[(fields[0].strip())] = ''
                        else:
                            error_msg = 'wrong number of fields in csv'
                            raise file_form.ValidationError(error_msg)
                            # raise ValueError(error_msg)

                    bulk_chars = []
                    bulk_actors = []

                    # validate actors if present
                    for c in tmp_actor_list:
                        try:
                            if Actor.objects.get(name=c):
                                print('actor found: ', c)
                        except ObjectDoesNotExist:
                            tmp_actor = Actor(name=c)
                            print('actor will be created: ', tmp_actor)
                            bulk_actors.append(tmp_actor)

                    # create new actors before dependant characters
                    if len(bulk_actors) > 0:
                        Actor.objects.bulk_create(bulk_actors)

                    # create new characters
                    for c in char_list:
                        if char_list[c] != '':
                            new_actor = Actor.objects.get(name=char_list[c])
                            new_char = Character(name=c, batch=batch, actor=new_actor)
                        else:
                            new_char = Character(name=c, batch=batch)
                        bulk_chars.append(new_char)

                    if len(bulk_chars) > 0:
                        Character.objects.bulk_create(bulk_chars)

                except Exception as e:
                    print(e)

                return HttpResponseRedirect(request.path_info)

    context = {
        'batch': batch,
        'session_list': Session.objects.filter(batch=batch),
        'character_list': Character.objects.filter(batch=batch),
        'form': new_char_form,
        'file_form':file_form,
        'session_form':session_form
    }
    if error_msg != '':
        context['errors'] = error_msg

    for c in context['character_list']:
        session_count = Session.objects.filter(character=c).count()
        setattr(c, 'session_count', session_count)

    return render(request, 'robotron_app/batch_detail.html', context=context)


class BatchDetailUpdateView(LoginRequiredMixin, UpdateView):
    model = Batch
    template_name_suffix = '_update'

    fields = [
        'name',
        'start_date',
        'deadline',
        'files_count',
        'word_count',
        'char_count',
    ]

    widgets = {
        'start_date': forms.DateInput(attrs={'class': 'datepicker'}),
        'deadline': forms.DateInput(attrs={'class': 'datepicker'}),
    }


class CharacterDetailView(LoginRequiredMixin, generic.DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super(CharacterDetailView, self).get_context_data(**kwargs)
        context['session_list'] = Session.objects.filter(character=context['character'])
        return context


class CharacterDetailUpdateView(LoginRequiredMixin, UpdateView):
    model = Character
    template_name = 'robotron_app/character_detail.html'

    fields = [
        'name',
        'actor',
        'files_count',
        'delivery_date',
        'delivery_time'
    ]

    widgets = {
        'actor': autocomplete.ModelSelect2(url='actor-autocomplete'),
        'delivety_date': forms.DateInput(attrs={'class': 'datepicker'}),
        'delivety_time': forms.DateInput(),
    }

    def get_context_data(self, **kwargs):
        context = super(CharacterDetailUpdateView, self).get_context_data(**kwargs)
        context['session_list'] = Session.objects.filter(character=context['character'])
        return context


class ActorAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Actor.objects.all()

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q)
            )

        return qs


class DirectorAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Director.objects.all()

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q)
            )

        return qs


class TranslatorAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Translator.objects.all()

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q)
            )

        return qs


class StudioAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Studio.objects.all()

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q)
            )

        return qs


@login_required
def manage_char_session(request, pk):
    character = Character.objects.get(pk=pk)
    SessionInlineFormset = inlineformset_factory(Character, Session,
        fields=(
            'day',
            'hour',
            'duration',
            'director',
            'translator'
        ),
        widgets={
            'director': autocomplete.ModelSelect2(url='director-autocomplete'),
            'translator': autocomplete.ModelSelect2(url='translator-autocomplete'),
            'day': forms.DateInput(attrs={'class': 'datepicker'}),
            'hour': forms.TimeInput(),
        },
        extra=0
    )
    if request.method == "POST":
        formset = SessionInlineFormset(request.POST, instance=character)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(character.get_absolute_url())
    else:
        formset = SessionInlineFormset(instance=character)
    return render(request, 'manage_sessions.html', {'formset': formset, 'character': character})


@login_required
def generate_new_sessions(request, batch_id):
    # generate new sessions for all characters:
    # - in given batch AND
    # - with assigned actor AND
    # - with 0 sessions
    batch = Batch.objects.get(id=batch_id)
    director = batch.project.director
    characters = Character.objects.filter(batch=batch).filter(actor__isnull=False)
    bulk_list = []
    for char in characters:
        s_count = Session.objects.filter(character=char).count()
        if s_count > 0:
            pass
        else:
            tmp_session = Session(batch=batch, director=director, character=char)
            bulk_list.append(tmp_session)

    # create one session for each char in a batch
    Session.objects.bulk_create(bulk_list)

    response = HttpResponse(content_type="text/html")
    response.write('ok')
    return response


@login_required
def nuke_empty_sessions(request):
    nuke_this = Session.objects.filter(translator__isnull=True)
    if nuke_this.exists():
        nuke_this._raw_delete(nuke_this.db)

    response = HttpResponse(content_type="text/html")
    response.write('ok')
    return response


@login_required
def nuke_chars(request):
    nuke_this_char = Character.objects.filter(files_count__isnull=True)
    if nuke_this_char.exists():
        nuke_this_char._raw_delete(nuke_this_char.db)

    response = HttpResponse(content_type="text/html")
    response.write('ok')
    return response


@login_required
def delete_selected_chars(request):
    # get list of ids from url and del all char records
    ids = request.GET.get('ids', '')
    id_list = ids.split(',')
    print(id_list)
    marked_for_del = Character.objects.filter(id__in=id_list)
    for m in marked_for_del:
        # call delete
        try:
            m.delete()
        except Exception as e:
            print(e)
            pass

    return HttpResponse()


@login_required
def delete_selected_sessions(request):
    # get list of ids from url and del all char records
    ids = request.GET.get('ids', '')
    id_list = ids.split(',')
    print(id_list)
    marked_for_del = Session.objects.filter(id__in=id_list)
    for m in marked_for_del:
        # call delete
        try:
            m.delete()
        except Exception as e:
            print(e)
            pass

    return HttpResponse()


@login_required
def delete_selected_batches(request):
    # get list of ids from url and del all char records
    ids = request.GET.get('ids', '')
    id_list = ids.split(',')
    print(id_list)
    marked_for_del = Batch.objects.filter(id__in=id_list)
    for m in marked_for_del:
        # call delete
        try:
            m.delete()
        except Exception as e:
            print(e)
            pass

    return HttpResponse()


@login_required
def delete_studio(request, pk):
    marked = Studio.objects.get(id=pk)
    try:
        marked.delete()
    except Exception as e:
        print(e)
        pass

    return HttpResponseRedirect(reverse('studios'))


@login_required
def delete_project(request, pk):
    marked = Project.objects.get(id=pk)
    try:
        marked.delete()
    except Exception as e:
        print(e)
        pass

    return HttpResponseRedirect(reverse('projects'))
