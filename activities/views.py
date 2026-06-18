from django.shortcuts import render
from activities.models import activity
# Create your views here.


def logActivity(request, action, arguments):
    username = None
    if request.user.is_authenticated():
        username = request.user.username

    myActivity = activity(action=action, user=username, arguments=arguments)
    myActivity.save()


def systemlogActivity(action, arguments):
    username = "System"
    myActivity = activity(action=action, user=username, arguments=arguments)
    myActivity.save()
