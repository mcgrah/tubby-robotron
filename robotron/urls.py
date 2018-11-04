"""robotron URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from robotron_app.views import ActorAutocomplete, DirectorAutocomplete, TranslatorAutocomplete, StudioAutocomplete

handler404 = 'robotron_app.views.error404'
handler500 = 'robotron_app.views.error500'
handler403 = 'robotron_app.views.error403'
handler400 = 'robotron_app.views.error400'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('robotron/', include('robotron_app.urls')),
    url(r'^progressbarupload/', include('progressbarupload.urls')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(
            r'^actor-autocomplete/$',
            ActorAutocomplete.as_view(create_field='name'),
            name='actor-autocomplete',
    ),
    url(
            r'^director-autocomplete/$',
            DirectorAutocomplete.as_view(create_field='name'),
            name='director-autocomplete',
    ),
    url(
            r'^translator-autocomplete/$',
            TranslatorAutocomplete.as_view(create_field='name'),
            name='translator-autocomplete',
    ),
    url(
            r'^studio-autocomplete/$',
            StudioAutocomplete.as_view(),
            name='studio-autocomplete',
    ),

    path('', RedirectView.as_view(url='/robotron/', permanent=True)),
]

# for debug only
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 

# urlpatterns += [
#     path('404/',test404),
#     path('403/',test403),
#     path('400/',test400),
#     path('500/',test500),
# ]

