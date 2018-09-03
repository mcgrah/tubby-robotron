from django.db import models
from django.urls import reverse


# =======================
# helper models
# =======================
class TranslationString(models.Model):
    key = models.CharField(null=False, blank=False, max_length=16, unique=True)
    english = models.TextField(null=True, blank=True)
    polish = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.key} EN: {self.english} PL: {self.polish}'


class Persona(models.Model):

    # PERSONA_ROLE = (
    #     ('a', 'ACTOR'),
    #     ('d', 'DIRECTOR'),
    #     ('t', 'TRANSLATOR'),
    # )
    #
    # role = models.CharField(null=True, blank=True, max_length=1, choices=PERSONA_ROLE)
    name = models.CharField(null=False, blank=False, max_length=64)
    # surname = models.CharField(null=False, blank=False, max_length=64)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return f'{self.name}'
        

class Actor(Persona):
    pass


class Director(Persona):
    pass


class Translator(Persona):
    pass


class Character(models.Model):
    name = models.CharField(null=False, blank=False, max_length=64)
    # project = models.ForeignKey("Project", on_delete=models.PROTECT, null=True, blank=True)
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, null=True, blank=True)
    files_count = models.PositiveIntegerField(null=True, blank=True)
    actor = models.ForeignKey(
        'Actor', on_delete=models.PROTECT,
        null=True, blank=True,
    )
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time = models.TimeField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('character', args=[str(self.id)])

    def __str__(self):
        # return f'{self.batch.project.name} {self.batch.name} {self.name} {self.actor.name}'
        return f'{self.batch.project.name} {self.batch.name} {self.name}'



# =======================
# main models - should have detail view pages
# =======================
class Studio(models.Model):
    name = models.CharField(null=False, blank=False, max_length=128)
    address = models.TextField(null=True, blank=True)
    telephone = models.CharField(null=True, blank=True, max_length=20)
    email = models.EmailField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('studio', args=[str(self.id)])

    def __str__(self):
        return f'{self.name} {self.email} {self.address} {self.telephone} {self.note}'


class Project(models.Model):
    name = models.CharField(null=False, blank=False, max_length=64)
    director = models.ForeignKey(
        "Director", on_delete=models.PROTECT,
        null=True, blank=True,
    )
    studio = models.ForeignKey('Studio', on_delete=models.PROTECT, null=False, blank=False)
    # batches don't need to be stored here, can be queried from Batch class
    # batch =
    batch_count = models.PositiveSmallIntegerField(null=True, blank=True)
    files_count = models.PositiveIntegerField(null=True, blank=True)
    word_count = models.PositiveIntegerField(null=True, blank=True)
    char_count = models.PositiveSmallIntegerField(null=True, blank=True)
    actor_count = models.PositiveSmallIntegerField(null=True, blank=True)
    sfx_note = models.TextField(null=True, blank=True)
    tc_note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('project', args=[str(self.id)])

    def __str__(self):
        return f'{self.name} {self.studio.name} {self.director.name}'


class Batch(models.Model):
    name = models.CharField(null=False, blank=False, max_length=64)
    project = models.ForeignKey('Project', on_delete=models.PROTECT, null=False, blank=False)
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    files_count = models.PositiveIntegerField(null=True, blank=True)
    word_count = models.PositiveIntegerField(null=True, blank=True)
    char_count = models.PositiveSmallIntegerField(null=True, blank=True)
    # characters can be queried from helper Character class
    # char_list =

    def get_absolute_url(self):
        return reverse('batch', args=[str(self.id)])

    def __str__(self):
        return f'{self.project.name} {self.name}'


class Session(models.Model):
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, null=False, blank=False)
    character = models.ForeignKey(
        'Character', on_delete=models.PROTECT,
        #limit_choices_to={'batch': batch},
        null=False, blank=False,
    )
    day = models.DateField(null=True, blank=True)
    hour = models.TimeField(null=True, blank=True)
    duration = models.PositiveSmallIntegerField(null=True, blank=True)
    director = models.ForeignKey(
        'Director', on_delete=models.PROTECT,
        null=True, blank=True,
    )
    translator = models.ForeignKey(
        'Translator', on_delete=models.PROTECT,
        null=True, blank=True,
    )

    def get_absolute_url(self):
        return reverse('session', args=[str(self.id)])

    def __str__(self):
        return f'{self.batch.name} {self.character.name} {self.day} {self.hour} {self.duration} {self.director}'
