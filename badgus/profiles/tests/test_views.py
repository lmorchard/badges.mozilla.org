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
