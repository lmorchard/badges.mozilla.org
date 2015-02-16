import logging
import random

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User, Group, Permission
from teamwork.models import TeamManager, Team, Role

from badgus.base.utils import (make_random_code, slugify, scale_image,
        mk_upload_to, UPLOADS_FS)

from tower import ugettext_lazy as _


IMG_MAX_SIZE = getattr(settings, "TEAM_IMG_MAX_SIZE", (256, 256))

BADGETEAM_INVALID_NAMES = ('new',)



class BadgeTeamManager(TeamManager):
    pass


class BadgeTeam(Team):
    """Expansions to the teamwork Team model for user-created teams"""
    
    slug = models.SlugField(blank=False, unique=True,
        help_text='Very short name, for use in URLs and links')

    image = models.ImageField(blank=True, null=True,
        storage=UPLOADS_FS, upload_to=mk_upload_to('team.png'),
        help_text='Image representing this team')

    objects = BadgeTeamManager()

    default_policy = {
        "all": (
        ),
        "authenticated": (
        ),
        'members': (
            'badger.award_badge',
            'badger.nominate_badge',
            'badger.manage_deferredawards',
            'badger.delete_award',
            'badger.approve_nomination',
            'badger.reject_nomination',
            'badger.grant_deferredaward',
        ),
        'owners': (
            'teams.change_badgeteam', 
            'teams.delete_badgeteam', 
            'teams.list_badgeteamapplication',
            'teams.view_badgeteamapplication',
            'teams.delete_badgeteamapplication',
            'teams.change_badgeteam',
            'teams.invite_badgeteam',
            'teams.list_badgeteamapplication',
            'teams.view_badgeteamapplication',
            'teams.approve_badgeteamapplication',
            'badger.change_badge',
            'badger.delete_badge',
            'badger.award_badge',
            'badger.nominate_badge',
            'badger.manage_deferredawards',
            'badger.change_award',
            'badger.delete_award',
            'badger.change_nomination',
            'badger.delete_nomination',
            'badger.approve_nomination',
            'badger.reject_nomination',
            'badger.grant_deferredaward',
        )
    }

    class Meta:

        permissions = (
            ('list_badgeteam', 'Can list badge teams'),
            ('view_badgeteam', 'Can view badge team'),
            ('invite_badgeteam', 'Can issue invitations join to badge team'),
            ('apply_badgeteam', 'Can apply to join to badge team'),

            ('list_badgeteamapplication', 'Can list badge team applications'),
            ('view_badgeteamapplication', 'Can view badge team applications'),
            ('approve_badgeteamapplication', 'Can approve badge team applications'),
        )

    def filter_permissions(self, user, permissions):
        policy = self.default_policy

        permissions = permissions.union(policy['all'])
        if user.is_authenticated():
            permissions = permissions.union(policy['authenticated'])
            if self.has_owner(user):
                permissions = permissions.union(policy['owners'])
            if self.team.has_member(user):
                permissions = permissions.union(policy['members'])

        return permissions

    def get_upload_meta(self):
        return ("team", self.pk)

    def get_absolute_url(self):
        return reverse('teams.team_detail', kwargs={'slug':self.slug})

    def clean(self):
        if self.name in BADGETEAM_INVALID_NAMES:
            raise ValidationError(_('Invalid name'))

        if self.image:
            scaled_file = scale_image(self.image.file, IMG_MAX_SIZE)
            if not scaled_file:
                raise ValidationError(_('Cannot process image'))
            self.image.file = scaled_file

    def save(self, **kwargs):
        """Save the submission, updating slug"""
        self.slug = slugify(self.name)

        is_new = not self.pk

        super(BadgeTeam, self).save(**kwargs)


class BadgeTeamApplication(models.Model):

    comment = models.TextField(blank=False)
    team = models.ForeignKey(BadgeTeam, blank=False, null=False,
                             related_name='applications')
    approver = models.ForeignKey(User, blank=True, null=True,
                                 related_name='approved_badgeteam_applications')
    creator = models.ForeignKey(User, blank=False, null=True,
                                related_name='submitted_badgeteam_applications')
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    def get_permission_parents(self):
        return [ self.team, ]

    def filter_permissions(self, user, permissions):

        if user.is_authenticated():
            if self.has_owner(user):
                permissions.update([
                    'teams.view_badgeteamapplication',
                    'teams.delete_badgeteamapplication'
                ])

        return permissions

    def has_owner(self, user):
        return user == self.creator

    def get_absolute_url(self):
        return reverse('teams.team_application_detail', kwargs=dict(
            team_slug=self.team.slug, pk=self.pk))

    def approve(self, approver):
        self.approver = approver
        self.save()
        self.team.add_member(self.creator)
