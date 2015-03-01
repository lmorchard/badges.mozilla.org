import logging
import json
import urllib
import urlparse

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_, raises
from nose.plugins.attrib import attr

import mock

from django.conf import settings, UserSettingsHolder
from django.utils.functional import wraps
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from badger.models import Badge

from badgus.base.utils import slugify
from badgus.teams.models import BadgeTeam, BadgeTeamApplication
from badgus.teams.tests import BadgeTeamTestCase


class BadgeTeamTest(BadgeTeamTestCase):

    @raises(ValidationError)
    def test_team_invalid_names(self):
        """Attempting to validate a team with a disallowed name results in error"""
        from badgus.teams.models import BADGETEAM_INVALID_NAMES
        team = BadgeTeam(name=BADGETEAM_INVALID_NAMES[0])
        team.clean()

    def test_slug(self):
        """Changing the team name updates the slug"""
        name1 = 'Alpha Team'
        slug1 = slugify(name1)

        team = BadgeTeam(name=name1)
        team.save()
        eq_(slug1, team.slug)

        name2 = 'Beta Team'
        slug2 = slugify(name2)

        team.name = name2
        team.save()
        eq_(slug2, team.slug)

    def test_team_deletion_does_not_delete_badges(self):
        """Deletion of a team should not delete badges"""
        team = BadgeTeam(name='To delete')
        team.save()

        badge = Badge(title='No disassemble', creator=self.users['user'],
                      team=team)
        badge.save()

        eq_(1, Badge.objects.filter(title=badge.title).count())
        team.delete()
        eq_(1, Badge.objects.filter(title=badge.title).count())

    def test_remove_member(self):
        """Membership should be revokable and member's badges are removed from the team"""
        team = BadgeTeam(name='To delete')
        team.save()

        team.add_member(self.users['user'])

        badge = Badge(title='No disassemble', creator=self.users['user'],
                      team=team)
        badge.save()

        eq_(team, Badge.objects.get(pk=badge.pk).team)
        team.remove_member(self.users['user'])
        eq_(None, Badge.objects.get(pk=badge.pk).team)


class BadgeTeamApplicationTest(BadgeTeamTestCase):

    def test_approve_application(self):
        """Approving an application should result in the applicant as a member of the team"""
        team = BadgeTeam(name="test_applications")
        team.save()
        
        application = BadgeTeamApplication(
            team=self.team, creator=self.users['user'])
        application.save()

        ok_(not team.has_member(self.users['user']))
        ok_(not application.approver)
        
        application.approve(approver=self.users['owner'])

        ok_(self.team.has_member(self.users['user']))
        eq_(self.users['owner'], application.approver)
