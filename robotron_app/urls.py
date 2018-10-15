from django.urls import path
from robotron_app import views, calendar

urlpatterns = [
    path('', views.index, name='index'),
    path('studios/', views.StudioListView.as_view(), {}, name='studios'),
    path('studio/<int:pk>/', views.StudioDetailView.as_view(), name='studio'),
    path('studio/create_studio/', views.studio_create_view, name='create_studio'),
    path('studio/<int:pk>/update/', views.StudioUpdateView.as_view(), name='update_studio'),

    path('projects/', views.ProjectListView.as_view(), {}, name='projects'),
    path('projects/create/',views.ProjectCreateView.as_view(),name='create_project'),

    path('project/<int:pk>/', views.project_detail_view, name='project'),
    path('project/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='update_project'),
    path('project/<int:pk>/updatemini/', views.ProjectUpdateViewMini.as_view(), name='update_project_mini'),
    path('project/<int:pk>/edit_loader/', views.BatchDetailUpdateViewMini.as_view(), name='batch_loader'),
    path('batch/<int:pk>/', views.batch_detail_view, name='batch'),
    path('batch/<int:pk>/update/', views.BatchDetailUpdateView.as_view(), name='update_batch'),
    path('batch/<int:pk>/edit_loader/', views.SessionDetailUpdateViewMini.as_view(), name='session_loader'),

    path('character/<int:pk>/', views.CharacterDetailUpdateView.as_view(), name='character'),
    path('character/<int:pk>/update_sessions/', views.manage_char_session, name='manage_char_sessions'),
    # path('character/<int:pk>/edit_loader/', views.character_loader, name='character_loader'),
    path('character/<int:pk>/edit_loader/', views.CharacterDetailUpdateViewMini.as_view(), name='character_loader'),

    path('assets', views.manage_asset, name='assets'),
    path('calendar/', calendar.calendar_current, name='calendar'),
    path('calendar/<int:year>/<int:month>/', calendar.calendar, name='calendar_range'),

    path('calendar/calendar_week', calendar.calendar_week, name='calendar_week_loader'),

    # path('users/', views.UserListView.as_view(), {}, name='users'),
    path('users/', views.userlist_view, {}, name='users'),


]
# functions only:
urlpatterns += [
    path('nuke_empty_sessions/', views.nuke_empty_sessions, name='nuke_empty_sessions'),
    path('nuke_chars/', views.nuke_chars, name='nuke_chars'),
    path('generate_sessions/<int:batch_id>', views.generate_new_sessions, name='generate_new_sessions'),
    path('delete_selected_chars/', views.delete_selected_chars, name='delete_selected_chars'),
    path('delete_selected_sessions/', views.delete_selected_sessions, name='delete_selected_sessions'),
    path('delete_selected_batches/', views.delete_selected_batches, name='delete_selected_batches'),
    path('studio/<int:pk>/delete/', views.delete_studio, name='delete_studio'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
]
