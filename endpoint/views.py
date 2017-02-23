from django.shortcuts import render
from django.http import HttpResponse
from endpoint import dbupdater
from endpoint import classifier
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
@csrf_exempt
def update(request):
    if request.method == 'POST':
        if 'feed' not in request.POST.keys():
            entries = dbupdater.get_entries()
        else:
            entries = dbupdater.get_entries(request.POST['feed'])
        entries = classifier.classify(entries)
        dbupdater.push_entries(entries)

    return HttpResponse(status = 200)
