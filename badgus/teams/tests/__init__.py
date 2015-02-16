import logging

from django.test import TestCase

from django.test.client import Client
from django.contrib.auth.models import User

from teamwork.models import Role
from badgus.teams.models import BadgeTeam, BadgeTeamApplication


class BadgeTeamTestCase(TestCase):

    def client_login(self, name='user'):
        self.client.login(username=self.users[name].username,
                          password=self.users[name].username)

    def setUp(self):
        self.client = Client()

        self.users = dict()
        users_data = {
            "owner": ("owner1", "owner1", "owner@example.com"),
            "user": ("user1", "user1", "user@example.com"),
            "member": ("member1", "member1", "member@example.com")
        }
        for name, (username, password, email) in users_data.items():
            (user,created) = User.objects.get_or_create(username=username, email=email)
            user.set_password(password)
            user.save()
            self.users[name] = user

        self.team = BadgeTeam(name='randoteam1')
        self.team.save()

        self.team.add_member(self.users['owner'], is_owner=True)

        self.team_url = self.team.get_absolute_url()

        self.member = self.team.add_member(self.users['member'])
