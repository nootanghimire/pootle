# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from collections import OrderedDict


UNITS_TEXT_SEARCH_TESTS = OrderedDict()
UNITS_TEXT_SEARCH_TESTS["exact:Translated (source)"] = {
    "text": "Translated",
    "sfields": ["source"]}
UNITS_TEXT_SEARCH_TESTS["exact:Translated (source/target)"] = {
    "text": "Translated",
    "sfields": ["source", "target"]}
UNITS_TEXT_SEARCH_TESTS["Suggestion for Translated (target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["suggestion for TRANSLATED (target)"] = {
    "text": "suggestion for TRANSLATED",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["suggestion for translated (source)"] = {
    "text": "suggestion for translated",
    "sfields": ["source"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["suggestion for translated (source/target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target", "source"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion for translated (target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion for translated (source/target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target", "source"]}
UNITS_TEXT_SEARCH_TESTS["suggestion translated for (target)"] = {
    "text": "suggestion translated for",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion translated for (target)"] = {
    "text": "suggestion translated for",
    "sfields": ["target"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["FOO BAR"] = {
    "sfields": ["target", "source"],
    "empty": True}
# hmm - not 100% if this should pass or fail
UNITS_TEXT_SEARCH_TESTS["suggestion for translated FOO (target)"] = {
    "text": "suggestion translated for FOO",
    "sfields": ["target"],
    "empty": True}

UNITS_CONTRIB_SEARCH_TESTS = [
    "suggestions",
    "FOO",
    "member:my_suggestions",
    "my_suggestions",
    "member:user_suggestions",
    "user_suggestions",
    "member:user_suggestions_accepted",
    "user_suggestions_accepted",
    "member:user_suggestions_rejected",
    "user_suggestions_rejected",
    "member:my_submissions",
    "my_submissions",
    "member:user_submissions",
    "user_submissions",
    "member:my_submissions_overwritten",
    "my_submissions_overwritten",
    "member:user_submissions_overwritten",
    "user_submissions_overwritten"]

UNITS_STATE_SEARCH_TESTS = [
    "all",
    "translated",
    "untranslated",
    "fuzzy",
    "incomplete",
    "FOO"]

UNITS_CHECKS_SEARCH_TESTS = [
    "checks:foo",
    "category:foo",
    "category:critical",
    "checks:endpunc",
    "checks:endpunc,printf",
    "checks:endpunc,foo"]


@pytest.fixture(params=UNITS_STATE_SEARCH_TESTS)
def units_state_searches(request):
    return request.param


@pytest.fixture(params=UNITS_CHECKS_SEARCH_TESTS)
def units_checks_searches(request):
    from pootle_misc.checks import get_category_id

    check_type, check_data = request.param.split(":")
    if check_type == "category":
        return check_type, get_category_id(check_data)
    return check_type, check_data.split(",")


@pytest.fixture(params=UNITS_CONTRIB_SEARCH_TESTS)
def units_contributor_searches(request):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if ":" in request.param:
        username, unit_filter = request.param.split(":")
        user = User.objects.get(username=username)
    else:
        user = None
        unit_filter = request.param
    return unit_filter, user


@pytest.fixture(params=UNITS_TEXT_SEARCH_TESTS.keys())
def units_text_searches(request):
    text = request.param
    if text.startswith("exact:"):
        text = text[6:]
        exact = True
    else:
        exact = False
    test = UNITS_TEXT_SEARCH_TESTS[request.param]
    test["text"] = test.get("text", text)
    test["empty"] = test.get("empty", False)
    test["exact"] = exact
    return test