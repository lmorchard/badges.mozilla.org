from django.conf import settings
from django.conf.urls import patterns, url

from badgus.teams.views import *

urlpatterns = patterns('badgus.teams.views',

    url(r'^$', 
        TeamListView.as_view(), name='teams.home'),
    url(r'^new$', 
        TeamCreateView.as_view(), name='teams.team_create'),
    url(r'^(?P<slug>[^/]+)$', 
        TeamDetailView.as_view(), name='teams.team_detail'),
    url(r'^(?P<slug>[^/]+)/delete$', 
        TeamDeleteView.as_view(), name='teams.team_delete'),
    url(r'^(?P<slug>[^/]+)/edit$', 
        TeamUpdateView.as_view(), name='teams.team_edit'),
    
    url(r'^(?P<team_slug>[^/]+)/applications/$',
        TeamApplicationListView.as_view(),
        name='teams.team_applications_list'),
    url(r'^(?P<team_slug>[^/]+)/applications/new$',
        TeamApplicationCreateView.as_view(),
        name='teams.team_apply'),
    url(r'^(?P<team_slug>[^/]+)/applications/(?P<pk>[^/]+)$',
        TeamApplicationDetailView.as_view(),
        name='teams.team_application_detail'),
    url(r'^(?P<team_slug>[^/]+)/applications/(?P<pk>[^/]+)/delete$',
        TeamApplicationDeleteView.as_view(),
        name='teams.team_application_delete'),
    url(r'^(?P<team_slug>[^/]+)/applications/(?P<pk>[^/]+)/approve$',
        TeamApplicationApproveView.as_view(),
        name='teams.team_application_approve'),
)
