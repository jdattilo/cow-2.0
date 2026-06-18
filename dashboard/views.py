from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import loader, render
from django.template import RequestContext
from ae2.models import AE2INSTALL, AE2RUN, suite, env, AEBranch
from runs.models import Run
from aetests.models import Test
from bamboo.models import BAMBOOINSTALL
from cluster.models import cluster_member, cluster_health
import socket
import os
from subprocess import check_output
import subprocess
from crontab import CronTab
import os.path
import sys
from django.http import Http404
from django.http import HttpResponseRedirect
from django.forms import ModelForm, Textarea
from runs.models import Run
import time
from activities.models import activity
from enqueued.models import job


class RunEdit(ModelForm):

    class Meta:
        model = Run
        fields = ['run_results']


class CowModeEdit(ModelForm):

    class Meta:
        model = AE2INSTALL
        fields = ['cow_mode']


RUNNING_DEVSERVER = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')


SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def svnversion(address):
    p = subprocess.Popen("svnversion " + address, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    return stdout


def svnhead(address):
    p = subprocess.Popen(
        "svn info " +
        address +
        " -r HEAD | sed -n 's/^Last Changed Rev: //p'",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    return stdout


def cow_update(request):
    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('created_at')
    if runInfo.running:
        return HttpResponse(
            "<html><header></header><body>ERROR:Cannot update while a test is running.</body><footer></footer></html>")

    else:
        subprocess.Popen(
            "/bin/bash " +
            SITE_ROOT +
            "/update_script.sh " +
            SITE_ROOT,
            shell=True)
    return HttpResponse(
        "<html><header><script>function f() { parent.location.reload(); } window.setTimeout(f, 180000);</script></header><body>Running: /bin/bash " +
        SITE_ROOT +
        "/update_script.sh\n\n This could take a while...</body><footer></footer></html>")


def cow_update_external(request):
    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('created_at')
    if runInfo.running:
        return HttpResponse("ERROR:Cannot update while a test is running.")

    else:
        subprocess.Popen(
            "/bin/bash " +
            SITE_ROOT +
            "/update_script.sh " +
            SITE_ROOT,
            shell=True)
    return HttpResponse(
        "Running: /bin/bash " +
        SITE_ROOT +
        "/update_script.sh\n\n This could take a while...")


def cow_version(request):
    return HttpResponse(str(svnversion(SITE_ROOT)))


def index(request):
    # #########Get COW Status and operation information############
    cowstatus = {
        "dev": RUNNING_DEVSERVER,
        "root": SITE_ROOT,
        "crontab": "UNKNOWN",
        "host": socket.gethostname(),
        "revision": svnversion(SITE_ROOT),
        "head": svnhead(SITE_ROOT)}
    # check crontab

    cmd = sys.executable + ' ' + SITE_ROOT + '/manage.py runserver 0.0.0.0:80'
    tab = CronTab(user="root")

    cron_job = tab.find_command(cmd)
    if len(list(cron_job)) > 0:
        cowstatus["crontab"] = "<b style='color:green;'>Present.</b>"
    else:
        cowstatus[
            "crontab"] = "<b style ='color:red;'>Missing, have you run 'manage.py install' for this installation?</b>"

    # ###########Get/initialize AE2 settings##############
    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory="/root/ae2",
            branch="https://sqa.yourdomain.com/tools/AwesomeExpress/branches/butterjunk/",
            revision=-1,
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]

    AE2Suites = suite.objects.all()
    AE2Environments = env.objects.all()
    # check AE2
    # Check moved to systemcheck view.

    # ################Get/Check Cluster###################
    if cluster_health.objects.count() == 0:
        initialHealth = cluster_health()
        initialHealth.save()

    ClusterHealthObject = cluster_health.objects.all()[0]

    myClusterMembers = cluster_member.objects.all()

    # ################Check Bamboo######################
    if BAMBOOINSTALL.objects.count() == 0:
        initialBamboo = BAMBOOINSTALL(
            jarfile='/root/atlassian-bamboo-agent-installer-5.8.1.jar',
            bamboohost="http://bamboo.yourdomain.com/agentServer/",
            crontab=False,
            enabled=False,
            running=False)
        initialBamboo.save()

    BambooSettings = BAMBOOINSTALL.objects.all()[0]

    # #################Check if AE2 is Running###########
    runInfo = [
        AE2RUN(
            suite="NA",
            env="NA",
            running=False,
            paused=False,
            passed=True)]  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.order_by('-pk')[0]
        runInfo = AE2RUN.objects.filter(
            buildnumber=runInfo.buildnumber).order_by('-pk')

    # #################Check for linked run##############
    runobject = Run.objects.none()
    testgroup = Test.objects.none()
    myform = None
    if len(Run.objects.all().filter(build_number=runInfo[0].buildnumber)) > 0:
        runobject = Run.objects.all().filter(
            build_number=runInfo[0].buildnumber)  # including all of same number
        for myrun in runobject:
            testgroup = testgroup | Test.objects.all().filter(
                parentrun=myrun).order_by("-test_sequence_number")
        myform = RunEdit(request.POST or None, instance=runobject[0])

    # ################Cow Mode Form#####################

    # ################  ##################
    myaebranches = AEBranch.objects.all()

    cowmodeform = CowModeEdit(request.POST or None, instance=AE2Settings)
    # #################Check Fluid Cache#################

    # #################Monitor Testing###################

    stdiolog = ""
    try:
        with open(SITE_ROOT + "/logs/stdio.log", "r") as myfile:
            myfile.seek(-1100, os.SEEK_END)
            stdiolog = myfile.read().split("\n", 1)[-1]
    except:
        stdiolog = "ERROR: STDIO File Not Found."

    ae2log = ""
    try:
        with open(AE2Settings.install_directory + "/src/logs/cow-ae-run.log", "r") as myfile:
            myfile.seek(-300, os.SEEK_END)
            ae2log = myfile.read().split("\n", 1)[-1]
    except:
        ae2log = "ERROR: AE2 Log File Not Found."

    # change opentab to match the first failed or group that needs monitoring
    opentab = 4
    if(not AE2Settings.present or AE2Settings.cow_mode == 2):
        opentab = 0
    elif not ClusterHealthObject.ping or (not ClusterHealthObject.ssh and not ClusterHealthObject.rpc) and not ClusterHealthObject.empty:
        opentab = 1
    # elif BambooSettings.running == False and BambooSettings.enabled != False:
    #    opentab = 2
    elif not runInfo[0].running or (runInfo[0].needs_triage and runInfo[0].running):
        opentab = 2
    # elif False: #place holder for cluster monitoring
    #    opentab = 4
    else:
        opentab = 3

    template = loader.get_template('dashboard/guided-unbound.html')
    context = RequestContext(request, {
        "message": "Nothing to see here.",
        "request": request,
        "cowstatus": cowstatus,
        "opentab": opentab,
        "AE2Settings": AE2Settings,
        "AE2Suites": AE2Suites,
        "AE2Environments": AE2Environments,
        "runInfo": runInfo,
        "runobjects": runobject,
        "testgroup": testgroup,
        "ClusterHealthObject": ClusterHealthObject,
        "myClusterMembers": myClusterMembers,
        "BambooSettings": BambooSettings,
        "ae2log": ae2log,
        "stdiolog": stdiolog,
        "myform": myform,
        "cowmodeform": cowmodeform,
        "myaebranches": myaebranches,
    })
    return HttpResponse(template.render(context))


def activityLogs(request):
    # #########Get COW Status and operation information############
    cowstatus = {
        "dev": RUNNING_DEVSERVER,
        "root": SITE_ROOT,
        "crontab": "UNKNOWN",
        "host": socket.gethostname()}
    # check crontab

    cmd = sys.executable + ' ' + SITE_ROOT + '/manage.py runserver 0.0.0.0:80'
    tab = CronTab(user="root")

    cron_job = tab.find_command(cmd)
    if len(list(cron_job)) > 0:
        cowstatus["crontab"] = "<b style='color:green;'>Present.</b>"
    else:
        cowstatus[
            "crontab"] = "<b style ='color:red;'>Missing, have you run 'manage.py install' for this installation?</b>"

    # ###########Get/initialize AE2 settings##############
    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory="/root/ae2",
            branch="https://sqa.yourdomain.com/tools/AwesomeExpress/branches/butterjunk/",
            revision=-1,
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]

    # #################Check if AE2 is Running###########
    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('created_at')

    myActivities = activity.objects.all().order_by('-created_at')
    myJobs = job.objects.all().order_by('-created_at')

    latest_logs = list(myActivities) + list(myJobs)
    latest_logs = sorted(latest_logs, key=lambda x: x.created_at, reverse=True)

    template = loader.get_template('dashboard/activity-log.html')
    context = RequestContext(request, {
        "request": request,
        "cowstatus": cowstatus,
        "AE2Settings": AE2Settings,
        "runInfo": runInfo,
        "latest_logs": latest_logs,
    })
    return HttpResponse(template.render(context))


