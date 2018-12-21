from django.urls import path
from robotron_app import views, calendar, stats

urlpatterns = [
    path('', views.index, name='index'),
    path('studios/', views.StudioListView.as_view(), {}, name='studios'),
    path('studio/<int:pk>/', views.StudioDetailView.as_view(), name='studio'),
    path('studio/create_studio/', views.studio_create_view, name='create_studio'),
    path('studio/<int:pk>/update/', views.StudioUpdateView.as_view(), name='update_studio'),

    path('attachments/', views.AttachmentListView.as_view(),  name='attachments'),

    path('projects/', views.ProjectListView.as_view(), {}, name='projects'),
    path('projects/create/',views.ProjectCreateView.as_view(),name='create_project'),

    path('project/<int:pk>/', views.project_detail_view, name='project'),
    path('project/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='update_project'),
    path('project/<int:pk>/updatemini/', views.ProjectUpdateViewMini.as_view(), name='update_project_mini'),
    path('project/<int:pk>/edit_loader/', views.BatchDetailUpdateViewMini.as_view(), name='batch_loader'),

    path('project/<int:pk>/upload/', views.attachment_upload, name='attachment_upload'),

    path('batch/<int:pk>/', views.batch_detail_view, name='batch'),
    path('batch/<int:pk>/update/', views.BatchDetailUpdateView.as_view(), name='update_batch'),
    path('batch/<int:pk>/update_characters/', views.manage_batch_characters, name='manage_batch_characters'),
    path('batch/<int:pk>/edit_loader/', views.SessionDetailUpdateViewMini.as_view(), name='session_loader'),
    path('batch/<int:pk>/edit_loader_cal/', views.SessionDetailUpdateCalendar.as_view(), name='session_loader_cal'),
    path('batch/<int:pk>/edit_loader_pcal/', views.SessionDetailUpdateProjectCalendar.as_view(), name='session_loader_pcal'),

    path('character/<int:pk>/', views.CharacterDetailUpdateView.as_view(), name='character'),
    path('character/<int:pk>/update_sessions/', views.manage_char_session, name='manage_char_sessions'),
    # path('character/<int:pk>/edit_loader/', views.character_loader, name='character_loader'),
    path('character/<int:pk>/edit_loader/', views.CharacterDetailUpdateViewMini.as_view(), name='character_loader'),
    path('character/<int:pk>/edit_loader_mini/', views.CharacterDetailUpdateStudioMini.as_view(), name='character_loader_mini'),

    path('assets', views.manage_asset, name='assets'),
    path('calendar/', calendar.calendar_current, name='calendar'),
    path('calendar/<int:year>/<int:month>/', calendar.calendar, name='calendar_range'),
    path('project/<int:pk>/calendar/', calendar.calendar_current, name='project_calendar'),
    path('project/<int:pk>/calendar/<int:year>/<int:month>/', calendar.calendar, name='project_calendar_range'),

    path('project/<int:pk>/stats/', stats.stats_current, name='project_stats'),

    path('calendar/calendar_week', calendar.calendar_week, name='calendar_week_loader'),
    path('project/<int:pk>/calendar/calendar_week', calendar.calendar_week, name='project_calendar_week_loader'),

    # path('users/', views.UserListView.as_view(), {}, name='users'),
    path('users/', views.userlist_view, {}, name='users'),
    path('users/create/', views.create_user, name='create_user'),


    path('profile/', views.update_profile, name='profile'),
    path('profile/<int:pk>', views.update_profile, name='user_profile'),
    path('profile/change_password',views.password_modal,name='change_password')
]
# functions only:
urlpatterns += [
    path('nuke_empty_sessions/', views.nuke_empty_sessions, name='nuke_empty_sessions'),
    path('nuke_chars/', views.nuke_chars, name='nuke_chars'),
    path('generate_sessions/<int:batch_id>', views.generate_new_sessions, name='generate_new_sessions'),
    path('delete_selected_chars/', views.delete_selected_chars, name='delete_selected_chars'),
    path('delete_selected_sessions/', views.delete_selected_sessions, name='delete_selected_sessions'),
    path('delete_selected_batches/', views.delete_selected_batches, name='delete_selected_batches'),
    path('delete_selected_attachments/', views.delete_selected_attachments, name='delete_selected_attachments'),
    path('studio/<int:pk>/delete/', views.delete_studio, name='delete_studio'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('project/<int:pk>/export/', views.export_project, name='export_project'),
    path('users/<int:pk>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('users/<int:pk>/activate/', views.activate_user, name='activate_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
]
# manual error redirects:
urlpatterns += [
    path('404/',views.error404, name='404'),
    path('403/',views.error403, name='403'),
    path('400/',views.error400, name='400'),
    path('500/',views.error500, name='500'),
]