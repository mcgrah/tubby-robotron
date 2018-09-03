from itertools import islice
from collections import OrderedDict
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum, Q
from django.http import HttpResponseRedirect, HttpResponse
from robotron_app.models import Studio, Project, Batch, Session, Character, Actor
from robotron_app.forms import AddBatchForm, AddCharacterForm, UploadCSVForm
# autocomplete
from dal import autocomplete


# Create your views here.
def index(request):
    return render(request, 'index.html')


class StudioListView(generic.ListView):
    model = Studio
    paginate_by = 50


class ProjectListView(generic.ListView):
    model = Project
    paginate_by = 50


class StudioDetailView(generic.DetailView):
    model = Studio

    def get_context_data(self, **kwargs):
        context = super(StudioDetailView, self).get_context_data(**kwargs)
        context['project_list'] = Project.objects.filter(studio=context['studio'])
        return context


class ProjectDetailView(generic.DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['batch_list'] = Batch.objects.filter(project=context['project'])
        return context


def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)

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
            )    #
            return HttpResponseRedirect(request.path_info)

    else:
        # default form goes here
        new_batch_form = AddBatchForm()

    batch_list = Batch.objects.filter(project=project)
    context = {
        'project': project,
        'batch_list': batch_list,
        'form': new_batch_form,
        'total_chars': batch_list.aggregate(total_chars=Sum('char_count'))['total_chars']
    }
    return render(request, 'robotron_app/project_detail.html', context=context)


class BatchDetailView(generic.DetailView):
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


def batch_detail_view(request, pk):
    batch = get_object_or_404(Batch, pk=pk)

    #     form handling for adding single character
    if request.method == 'POST':
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
    else:
        new_char_form = AddCharacterForm()

    context = {
        'batch': batch,
        'session_list': Session.objects.filter(batch=batch),
        'character_list': Character.objects.filter(batch=batch),
        'form': new_char_form
    }

    for c in context['character_list']:
        session_count = Session.objects.filter(character=c).count()
        setattr(c, 'session_count', session_count)

    return render(request, 'robotron_app/batch_detail.html', context=context)


class CharacterDetailView(generic.DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super(CharacterDetailView, self).get_context_data(**kwargs)
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


def nuke_empty_sessions(request):
    nuke_this = Session.objects.filter(translator__isnull=True)
    if nuke_this.exists():
        nuke_this._raw_delete(nuke_this.db)

    response = HttpResponse(content_type="text/html")
    response.write('ok')
    return response


def upload_csv_modal(request, last_batch_id):
    response = HttpResponse(content_type="text/html")
    print('upload_csv_called')
    print(last_batch_id)
    error_msg = ''
    context = {
        'last_batch_id':last_batch_id
    }
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        print('entering post')
        if form.is_valid():
            print('form is valid')
            #do something with the file
            try:
                file = request.FILES['file']
                if not file.name.endswith('.csv'):
                    error_msg = 'file is not CSV type'

                if file.multiple_chunks():
                    error_msg = 'file is too large'

                if error_msg != '':
                    context['errors'] = error_msg
                    print(error_msg)
                    response.write(error_msg)
                    return response
                else:
                    file_data = file.read().decode('utf-8')
                    lines = file_data.split("\n")

                    bulk_chars = []
                    bulk_actors = []

                    char_list = OrderedDict()
                    tmp_actor_list = []

                    batch = Batch.objects.get(id=last_batch_id)
                    # parse lines
                    for l in lines:
                        fields = l.split(",")
                        if len(fields) > 2:
                            error_msg = 'too many fields in csv'
                            response.write(error_msg)
                            return response
                        tmp_tmp_actor = fields[1].strip()
                        char_list[(fields[0].strip())] = tmp_tmp_actor
                        if tmp_tmp_actor not in tmp_actor_list:
                            tmp_actor_list.append(tmp_tmp_actor)

                    # validate actors
                    for c in tmp_actor_list:
                        # tmp_actor = char_list[c]
                        # print(tmp_actor)
                        try:
                            if Actor.objects.get(name=c):
                                print('actor found: ', c)

                        except ObjectDoesNotExist as e:
                            tmp_tmp_actor = Actor(name=c)
                            print('actor will be created: ', tmp_tmp_actor)
                            bulk_actors.append(tmp_tmp_actor)

                    if len(bulk_actors) > 0:
                        Actor.objects.bulk_create(bulk_actors)

                    # create new chars
                    for c in char_list:
                         tmp_actor = char_list[c]
                         fresh_actor = Actor.objects.get(name=tmp_actor)
                         new_char = Character(name=c, batch=batch, actor=fresh_actor)
                         bulk_chars.append(new_char)

                    Character.objects.bulk_create(bulk_chars)

                    return batch_detail_view(request,last_batch_id)

            except Exception as e:
                error_msg = e
                print(e)

            # handle_csv_file(file)
            # return to main or the same?
            if error_msg != '':
                context['errors'] = error_msg

            print(error_msg)
            response.write(error_msg)
        else:
            error_msg = 'invalid form'
    else:
        form = UploadCSVForm()

    context['form'] = form

    if error_msg != '':
        context['errors'] = error_msg
    else:
        context['success'] = "upload successful"

    return render(request, 'upload_modal.html', context=context)


def handle_csv_file(f):
    # do something funny
    # parse on the fly, no saving to disk
    pass