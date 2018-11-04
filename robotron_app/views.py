from itertools import islice
from collections import OrderedDict
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ViewDoesNotExist
from django.views import generic
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404, redirect
from django.forms import inlineformset_factory, modelformset_factory
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.db.models import Sum, Q, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User, Group
from robotron_app.models import *
from robotron_app.forms import *
# autocomplete
from dal import autocomplete

from django.forms.models import modelform_factory
from django.core.files.storage import FileSystemStorage
import os
import xlwt


class ModelFormWidgetMixin(object):
    def get_form_class(self):
        return modelform_factory(self.model, fields=self.fields, widgets=self.widgets)


class RobotoUpdateView(UserPassesTestMixin, UpdateView):

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Roboto Users').exists()


class RobotoCreateView(UserPassesTestMixin, generic.CreateView):

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Roboto Users').exists()


class RobotoListView(UserPassesTestMixin, generic.ListView):

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Roboto Users').exists()


def is_roboto(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name='Roboto Users').exists()


# Create your views here.
@login_required
@user_passes_test(is_roboto,login_url='projects',redirect_field_name=None)
def index(request):
    return render(request, 'index.html')


@login_required
@user_passes_test(is_roboto)
def calendar_view(request):
    return render(request, 'calendar.html')


class StudioListView(LoginRequiredMixin, RobotoListView):
    model = Studio
    paginate_by = 50

    queryset = Studio.objects.annotate(num_projects = Count('project'))


@login_required
@user_passes_test(is_roboto)
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


class ProjectCreateView(LoginRequiredMixin, ModelFormWidgetMixin, RobotoCreateView):
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


class CharactersListView(generic.ListView):
    model = Character
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super(CharactersListView, self).get_context_data(**kwargs)
        context['project_list'] = Project.objects.all()
        context['character_list'] = Character.objects.all()
        context['batch_list'] = Batch.objects.all()
        context['actor_list'] = Actor.objects.all()
        context['translator_list'] = Translator.objects.all()
        context['director_list'] = Director.objects.all()
        context['session_list'] = Session.objects.all()
        return context



class ProjectListView(LoginRequiredMixin, generic.ListView):
    model = Project
    paginate_by = 50

    queryset = Project.objects.annotate(num_batches=Count('batch'))

    def get_queryset(self, *args, **kwargs):
        this_user = self.request.user
        if is_roboto(this_user):
            return Project.objects.annotate(num_batches=Count('batch'))
        else:
            try:
                user_studio = Studio.objects.get(user=this_user)
                return Project.objects.filter(studio=user_studio)
            except ObjectDoesNotExist:
                return Project.objects.none()


class UserListView(LoginRequiredMixin, RobotoListView):
    model = User


@login_required
@user_passes_test(is_roboto)
def userlist_view(request):
    users = User.objects.all()
    for u in users:
        print(u)
        print(u.is_superuser)

    context = {
        'user_list':users
    }
    return render(request, 'auth/user_list.html', context=context)


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


class ProjectUpdateViewMini(LoginRequiredMixin, ModelFormWidgetMixin, UpdateView):
    model = Project
    template_name_suffix = '_update'
    fields = [
        'director',
    ]
    widgets = {
        'director': autocomplete.ModelSelect2(url='director-autocomplete'),
    }


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['batch_list'] = Batch.objects.filter(project=context['project'])
        context['attachment_list'] = Attachment.objects.filter(project=context['project'])
        return context


class AttachmentListView(LoginRequiredMixin, generic.ListView):
    model = Attachment


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    batch_list = Batch.objects.annotate(real_chars=Count('character')).filter(project=project)
    attachment_list = Attachment.objects.filter(project=project)
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
        'attachment_list': attachment_list,
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
    batch = Batch.objects.annotate(char_filecount=Sum('character__files_count')).get(pk=pk)
    # batch = get_object_or_404(Batch, pk=pk)
    error_msg = ''

    # init forms
    new_char_form = AddCharacterForm(initial=
        {
            'new_char_delivery_date':batch.deadline,
            'new_char_delivery_time':'17:00'
        })
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
                    actor=new_char_form.cleaned_data['new_char_actor'],
                    char_note=new_char_form.cleaned_data['new_char_note']
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

                    # create new characters, setting delivery to batch deadline
                    for c in char_list:
                        if char_list[c] != '':
                            new_actor = Actor.objects.get(name=char_list[c])
                            new_char = Character(
                                name=c,
                                batch=batch,
                                actor=new_actor,
                                files_count=0,
                                delivery_date=batch.deadline,
                                delivery_time='17:00'
                            )
                        else:
                            new_char = Character(
                                name=c,
                                batch=batch,
                                files_count=0,
                                delivery_date=batch.deadline,
                                delivery_time='17:00'
                            )
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


