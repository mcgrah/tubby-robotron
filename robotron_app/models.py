from django.db import models
from django.urls import reverse
from django.conf import settings
from urllib.parse import urlparse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# =======================
# helper models
# =======================
class TranslationString(models.Model):
    key = models.CharField(null=False, blank=False, max_length=16, unique=True)
    english = models.TextField(null=True, blank=True)
    polish = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.key} EN: {self.english} PL: {self.polish}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    studio = models.ForeignKey('Studio', on_delete=models.PROTECT, null=True, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()



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
    char_note = models.TextField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('character', args=[str(self.id)])

    def __str__(self):
        # return f'{self.batch.project.name} {self.batch.name} {self.name} {self.actor.name}'
        return f'{self.batch.project.name} {self.batch.name} {self.name}'


class Attachment(models.Model):
    description = models.CharField(max_length=255, blank=True)
    attachment = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        'Project', on_delete=models.PROTECT,
    )

    def get_absolute_url(self):
        return reverse('document', args=[str(self.id)])

    def get_filename_from_url(self):
        url = urlparse(f'html://+{self.attachment}')
        filename = f'{url.path}'
        return filename[1:]

    def __str__(self):
        return f'{self.description} {self.attachment} {self.uploaded_at} {self.project.id}'


# ======================
# main models - should have detail view pages
# =======================
class Studio(models.Model):
    name = models.CharField(null=False, blank=False, max_length=128, unique=True)
    address = models.TextField(null=True, blank=True)
    telephone = models.CharField(null=True, blank=True, max_length=20)
    email = models.EmailField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('studio', args=[str(self.id)])

    def __str__(self):
        if self.email == '':
            return f'{self.name}'
        else:
            return f'{self.name} ({self.email})'


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
    char_count = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Characters number")
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
    char_count = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Characters number")
    # characters can be queried from helper Character class
    # char_list =

    def get_absolute_url(self):
        return reverse('batch', args=[str(self.id)])

    def __str__(self):
        return f'{self.project.name} {self.name}'


class CustomManager(models.Manager):
    def get_queryset(self):
        return super(CustomManager, self).get_queryset().filter(marked_delete=False)

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

    # duration switched from hours to quarters (x * 4) - 03.11.2018
    DURATION_CHOICES = (
        (0,'-'),
        (1,'15 min'),(2,'30 min'),(3,'45 min'),(4,'60 min (1h)'),
        (5,'1h 15 min'),(6,'1h 30 min'),(7,'1h 45 min'),(8,'2h'),
        (9,'2h 15 min'),(10,'2h 30 min'),(11,'2h 45 min'),(12,'3h'),
        (13,'3h 15 min'),(14,'3h 30 min'),(15,'3h 45 min'),(16,'4h'),
        (17,'4h 15 min'),(18,'4h 30 min'),(19,'4h 45 min'),(20,'5h'),
    )
    duration_blocks = models.SmallIntegerField(choices=DURATION_CHOICES,default=0)

    # fake delete
    marked_delete = models.BooleanField(null=False, blank=False,default=False)
    active = CustomManager()
    objects = models.Manager()

    def get_absolute_url(self):
        return reverse('session', args=[str(self.id)])

    def __str__(self):
        return f'{self.batch.name} {self.character.name} {self.day} {self.hour} {self.duration} {self.director}'
