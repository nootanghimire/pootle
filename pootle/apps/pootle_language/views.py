# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.browser import make_project_item
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.views import (
    PootleBrowseView, PootleTranslateView, PootleExportView)
from pootle.core.views.admin import PootleAdminFormView, PootleAdminView
from pootle.i18n.gettext import tr_lang
from pootle_app.views.admin.permissions import admin_permissions
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from pootle_store.models import (
    QualityCheck, Suggestion, SuggestionStates, Unit)

from .forms import (
    LanguageSpecialCharsForm, LanguageSuggestionAdminForm, LanguageTeamAdminForm,
    LanguageUnitAdminForm)
from .models import Language


class LanguageMixin(object):
    model = Language
    browse_url_path = "pootle-language-browse"
    export_url_path = "pootle-language-export"
    translate_url_path = "pootle-language-translate"
    template_extends = 'languages/base.html'

    @property
    def language(self):
        return self.object

    @property
    def permission_context(self):
        return self.get_object().directory

    @property
    def url_kwargs(self):
        return {"language_code": self.object.code}

    @lru_cache()
    def get_object(self):
        lang = Language.get_canonical(self.kwargs["language_code"])
        if lang is None:
            raise Http404
        return lang

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.code != kwargs["language_code"]:
            return redirect(
                self.url_pattern_name,
                self.object.code,
                permanent=True)
        return super(LanguageMixin, self).get(*args, **kwargs)


class LanguageBrowseView(LanguageMixin, PootleBrowseView):
    url_pattern_name = "pootle-language-browse"
    table_id = "language"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @cached_property
    def items(self):
        return [
            make_project_item(tp)
            for tp in self.object.get_children_for_user(self.request.user)
        ]

    @property
    def language(self):
        return {
            'code': self.object.code,
            'name': tr_lang(self.object.fullname)}

    def get(self, *args, **kwargs):
        response = super(LanguageBrowseView, self).get(*args, **kwargs)
        response.set_cookie('pootle-language', self.object.code)
        return response


class LanguageTranslateView(LanguageMixin, PootleTranslateView):
    url_pattern_name = "pootle-language-translate"


class LanguageExportView(LanguageMixin, PootleExportView):
    url_pattern_name = "pootle-language-export"
    source_language = "en"


class LanguageTeamAdminView(PootleAdminView):
    form_class = LanguageTeamAdminForm
    template_name = "admin/language_team.html"

    @cached_property
    def language(self):
        return Language.objects.get(code=self.kwargs["language_code"])

    def get_context_data(self, **kwargs):
        context = super(LanguageTeamAdminView, self).get_context_data(**kwargs)
        permissions = self.language.directory.permission_sets.all()
        context["language"] = self.language
        context["admins"] = list(
            permissions.filter(positive_permissions__codename="administrate")
                       .exclude(negative_permissions__codename="administrate")
                       .values_list("user__username", flat=True))
        context["reviewers"] = list(
            permissions.filter(positive_permissions__codename="review")
                       .exclude(negative_permissions__codename="administrate")
                       .values_list("user__username", flat=True)
                       .exclude(user__username__in=context["admins"]))
        context["members"] = list(
            permissions.filter(positive_permissions__codename="suggest")
                       .exclude(negative_permissions__codename="administrate")
                       .values_list("user__username", flat=True)
                       .exclude(user__username__in=(context["admins"]
                                                    + context["reviewers"])))
        context["links"] = dict(
            unit_admin=reverse(
                "pootle-language-admin-units",
                kwargs=dict(language_code=self.language.code)),
            suggestion_admin=reverse(
                "pootle-language-admin-suggestions",
                kwargs=dict(language_code=self.language.code)))
        return context


class LanguageTeamAdminFormView(PootleAdminFormView):
    form_class = LanguageTeamAdminForm
    template_name = "admin/language_team_form.html"


@get_path_obj
@permission_required('administrate')
def language_admin(request, language):
    ctx = {
        'page': 'admin-permissions',

        'browse_url': reverse('pootle-language-browse', kwargs={
            'language_code': language.code,
        }),
        'translate_url': reverse('pootle-language-translate', kwargs={
            'language_code': language.code,
        }),

        'language': language,
        'directory': language.directory,
    }
    return admin_permissions(request, language.directory,
                             'languages/admin/permissions.html', ctx)


@get_path_obj
@permission_required('administrate')
def language_characters_admin(request, language):
    form = LanguageSpecialCharsForm(request.POST
                                    if request.method == 'POST'
                                    else None,
                                    instance=language)
    if form.is_valid():
        form.save()
        return redirect('pootle-language-browse', language.code)

    ctx = {
        'page': 'admin-characters',

        'browse_url': reverse('pootle-language-browse', kwargs={
            'language_code': language.code,
        }),
        'translate_url': reverse('pootle-language-translate', kwargs={
            'language_code': language.code,
        }),

        'language': language,
        'directory': language.directory,
        'form': form,
    }

    return render(request, 'languages/admin/characters.html', ctx)


class LanguageSuggestionAdminView(PootleAdminView):
    template_name = 'admin/language_team_suggestions.html'

    def get_context_data(self, **kwargs):
        language = get_object_or_404(
            Language,
            code=self.kwargs["language_code"])
        filter_user = self.request.GET.get('filteruser', '')
        if(filter_user.strip() == ''):
            suggestions = Suggestion.objects.filter(
            state=SuggestionStates.PENDING,
            unit__state__gt=OBSOLETE,
            unit__store__translation_project__language=language)
        else:
            suggestions = Suggestion.objects.filter(
            state=SuggestionStates.PENDING,
            unit__state__gt=OBSOLETE,
            unit__store__translation_project__language=language,
            user = filter_user)
        suggestions = suggestions.order_by("-creation_time")
        users = set(suggestions.values_list(
            "user__username",
            "user__full_name"))
        page = 1
        if self.request.GET:
            form = LanguageSuggestionAdminForm(self.refquest.GET)
            if form.is_valid():
                page = form.cleaned_data["page"]
        number_paginator = self.request.GET.get('perpage', '10')
        try:
            number_paginator = int(number_paginator)
        except ValueError:
            number_paginator = int(float(number_paginator))

        paginator = Paginator(suggestions, number_paginator)
        return dict(
            paginator=paginator,
            suggestions=paginator.page(page),
            users=users)


class LanguageUnitAdminView(PootleAdminView):
    template_name = 'admin/language_team_units.html'

    def get_context_data(self, **kwargs):
        language = get_object_or_404(
            Language,
            code=self.kwargs["language_code"])
        units = Unit.objects.filter(
            state__gt=OBSOLETE,
            store__translation_project__language=language)
        units = units.order_by("-creation_time")
        page = 1
        reviewers = set(units.values_list(
            "reviewed_by__username",
            "reviewed_by__full_name"))
        submitters = set(units.values_list(
            "submitted_by__username",
            "submitted_by__full_name"))
        checks = QualityCheck.objects.filter(unit__in=units)
        checks = set(checks.values_list("name", flat=True))
        states = [
            (TRANSLATED, "translated"),
            (FUZZY, "fuzzy"),
            (UNTRANSLATED, "untranslated")]

        if self.request.GET:
            form = LanguageUnitAdminForm(self.request.GET)
            if form.is_valid():
                page = form.cleaned_data["page"]
        paginator = Paginator(units, 10)
        units = paginator.page(page)
        return dict(
            paginator=paginator,
            reviewers=reviewers,
            submitters=submitters,
            checks=checks,
            states=states,
            units=units)
