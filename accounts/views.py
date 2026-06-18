from django.shortcuts import render
from django.shortcuts import loader, render
# Create your views here.
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from activities.views import logActivity


def login_user(request):
    state = "Please log in below..."
    username = password = ''

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = "You're successfully logged in!"
                logActivity(
                    request=request,
                    action="Logged in",
                    arguments={
                        "user": user})

                if 'next' in request.GET:
                    return HttpResponseRedirect(request.GET.get('next'))
                    state = "Failed to redirect"
                else:
                    return HttpResponseRedirect(
                        request.META.get('HTTP_REFERER'))
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."

    template = loader.get_template('accounts/login.html')
    context = RequestContext(request, {
        "state": state,
        "username": username,
    })
    return HttpResponse(template.render(context))


def logout_user(request):
    logActivity(request=request, action="Logged out", arguments={})
    logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
