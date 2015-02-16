import logging

import json
from nose.tools import eq_, ok_
from django.test import TestCase
from django.http import HttpRequest

from django.contrib.auth.models import User

from pyquery import PyQuery as pq
from django_browserid.tests import mock_browserid

from tower import activate

from teamwork.models import Role

from badger.models import Badge

from badgus.base.urlresolvers import reverse
from badgus.teams.models import BadgeTeam, BadgeTeamApplication
from badgus.teams.tests import BadgeTeamTestCase


class BadgeTeamApplicationViewsTest(BadgeTeamTestCase):

    def test_application_button_on_team(self):
        """Application button appears on team view"""
        self.client_login()
        r = self.client.get(self.team_url, follow=True)

        doc = pq(r.content)
        button = doc.find('a.apply-team')
        eq_(1, button.length)

        expected_url = reverse('teams.team_apply',
                               kwargs={"team_slug": self.team.slug})
        eq_(expected_url, button.attr('href'))

    def test_application_button_lifecycle(self):
        """Show a button to apply, review application, or hide altogether as appropriate"""
        self.client_login()

        application = BadgeTeamApplication(
            team=self.team, creator=self.users['user'])
        application.save()

        r = self.client.get(self.team_url, follow=True)
        doc = pq(r.content)

        eq_(0, doc.find('a.apply-team').length)
        eq_(application.get_absolute_url(),
            doc.find('a.view-team-application').attr('href'))

        application.approve(self.users['owner'])

        r = self.client.get(self.team_url, follow=True)
        doc = pq(r.content)

        eq_(0, doc.find('a.view-team-application').length)
        eq_(0, doc.find('a.apply-team').length)


    def test_application_button_hidden_for_members(self):
        """Application to team button should be hidden for members"""
        for name in ('member', 'owner'):
            self.client_login(name)
            r = self.client.get(self.team_url, follow=True)
            doc = pq(r.content)
            eq_(0, doc.find('a.apply-team').length)

    def test_list_applications_button(self):
        """List applications button should appear for owner and members with permission"""
        for name in ('owner',):
            self.client_login(name)
            r = self.client.get(self.team_url, follow=True)
            doc = pq(r.content)
            eq_(1, doc.find('a.list-team-applications').length)

    def test_list_applications(self):
        """Ensure users wth permissions can list applications"""
        for name in ('owner',):
            self.client_login(name)

            url = reverse('teams.team_applications_list',
                          kwargs={"team_slug": self.team.slug})

            self.team.applications.all().delete()

            r = self.client.get(url, follow=True)
            doc = pq(r.content)
            eq_(1, doc.find('.applications .empty').length)
            eq_(0, doc.find('.applications .application').length)

            application = BadgeTeamApplication(
                team=self.team, creator=self.users['user'])
            application.save()

            r = self.client.get(url, follow=True)
            doc = pq(r.content)
            eq_(0, doc.find('.applications .empty').length)
            eq_(1, doc.find('.applications .application').length)

    def test_list_only_pending_applications(self):
        """Only pending applications should be listed by default unless a query param is supplied"""
        self.client_login('owner')

        application = BadgeTeamApplication(
            team=self.team, creator=self.users['user'])
        application.save()

        url = reverse('teams.team_applications_list',
                      kwargs={"team_slug": self.team.slug})

        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(0, doc.find('.applications .empty').length)
        eq_(1, doc.find('.applications .application').length)

        r = self.client.get('%s?approved' % url, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('.applications .empty').length)
        eq_(0, doc.find('.applications .application').length)

        application.approve(self.users['owner'])

        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('.applications .empty').length)
        eq_(0, doc.find('.applications .application').length)

        r = self.client.get('%s?approved' % url, follow=True)
        doc = pq(r.content)
        eq_(0, doc.find('.applications .empty').length)
        eq_(1, doc.find('.applications .application').length)

    def test_detail_application_approve_button(self):
        """For users with permission, the team application detail page should offer an approval button"""

        application = BadgeTeamApplication(
            team=self.team, creator=self.users['user'])
        application.save()

        self.client_login('owner')

        url = application.get_absolute_url()
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        
        button = doc.find('.approve-application')
        eq_(1, button.length)

    def test_approve_button_gone_once_approved(self):
        """Once a team application is approved, there is no longer an approval button"""

        application = BadgeTeamApplication(
            team=self.team, creator=self.users['user'])
        application.save()

        self.client_login('owner')

        url = application.get_absolute_url()

        doc = pq(self.client.get(url, follow=True).content)
        eq_(1, doc.find('.approve-application').length)

        application.approve(self.users['owner'])

        doc = pq(self.client.get(url, follow=True).content)
        eq_(0, doc.find('.approve-application').length)

    def test_detail_lists_members(self):
        """Team detail page should list current members"""
        url = self.team.get_absolute_url()

        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('.members .member .label .title:contains("owner1")').length)
        eq_(0, doc.find('.members .member .label .title:contains("user1")').length)

        self.team.add_member(self.users['user'])

        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('.members .member .label .title:contains("owner1")').length)
        eq_(1, doc.find('.members .member .label .title:contains("user1")').length)

    def test_detail_lists_badges(self):
        """Team detail page should list current badges"""
        url = self.team.get_absolute_url()

        doc = pq(self.client.get(url, follow=True).content)
        eq_(0, doc.find('.badges .badge .label .title:contains("test-badge")').length)

        badge = Badge(creator=self.users['user'], team=self.team,
                      title="test-badge", description="test-badge")
        badge.save()

        doc = pq(self.client.get(url, follow=True).content)
        eq_(1, doc.find('.badges .badge .label .title:contains("test-badge")').length)
