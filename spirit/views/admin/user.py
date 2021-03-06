# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.translation import ugettext as _

from djconfig import config

from ...utils.paginator import yt_paginate
from spirit.utils.decorators import administrator_required
from spirit.utils.user.email import send_verification_email

from spirit.forms.admin import UserEditForm


User = get_user_model()


@administrator_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        is_verified = user.is_verified and user.is_active
        form = UserEditForm(data=request.POST, instance=user)

        if form.is_valid():
            form.save()
            if not is_verified and user.is_verified and user.is_active:
                send_verification_email(request, user)
            messages.info(request, _("This profile has been updated!"))
            return redirect(request.GET.get("next", request.get_full_path()))
    else:
        form = UserEditForm(instance=user)

    context = {'form': form, }

    return render(request, 'spirit/admin/user/user_edit.html', context)


def get_users_context(users):
    return {
        'users': users,
        'show_verified_tab': settings.ST_APPROVE_NEW_USERS,
    }

@administrator_required
def user_list(request):
    users = yt_paginate(
        User.objects.all(),
        per_page=config.topics_per_page,
        page_number=request.GET.get('page', 1)
    )
    context = {'users': users, }
    return render(request, 'spirit/admin/user/user_list.html', context)


@administrator_required
def user_admins(request):
    users = yt_paginate(
        User.objects.filter(is_administrator=True),
        per_page=config.topics_per_page,
        page_number=request.GET.get('page', 1)
    )
    context = {'users': users, }
    return render(request, 'spirit/admin/user/user_admins.html', context)


@administrator_required
def user_mods(request):
    users = yt_paginate(
        User.objects.filter(is_moderator=True, is_administrator=False),
        per_page=config.topics_per_page,
        page_number=request.GET.get('page', 1)
    )
    context = {'users': users, }
    return render(request, 'spirit/admin/user/user_mods.html', context)


@administrator_required
def user_unactive(request):
    users = User.objects.filter(is_active=False)
    return render(request, 'spirit/admin/user/user_unactive.html', get_users_context(users))

@administrator_required
def user_unverified(request):
    users = yt_paginate(
        User.objects.filter(is_active=False),
        per_page=config.topics_per_page,
        page_number=request.GET.get('page', 1)
    )
    context = {'users': users, }
    return render(request, 'spirit/admin/user/user_unactive.html', context)
