from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import (DetailView, SingleObjectMixin, 
                                         SingleObjectTemplateResponseMixin)
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group, Permission

from tower import ugettext_lazy as _

from teamwork.models import Team, Role, Policy, Member

from .models import BadgeTeam, BadgeTeamApplication

from badger.models import Badge


TEAMS_PAGE_SIZE = 50


def object_permission_required(perm):
    def decorator(func):
        def _wrapper(self, request, *args, **kwargs):
            if not request.user.has_perm(perm, self.get_object()):
                raise PermissionDenied
            return func(self, request, *args, **kwargs)
        return _wrapper
    return decorator


class TeamListView(ListView):
    """Teams list page"""
    model = BadgeTeam
    
    def get_context_data(self, **kwargs):
        context = super(TeamListView, self).get_context_data(**kwargs)
        return context

    @method_decorator(permission_required('teams.list_badgeteam'))
    def dispatch(self, request, *args, **kwargs):
        return super(TeamListView, self).dispatch(request, *args, **kwargs)


class TeamDetailView(DetailView):
    model = BadgeTeam
    
    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)

        context['memberships'] = [
            (member, BadgeTeam.objects.get(team_ptr__pk=member.team.pk))
            for member in Member.objects.filter(team=self.object)]
        context['badge_list'] = Badge.objects.filter(team=self.object)

        context['existing_application'] = None
        if self.request.user.is_authenticated():
            try:
                context['existing_application'] = (BadgeTeamApplication.objects
                    .filter(team=self.object.team, creator=self.request.user)
                    .first())
            except BadgeTeamApplication.DoesNotExist:
                pass
        return context

    @object_permission_required('teams.view_badgeteam')
    def dispatch(self, request, *args, **kwargs):
        return super(TeamDetailView, self).dispatch(request, *args, **kwargs)


class TeamCreateView(CreateView):
    model = BadgeTeam
    fields = ['name', 'image', 'description']

    def form_valid(self, form):
        result = super(TeamCreateView, self).form_valid(form)
        form.instance.add_member(self.request.user, is_owner=True)
        return result

    @method_decorator(login_required)
    @method_decorator(permission_required('teams.add_badgeteam'))
    def dispatch(self, request, *args, **kwargs):
        return super(TeamCreateView, self).dispatch(request, *args, **kwargs)


class TeamUpdateView(UpdateView):
    model = BadgeTeam
    fields = ['name', 'image', 'description']

    @method_decorator(login_required)
    @object_permission_required('teams.change_badgeteam')
    def dispatch(self, request, *args, **kwargs):
        return super(TeamUpdateView, self).dispatch(request, *args, **kwargs)


class TeamDeleteView(DeleteView):
    model = BadgeTeam
    success_url = reverse_lazy('teams.home')

    @method_decorator(login_required)
    @object_permission_required('teams.delete_badgeteam')
    def dispatch(self, request, *args, **kwargs):
        return super(TeamDeleteView, self).dispatch(request, *args, **kwargs)


class TeamApplicationCreateView(CreateView):
    model = BadgeTeamApplication
    fields = ['comment']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        return super(TeamApplicationCreateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(TeamApplicationCreateView, self).get_context_data(**kwargs)
        context['badgeteam'] = self.team
        return context

    def form_valid(self, form):
        form.instance.team = self.team
        form.instance.creator = self.request.user
        return super(TeamApplicationCreateView, self).form_valid(form)


class TeamApplicationListView(ListView):
    model = BadgeTeamApplication

    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        if not request.user.has_perm('teams.list_badgeteamapplication', self.team):
            raise PermissionDenied
        return super(TeamApplicationListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (super(TeamApplicationListView, self)
            .get_queryset()
            .filter(team = self.team,
                    approver__isnull=(not 'approved' in self.request.GET)))

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(TeamApplicationListView, self).get_context_data(**kwargs)
        context['team'] = self.team
        return context


class TeamApplicationDetailView(DetailView):
    model = BadgeTeamApplication

    @method_decorator(login_required)
    @object_permission_required('teams.view_badgeteamapplication')
    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        return super(TeamApplicationDetailView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(TeamApplicationDetailView, self).get_context_data(**kwargs)
        context['team'] = self.team
        return context


class TeamApplicationDeleteView(DeleteView):
    model = BadgeTeamApplication

    @method_decorator(login_required)
    @object_permission_required('teams.delete_badgeteamapplication')
    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        self.success_url = self.team.get_absolute_url()
        return super(TeamApplicationDeleteView, self).dispatch(request, *args, **kwargs)


class TeamApplicationApproveView(View, SingleObjectMixin):
    model = BadgeTeamApplication

    @method_decorator(login_required)
    @object_permission_required('teams.approve_badgeteamapplication')
    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        self.success_url = self.team.get_absolute_url()
        return super(TeamApplicationApproveView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.object.get_absolute_url()
        self.object.approve(request.user)
        return HttpResponseRedirect(success_url)


class TeamMemberDeleteView(DeleteView):
    template_name = 'teams/member_confirm_delete.html'
    model = Member

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('teams.remove_member', self.team):
            raise PermissionDenied
        self.success_url = self.user.get_absolute_url()
        return super(TeamMemberDeleteView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Member.objects.filter(team=self.team, user=self.user)

    def get_object(self, queryset=None):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        self.user = get_object_or_404(User, username=self.kwargs['username'])

        queryset = self.get_queryset()
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_context_data(self, **kwargs):
        context = super(TeamMemberDeleteView, self).get_context_data(**kwargs)
        context['team'] = self.team
        context['user'] = self.user
        return context

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.team.remove_member(self.user)
        return HttpResponseRedirect(success_url) 


class TeamMemberConfirmView(TemplateView):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(BadgeTeam, slug=self.kwargs['team_slug'])
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        self.member = get_object_or_404(Member, team=self.team, user=self.user)
        
        if not request.user.has_perm(self.permission_name, self.team):
            raise PermissionDenied

        self.success_url = self.team.get_absolute_url()
        return super(TeamMemberConfirmView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TeamMemberConfirmView, self).get_context_data(**kwargs)
        context['team'] = self.team
        context['user'] = self.user
        context['member'] = self.member
        return context


class TeamMemberPromoteView(TeamMemberConfirmView):
    template_name = 'teams/member_confirm_promote.html'
    permission_name = 'teams.promote_member'

    def post(self, request, *args, **kwargs):
        self.member.is_owner = True
        self.member.save()
        return HttpResponseRedirect(self.success_url) 


class TeamMemberDemoteView(TeamMemberConfirmView):
    template_name = 'teams/member_confirm_demote.html'
    permission_name = 'teams.demote_member'

    def post(self, request, *args, **kwargs):
        self.member.is_owner = False
        self.member.save()
        return HttpResponseRedirect(self.success_url) 