def runLogs(request):
    # #########Get COW Status and operation information############
    cowstatus = {
        "dev": RUNNING_DEVSERVER,
        "root": SITE_ROOT,
        "crontab": "UNKNOWN",
        "host": socket.gethostname()}
    # check crontab

    cmd = sys.executable + ' ' + SITE_ROOT + '/manage.py runserver 0.0.0.0:80'
    tab = CronTab(user="root")

    cron_job = tab.find_command(cmd)
    if len(list(cron_job)) > 0:
        cowstatus["crontab"] = "<b style='color:green;'>Present.</b>"
    else:
        cowstatus[
            "crontab"] = "<b style ='color:red;'>Missing, have you run 'manage.py install' for this installation?</b>"

    # ###########Get/initialize AE2 settings##############
    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory="/root/ae2",
            branch="https://sqa.yourdomain.com/tools/AwesomeExpress/branches/butterjunk/",
            revision=-1,
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]

    # #################Check if AE2 is Running###########
    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('updated_at')

    myActivities = activity.objects.all().order_by('-created_at')
    myJobs = job.objects.all().order_by('-created_at')

    latest_logs = list(myActivities) + list(myJobs)
    latest_logs = sorted(latest_logs, key=lambda x: x.created_at, reverse=True)

    myRuns = Run.objects.all().order_by('-end_time')

    template = loader.get_template('dashboard/runs.html')
    context = RequestContext(request, {
        "request": request,
        "cowstatus": cowstatus,
        "AE2Settings": AE2Settings,
        "runInfo": runInfo,
        "myRuns": myRuns,
        "latest_logs": latest_logs,
    })
    return HttpResponse(template.render(context))