class BatchDetailUpdateViewMini(LoginRequiredMixin, UpdateView):
    model = Batch
    template_name = 'batch_loader.html'

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

    def get_success_url(self, **kwargs):
        context = super(BatchDetailUpdateViewMini, self).get_context_data(**kwargs)
        return_project = Project.objects.get(batch=context['batch'])
        return return_project.get_absolute_url()+"#batch-table"


class CharacterDetailView(LoginRequiredMixin, ModelFormWidgetMixin, generic.DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super(CharacterDetailView, self).get_context_data(**kwargs)
        context['session_list'] = Session.objects.filter(character=context['character'])
        return context


class CharacterDetailUpdateViewMini(LoginRequiredMixin, ModelFormWidgetMixin, UpdateView):
    model = Character
    template_name = 'character_loader.html'
    fields = [
        'name',
        'actor',
        'files_count',
        'delivery_date',
        'delivery_time',
        'char_note'
    ]
    widgets = {
        'actor': autocomplete.ModelSelect2(url='actor-autocomplete'),
        'delivery_date': forms.DateInput(attrs={'class': 'datepicker'}),
        'delivery_time': forms.TimeInput(),
    }

    def get_success_url(self, **kwargs):
        context = super(CharacterDetailUpdateViewMini, self).get_context_data(**kwargs)
        return_batch = Batch.objects.get(character=context['character'])
        return return_batch.get_absolute_url()+"#char-section"


class SessionDetailUpdateViewMini(LoginRequiredMixin, ModelFormWidgetMixin, UpdateView):
    model = Session
    template_name = 'session_loader.html'
    fields = [
        'day',
        'hour',
        'duration',
        'director',
        'translator'
    ]
    widgets = {
          'director': autocomplete.ModelSelect2(url='director-autocomplete'),
          'translator': autocomplete.ModelSelect2(url='translator-autocomplete'),
          'day': forms.DateInput(attrs={'class': 'datepicker'}),
          'hour': forms.TimeInput(),
    }

    def get_success_url(self, **kwargs):
        context = super(SessionDetailUpdateViewMini, self).get_context_data(**kwargs)
        return_batch = Batch.objects.get(session=context['session'])
        return return_batch.get_absolute_url()+"#sess-section"


# Calendar should redirect elsewhere
class SessionDetailUpdateCalendar(SessionDetailUpdateViewMini):
    template_name = 'session_loader_cal.html'

    def get_success_url(self, **kwargs):
        context = super(SessionDetailUpdateCalendar, self).get_context_data(**kwargs)
        return_batch = Batch.objects.get(session=context['session'])
        return_project = Project.objects.get(batch=return_batch)
        return reverse('calendar')


class SessionDetailUpdateProjectCalendar(SessionDetailUpdateViewMini):
    template_name = 'session_loader_pcal.html'

    def get_success_url(self, **kwargs):
        context = super(SessionDetailUpdateProjectCalendar, self).get_context_data(**kwargs)
        return_batch = Batch.objects.get(session=context['session'])
        return_project = Project.objects.get(batch=return_batch)
        return return_project.get_absolute_url() + 'calendar/'


class CharacterDetailUpdateView(LoginRequiredMixin, ModelFormWidgetMixin, UpdateView):
    model = Character
    template_name = 'robotron_app/character_detail.html'

    fields = [
        'name',
        'actor',
        'files_count',
        'delivery_date',
        'delivery_time',
        'char_note'
    ]

    widgets = {
        'actor': autocomplete.ModelSelect2(url='actor-autocomplete'),
        'delivery_date': forms.DateInput(attrs={'class': 'datepicker'}),
        'delivery_time': forms.TimeInput(),
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
def manage_batch_characters(request, pk):
    batch = Batch.objects.get(pk=pk)
    CharInlineFormset = inlineformset_factory(
        Batch, Character,
        fields=(
            'name',
            'files_count',
            'actor',
            'delivery_date',
            'delivery_time',
            'char_note'
        ),
        widgets={
            'actor': autocomplete.ModelSelect2(url='actor-autocomplete'),
            'delivery_date': forms.DateInput(attrs={'class': 'datepicker'}),
            'delivery_time': forms.TimeInput(),
        },
        extra=0
    )
    if request.method == "POST":
        formset = CharInlineFormset(request.POST, instance=batch)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(batch.get_absolute_url())
    else:
        formset = CharInlineFormset(instance=batch)
    return render(request, 'manage_characters.html', {'formset': formset, 'batch': batch})


@login_required
def manage_asset(request):
    asset_formset1 = modelformset_factory(Actor, fields=('name',), extra=0, can_delete=True)
    asset_formset2 = modelformset_factory(Translator, fields=('name',), extra=0, can_delete=True)
    asset_formset3 = modelformset_factory(Director, fields=('name',), extra=0, can_delete=True)
    asset_formset4 = modelformset_factory(Attachment, fields=('description', 'attachment', 'project'), extra=0, can_delete=True)
    # asset_formset4 = modelformset_factory(Attachment, fields=('description', 'attachment', 'project',), extra=0, can_delete=True)

    context = {
        'formset_actor': asset_formset1,
        'formset_translator': asset_formset2,
        'formset_director': asset_formset3,
        'formset_attachment': asset_formset4,
        'form_errors': 'none',
        'form_error_id': 'none'
    }

    if request.method == 'POST':
        if 'actors_control' in request.POST:
            formset_actor = asset_formset1(request.POST)
            try:
                if formset_actor.is_valid():
                    formset_actor.save()
            except Exception as e:
                context['form_error_id'] = type(e).__name__
                context['form_errors'] = 'error_actors'

        elif 'translators_control' in request.POST:
            formset_translator = asset_formset2(request.POST)
            try:
                if formset_translator.is_valid():
                    formset_translator.save()
            except Exception as e:
                context['form_error_id'] = type(e).__name__
                context['form_errors'] = 'error_translators'

        elif 'directors_control' in request.POST:
            formset_director = asset_formset3(request.POST)
            try:
                if formset_director.is_valid():
                    formset_director.save()
            except Exception as e:
                context['form_error_id'] = type(e).__name__
                context['form_errors'] = 'error_directors'
        elif 'attachment_control' in request.POST:
            formset_attachment = asset_formset4(request.POST)
            try:
                if formset_attachment.is_valid():
                    formset_attachment.save()
            except Exception as e:
                context['form_error_id'] = type(e).__name__
                context['form_errors'] = 'error_attachment'
        else:
            print('WTF')

    return render(request, 'manage_assets.html', context=context)


@login_required
def character_loader(request, pk):
    character = Character.objects.get(id=pk)
    context = {
        'character':character
    }
    return render(request, 'character_loader.html', context=context)


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
def delete_selected_attachments(request):
    # get list of ids from url and del all char records
    ids = request.GET.get('ids', '')
    id_list = ids.split(',')
    print(id_list)
    marked_for_del = Attachment.objects.filter(id__in=id_list)
    for m in marked_for_del:
        # call delete
        filename = m.attachment.name
        try:
            m.delete()
        except Exception as e:
            print(e)
            pass
        finally:
            # delete file for real not just database
            print(filename)
            # try:
            #     os.remove(f'{filename}')
            # except OSError:
            #     pass
            pass

    return HttpResponse()


@login_required
def attachment_upload(request, pk):
    project = Project.objects.get(id=pk)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            new_doc = Attachment(
                description=form.cleaned_data['description'],
                attachment=request.FILES["file"],
                project=project
            )
            new_doc.save()
            return HttpResponseRedirect(project.get_absolute_url())
            # redirect('/')
    else:
        form = AttachmentForm()
    return render(request, 'attachment_upload.html', {
        'form': form
    })


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

# ERROR HANDLERS
def error404(request, exception):
    context = {
        'code':'404'
    }
    print('hit 404')
    return render(request,'base_error.html',context=context)

def error403(request, exception):
    context = {
        'code': '403'
    }
    print('hit 403')
    return render(request, 'base_error.html', context=context)

def error400(request, exception):
    context = {
        'code': '400'
    }
    print('hit 400')
    return render(request, 'base_error.html', context=context)

def error500(request, exception):
    context = {
        'code': '500'
    }
    print('hit 500')
    return render(request, 'base_error.html', context=context)


def export_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{project.name}.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(f'PROJECT "{project.name}"')
    ws.col(0).width = 0x0d00 + 2000
    ws.col(1).width = 0x0d00 + 5000

    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    font_style.font.height = 240

    row_captions = ['Project', 'Studio', 'Director', 'Batches', 'Files', 'Words', 'Characters', 'Actors', 'SFX', 'TC',]
    row_data = [project.name, project.studio.name, project.director.name, project.batch_count, project.files_count, project.word_count, project.char_count, project.actor_count, project.sfx_note, project.tc_note,]

    col_num = 0
    for row_num in range(len(row_captions)):
        ws.write(row_num, col_num, row_captions[row_num], font_style)

    font_style = xlwt.XFStyle()
    font_style.font.bold = False
    font_style.font.height = 240

    col_num = 1
    for row_num in range(len(row_data)):
        ws.write(row_num, col_num, row_data[row_num], font_style)

    batches = Batch.objects.filter(project=project)

    font_style_bold2 = xlwt.XFStyle()
    font_style_bold2.font.bold = True
    font_style_bold2.font.height = 240

    font_style_plain2 = xlwt.XFStyle()
    font_style_plain2.font.bold = False
    font_style_plain2.font.height = 240


    font_style_bold = xlwt.XFStyle()
    font_style_bold.font.bold = True

    font_style_plain = xlwt.XFStyle()
    font_style_plain.font.bold = False

    for batch in batches:
        # zero row number for each batch
        row_num, col_num = 0, 0

        ws_batch = wb.add_sheet(f'BATCH "{batch.name}"')
        ws_batch.col(col_num).width = 0x0d00 + 2000
        ws_batch.col(col_num+1).width = 0x0d00 + 1500
        ws_batch.col(col_num+2).width = 0x0d00 + 500
        ws_batch.col(col_num+3).width = 0x0d00 + 500
        ws_batch.col(col_num+4).width = 0x0d00 + 500
        ws_batch.col(col_num+5).width = 0x0d00 + 2000
        ws_batch.col(col_num+6).width = 0x0d00 + 2000

        ws_batch.write(row_num, col_num, 'Name', font_style_bold2)
        ws_batch.write(row_num, col_num+1, f'{batch.name}', font_style_plain2)

        row_num += 1
        ws_batch.write(row_num, col_num, 'Start Date', font_style_bold2)
        ws_batch.write(row_num, col_num+1, f'{batch.start_date}', font_style_plain2)

        row_num += 1
        ws_batch.write(row_num, col_num, 'Deadline', font_style_bold2)
        ws_batch.write(row_num, col_num+1, f'{batch.deadline}', font_style_plain2)

        row_num += 1
        ws_batch.write(row_num, col_num, 'Files', font_style_bold2)
        ws_batch.write(row_num, col_num+1, batch.files_count, font_style_plain2)

        row_num += 1
        ws_batch.write(row_num, col_num, 'Words', font_style_bold2)
        ws_batch.write(row_num, col_num+1, batch.word_count, font_style_plain2)

        row_num += 1
        ws_batch.write(row_num, col_num, 'Characters', font_style_bold2)
        ws_batch.write(row_num, col_num+1, batch.char_count, font_style_plain2)

        # print all characters for each batch
        row_num += 5
        ws_batch.write(row_num, col_num, 'CHARACTERS', font_style_bold2)
        row_num += 1
        characters_columns = ['Character', 'Actor', 'Files', 'Delivery Date', 'Delivery Time', 'Comments', 'Sessions', ]
        characters = Character.objects.filter(batch=batch)
        for col_num in range(len(characters_columns)):
            ws_batch.write(row_num, col_num, characters_columns[col_num], font_style_bold)

        col_num = 0
        row_num += 1
        idx = 0

        for idx, char in enumerate(characters):
            ws_batch.write(row_num + idx, col_num, f'{char.name}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+1, f'{char.actor}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+2, char.files_count, font_style_plain)
            ws_batch.write(row_num + idx, col_num+3, f'{char.delivery_date}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+4, f'{char.delivery_time}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+5, f'{char.char_note}', font_style_plain)

            sessions = Session.objects.filter(batch=batch, character=char)
            ws_batch.write(row_num + idx, col_num+6, len(sessions), font_style_plain)

        # print all sessions for each batch
        row_num += idx + 5
        col_num = 0
        ws_batch.write(row_num, col_num, 'SESSIONS', font_style_bold2)
        row_num += 1
        sessions_columns = ['Character', 'Actor', 'Day', 'Hour', 'Duration', 'Director', 'Translator', ]
        sessions = Session.objects.filter(batch=batch)
        for col_num in range(len(sessions_columns)):
            ws_batch.write(row_num, col_num, sessions_columns[col_num], font_style_bold)

        col_num = 0
        row_num += 1
        for idx, session in enumerate(sessions):
            ws_batch.write(row_num + idx, col_num, f'{session.character.name}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+1, f'{session.character.actor}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+2, f'{session.day}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+3, f'{session.hour}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+4, f'{session.duration}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+5, f'{session.director}', font_style_plain)
            ws_batch.write(row_num + idx, col_num+6, f'{session.translator}', font_style_plain)

    wb.save(response)
    return response


# def test400(request):
#     raise PermissionDenied
#
# def test403(request):
#     raise PermissionDenied
#
# def test404(request):
#     raise ViewDoesNotExist
#
# def test500(request):
#     raise PermissionDenied