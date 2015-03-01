import logging

import json
from nose.tools import eq_, ok_
from django.test import TestCase
from django.http import HttpRequest
from django import test

from django.contrib.auth.models import User

from pyquery import PyQuery as pq
from django_browserid.tests import mock_browserid

from tower import activate

from teamwork.models import Role

from badger.models import Badge

from badgus.base.urlresolvers import reverse
from badgus.teams.models import BadgeTeam


class BadgeProfileViewsTest(test.TestCase):

    def test_list_team_membership(self):
        """User profile page should list team memberships"""
        team = BadgeTeam(name='randoteam23')
        team.save()

        team.members.through.objects.all().delete()

        member = User(username='rando23', email='random23@example.com')
        member.save()

        url = member.get_absolute_url()

        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(0, doc.find('.teams .team .label .title:contains("randoteam23")').length)

        team.add_member(member)

        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('.teams .team .label .title:contains("randoteam23")').length)

    def _client_login(self, name):
        self.client.login(username=name, password=name)

    def test_remove_member(self):
        """Teams listed should have revocation buttons when viewed with appropriate permissions"""
        rando = User(username='rando23', email='rando23@example.com')
        rando.set_password('rando23')
        rando.save()

        owner = User(username='owner23', email='owner23@example.com')
        owner.set_password('owner23')
        owner.save()

        member = User(username='member23', email='member23@example.com')
        member.set_password('member23')
        member.save()

        team1 = BadgeTeam(name='randoteam46')
        team1.save()
        
        team2 = BadgeTeam(name='randoteam69')
        team2.save()

        team1.add_member(owner, is_owner=True)
        team1.add_member(member)
        team2.add_member(member)

        url = member.get_absolute_url()

        button_selector_tmpl = '.teams .team .remove_member[data-team-slug=%s]'
        cases = ( ('rando23', 0, 0), ('owner23', 1, 0), ('member23', 1, 1) )
        for username, expected_team1_count, expected_team2_count in cases:
            self._client_login(username)
            doc = pq(self.client.get(url, follow=True).content)
            eq_(expected_team1_count, doc.find(button_selector_tmpl % team1.slug).length)
            eq_(expected_team2_count, doc.find(button_selector_tmpl % team2.slug).length)
