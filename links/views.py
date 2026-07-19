from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from .models import LinkItem, SiteProfile


def home(request):
    profile = SiteProfile.get_current()
    links = LinkItem.objects.filter(is_visible=True)
    return render(request, "links/home.html", {"profile": profile, "links": links})


def healthz(request):
    return HttpResponse("ok")


@transaction.atomic
def redirect_link(request, slug):
    try:
        link = LinkItem.objects.select_for_update().get(slug=slug, is_visible=True)
    except LinkItem.DoesNotExist as exc:
        raise Http404 from exc

    LinkItem.objects.filter(pk=link.pk).update(
        click_count=F("click_count") + 1,
        last_clicked_at=timezone.now(),
    )
    return HttpResponseRedirect(link.target_url)
