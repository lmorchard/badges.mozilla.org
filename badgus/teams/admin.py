from urlparse import urljoin

from django.conf import settings
from django.contrib import admin

from django import forms
from django.db import models

from badgus.base.urlresolvers import reverse
from badgus.base.utils import UPLOADS_URL, show_unicode, show_image

from teamwork.admin import related_members_link, RoleInline
from .models import *


class BadgeTeamAdmin(admin.ModelAdmin):
    fields = ( 'name', 'image', 'description',)
    list_select_related = True
    list_display = ('name', 'slug', show_image, related_members_link,)
    search_fields = ('name', 'description',)
    inlines = (RoleInline,)

admin.site.register(BadgeTeam, BadgeTeamAdmin)


class BadgeTeamApplicationAdmin(admin.ModelAdmin):
    fields = ('team', 'creator', 'approver', 'created', 'comment')
    list_display = ('team', 'creator', 'approver', 'created', 'comment')
    search_fields = ('creator__username', 'approver__username')

admin.site.register(BadgeTeamApplication, BadgeTeamApplicationAdmin)
