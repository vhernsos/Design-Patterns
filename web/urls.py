from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.dashboard,     name='dashboard'),
    path('events/<int:pk>/',          views.event_detail,  name='event_detail'),
    path('events/<int:pk>/edit/',     views.event_update,  name='event_update'),
    path('events/<int:pk>/delete/',   views.event_delete,  name='event_delete'),
    path('events/build/',             views.build_event,   name='build_event'),
    path('events/<int:pk>/clone/',    views.clone_event,   name='clone_event'),
    path('config/',                   views.global_config, name='global_config'),
]