def logview(request, logname, build_number):
    runInfo = AE2RUN.objects.latest('updated_at')

    # return HttpResponse(str(build_number)+" < " +str(runInfo.buildnumber)+"
    # = "+str(int(build_number) < int(runInfo.buildnumber)))

    if int(build_number) < int(runInfo.buildnumber):
        return HttpResponseRedirect(
            "http://cowtracks.yourdomain.com/view/" +
            socket.gethostname() +
            "/" +
            build_number +
            "/" +
            logname)
    elif int(build_number) == int(runInfo.buildnumber) and not runInfo.running:
        return HttpResponseRedirect(
            "http://cowtracks.yourdomain.com/view/" +
            socket.gethostname() +
            "/" +
            build_number +
            "/" +
            logname)

    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory="/root/ae2",
            branch="https://sqa.yourdomain.com/tools/AwesomeExpress/branches/butterjunk/",
            revision=-1,
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]

    mylog = None
    loginfo = {"logname": mylog}

    if logname == "stdio.log":
        try:
            with open(SITE_ROOT + "/logs/stdio.log", "r") as myfile:
                mylog = myfile.read()
        except:
            mylog = "ERROR: Attempted to read, but STDIO File Not Found."

    elif logname == "cow-ae-run.log":
        try:
            with open(AE2Settings.install_directory + "/src/logs/cow-ae-run.log", "r") as myfile:
                mylog = myfile.read()
        except:
            mylog = "ERROR: AE2 Log File Not Found."

    elif logname == "cow-ae-run_debug.log":
        try:
            with open(AE2Settings.install_directory + "/src/logs/cow-ae-run_debug.log", "r") as myfile:
                mylog = myfile.read()
        except:
            mylog = "ERROR: AE2 Debug Log File Not Found."
    else:
        raise Http404("Error...")

    template = loader.get_template('dashboard/logview.html')
    context = RequestContext(request, {
        "loginfo": loginfo,
        "mylog": mylog,
    })
    return HttpResponse(template.render(context))


# microtime function for calculations of time difference


def microtime(get_as_float=False):
    """converts an integer or float to microtime"""
    if get_as_float:
        return time.time()
    else:
        return '%f %d' % math.modf(time.time())


def buildbot_json_simulator(request):
    runInfo = AE2RUN.objects.latest('updated_at')
    myrun = Run.objects.all().filter(build_number=runInfo.buildnumber)[0]

    if myrun.end_time != myrun.start_time:
        mytimings = {
            "start": time.mktime(
                myrun.start_time.timetuple()), "end": time.mktime(
                myrun.end_time.timetuple())}
    else:
        mytimings = {
            "start": time.mktime(
                myrun.start_time.timetuple()),
            "end": None}

    template = loader.get_template('dashboard/buildbot_json_simulator.html')
    context = RequestContext(request, {
        "runInfo": runInfo,
        "timing": mytimings,
    })
    return HttpResponse(template.render(context))
