from django.urls import path
from robotron_app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('studios/', views.StudioListView.as_view(), {}, name='studios'),
    path('projects/', views.ProjectListView.as_view(), {}, name='projects'),
    path('studio/<int:pk>', views.StudioDetailView.as_view(), name='studio'),
    # path('project/<int:pk>', views.ProjectDetailView.as_view(), name='project'),
    path('project/<int:pk>', views.project_detail_view, name='project'),
    # path('batch/<int:pk>', views.BatchDetailView.as_view(), name='batch'),
    path('batch/<int:pk>', views.batch_detail_view, name='batch'),
    path('character/<int:pk>', views.CharacterDetailView.as_view(), name='character'),
]
# functions only:
urlpatterns += [
    path('nuke_empty_sessions/', views.nuke_empty_sessions, name='nuke_empty_sessions'),
    path('generate_sessions/<int:batch_id>', views.generate_new_sessions, name='generate_new_sessions'),
    path('delete_selected_chars/', views.delete_selected_chars, name='delete_selected_chars'),

]
