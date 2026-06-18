from django.shortcuts import render
from django.shortcuts import loader, render
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from models import job
from ae2.models import AE2INSTALL, AE2RUN
from ae2.functions import ChangeEnvironment
import subprocess
import socket
from functions import jobmatrix, cattleserver, run_ae2
import requests
import json
from runs.models import Run
from django.utils import timezone
from cluster.models import cluster_member
import logging
import os
import shutil
from ae2.views import populate_files
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response

SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def view(request):
    # This should render the queue for dashboard and other views
    return HttpResponse(
        "<html><body>This should render the queue for dashboard and other views</body></html>")


def report(request):
    # This should render specific views of the queue and its history.
    return HttpResponse(
        "<html><body>This should render specific views of the queue and its history.</body></html>")


def runnext(request):
    # This should run the next queued job
    secondaryjobs = job.objects.exclude(
        command="ae2run").exclude(
        attempted=True)
    if secondaryjobs.count() > 0:
        myjob = secondaryjobs[0]
        # try:
        myjob.attempted = True

        myresults = jobmatrix(myjob)
        if myresults["exitcode"] == -1:
            myjob.attempt_result = -1
        else:
            myjob.attempt_result = 0

        myjob.command_results = myresults["exitcode"]
        myjob.command_message = myresults["message"]
        myjob.save()
        return HttpResponse("Job with id:" +
                            str(myjob.pk) +
                            " just ran, with message:" +
                            str(myresults["message"]))
        # except:
        #    myjob.attempted=True
        #    myjob.attempt_result=1
        #    myjob.save()
        return HttpResponse(
            "--!!ERROR: Failed to run job id:" + str(myjob.pk) + "!!--")

    return HttpResponse("--There are " +
                        str(secondaryjobs.count()) +
                        " other Jobs in the queue.--")


def runae2(request):
    # This should run the next queued ae2 run
    ae2jobs = job.objects.filter(command="ae2run").exclude(attempted=True)
    if ae2jobs.count() > 0:
        if AE2INSTALL.objects.count() == 0:
            initialAE2 = AE2INSTALL(
                install_directory=ae2directory,
                branch=ae2branch,
                revision=ae2revision,
                autopull=False,
                present=False)
            initialAE2.save()
        AE2Settings = AE2INSTALL.objects.all()[0]

        myae2run = ae2jobs[0]
        if myae2run.arguments is not None:
            if "suite" in myae2run.arguments and "env" in myae2run.arguments:
                ae2python = "/opt/python2.7/bin/python2.7"
                ae2suite = myae2run.arguments["suite"]
                if ae2suite == "" or ae2suite == "auto":  # default to systems automation defaults if none or auto is provided
                    ae2suite = AE2Settings.automated_suite
                ae2env = myae2run.arguments["env"]
                if ae2env == "" or ae2env == "auto":  # default to systems automation defaults if none or auto is provided
                    ae2env = AE2Settings.automated_env
                fldcrpm = myae2run.arguments["rpm"]
                fldctools = myae2run.arguments["tools"]
                fldcbranch = myae2run.arguments["branch"]
                fldccommit = myae2run.arguments["commit"]
                cleanup = 0
                if "cleanup" in myae2run.arguments.keys():  # check if cleanup exists
                    cleanup = myae2run.arguments["cleanup"]

                if cleanup != 0:
                    cleanup = Run.objects.all().filter(
                        build_number=getnextbuildnumber()[0] - 1).count()

                if fldccommit == "":
                    fldccommit = -1
                fldcmuted = myae2run.arguments["muted"]
                runInfo = AE2RUN(
                    suite="NA",
                    env="NA",
                    branch="NA",
                    commit="NA",
                    buildnumber=0,
                    running=False,
                    paused=False,
                    passed=True,
                    cleanup=cleanup)  # This is in case of no runs existing
                if len(AE2RUN.objects.all()) > 0:
                    runInfo = AE2RUN.objects.latest('updated_at')
                if runInfo.running:
                    return HttpResponse(
                        "--Your request cannot be completed because there is already a test running.--")
                else:
                    myRun = None
                    if cleanup == 0:
                        myRun = AE2RUN(
                            suite=ae2suite.strip(
                                AE2Settings.install_directory +
                                "src/"),
                            env=ae2env.strip(
                                AE2Settings.install_directory +
                                "src/"),
                            rpm=fldcrpm,
                            tools=fldctools,
                            branch=fldcbranch,
                            commit=fldccommit,
                            muted=fldcmuted,
                            buildnumber=getnextbuildnumber()[0],
                            running=True,
                            paused=False,
                            passed=True)
                        myRun.save()
                    else:
                        myRun = AE2RUN(
                            suite=ae2suite.strip(
                                AE2Settings.install_directory + "src/"),
                            env=ae2env.strip(
                                AE2Settings.install_directory + "src/"),
                            rpm=fldcrpm,
                            tools=fldctools,
                            branch=fldcbranch,
                            commit=fldccommit,
                            muted=fldcmuted,
                            buildnumber=getnextbuildnumber()[0] - 1,
                            running=True,
                            paused=False,
                            passed=True)
                        myRun.save()

                    myParentRun = Run(
                        build_number=myRun.buildnumber,
                        commit=myRun.commit,
                        suite_file=myRun.suite,
                        env_file=myRun.env,
                        parent_branch=myRun.branch,
                        operating_system=AE2Settings.automated_os,
                        log_file="",
                        run_results=13)
                    myParentRun.save()

                    logger = logging.getLogger('run_logger')
                    logger.setLevel(logging.DEBUG)
                    # logging.Formatter.converter = time.localtime
                    formatter = logging.Formatter(
                        '%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")
                    # formatter.converter = time.localtime
                    ch_stream = logging.StreamHandler()
                    ch_stream.setFormatter(formatter)
                    ch_stream.setLevel(logging.DEBUG)
                    logger.addHandler(ch_stream)
                    file_stream = logging.FileHandler(
                        SITE_ROOT + "/logs/stdio.log", 'w')
                    file_stream.setFormatter(formatter)
                    file_stream.setLevel(logging.DEBUG)
                    logger.addHandler(file_stream)
                    logger.debug(
                        "Log handler initiated in COW runae2 function following creation of Run object.")

                    logger.debug(
                        "COW refreshing suite, environment, and svn info for installed version of Awesome Express.")
                    try:
                        if populate_files(AE2Settings.install_directory):
                            logger.debug("COW AE Refresh was successful.")
                        else:
                            logger.debug(
                                "COW AE refresh did not complete without errors.")
                    except Exception as e:
                        logger.warning(
                            "COW AE refresh encountered an unexpected exception " + e.message)

                    logger.debug("Cleanup is set to: " + str(cleanup))

                    try:
                        # attempt to delete existing cow logs
                        os.remove(
                            AE2Settings.install_directory +
                            "/src/logs/cow-ae-run.log")
                        logger.debug(
                            "Successfully removed log file " +
                            AE2Settings.install_directory +
                            "/src/logs/cow-ae-run.log")
                    except Exception as e:
                        logger.warning(
                            "Failed to remove log file " +
                            AE2Settings.install_directory +
                            "/src/logs/cow-ae-run.log: " +
                            e.message)

                    try:
                        # attempt to delete existing cow debug logs
                        os.remove(
                            AE2Settings.install_directory +
                            "/src/logs/cow-ae-run_debug.log")
                        logger.debug(
                            "Successfully removed log file " +
                            AE2Settings.install_directory +
                            "/src/logs/cow-ae-run_debug.log")
                    except Exception as e:
                        logger.warning(
                            "Failed to remove log file " +
                            AE2Settings.install_directory +
                            "/src/logs/cow-ae-run_debug.log " +
                            e.message)

                    if not myRun.muted and cleanup == 0:
                        myjob = job(
                            command="CATTLE_RUN_UPLOAD", arguments={
                                "PK": myParentRun.pk})
                        myjob.save()

                    logger.debug(
                        "Cattle run upload job saved (tells CATTLE about the start of this run).")

                    try:

                        hostname = socket.gethostname()
                        addr = socket.gethostbyname(hostname)
                        # print 'The address of ', hostname, 'is', addr
                        # this changes the cluster to match the loaded env file
                        ChangeEnvironment(
                            ipaddr=addr, full_path_name=ae2env, debug=False)
                        rpmcomponent = ""
                        if fldcrpm != "" and ".exe" in fldcrpm:
                            rpmcomponent = ' exe_url="' + fldcrpm.strip() + '"'
                        elif fldcrpm != "":
                            rpmcomponent = ' rpm_url="' + fldcrpm.strip() + '"'

                        if ".rpm" in fldctools:
                            rpmcomponent = rpmcomponent + ' archive_configs=true testrail=false timeout=2700 sim_url="' + \
                                fldctools.strip() + '"'  # for windows
                        elif fldctools != "":
                            rpmcomponent = rpmcomponent + ' tools_url="' + \
                                fldctools.strip() + '"'  # for linux

                        runstring = ae2python + ' ' + AE2Settings.install_directory + \
                            '/src/ae2.py ' + ae2suite + ' ' + ae2env + ' clean_log=true ' + rpmcomponent

                        # returncode = subprocess.call([runstring], shell=True)
                        results = run_ae2(
                            cmd=runstring,
                            myParentRun=myParentRun,
                            myAE2RUN=myRun,
                            logger=logger)

                        logger.debug("AE2 ran with the following command:")
                        logger.debug(runstring)
                        logger.debug(
                            "AE2 monitoring app returned the following:" + str(results["result"]))

                        if cleanup == 0 and "cow_multi_clean" not in myParentRun.suite_file:
                            mydebuglogurl = upload_log(
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run_debug.log",
                                hostname,
                                myParentRun.build_number)
                            mybasiclogurl = upload_log(
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run.log",
                                hostname,
                                myParentRun.build_number)
                            mystdiologurl = upload_log(
                                SITE_ROOT + "/logs/stdio.log", hostname, myParentRun.build_number)
                        else:
                            shutil.copyfile(
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run_debug.log",
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run_debug_cleanup_" +
                                str(cleanup) +
                                ".log")
                            mydebuglogurl = upload_log(
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run_debug_cleanup_" +
                                str(cleanup) +
                                ".log",
                                hostname,
                                myParentRun.build_number)
                            shutil.copyfile(
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run.log",
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run_cleanup_" +
                                str(cleanup) +
                                ".log")
                            mybasiclogurl = upload_log(
                                AE2Settings.install_directory +
                                "/src/logs/cow-ae-run_cleanup_" +
                                str(cleanup) +
                                ".log",
                                hostname,
                                myParentRun.build_number)
                            shutil.copyfile(
                                SITE_ROOT +
                                "/logs/stdio.log",
                                SITE_ROOT +
                                "/logs/stdio_cleanup_" +
                                str(cleanup) +
                                ".log")
                            mystdiologurl = upload_log(
                                SITE_ROOT +
                                "/logs/stdio_cleanup_" +
                                str(cleanup) +
                                ".log",
                                hostname,
                                myParentRun.build_number)

                        myParentRun.run_results = results["result"]
                        myParentRun.end_time = timezone.now()
                        myParentRun.log_file = mydebuglogurl
                        # perhaps in the future we could support other logs
                        mycluster = cluster_member.objects.all()
                        if mycluster.count() > 0 and myParentRun.operating_system == "Unset":
                            myParentRun.operating_system = mycluster[
                                0].operating_system
                        myParentRun.save()
                        if not myRun.muted and cleanup == 0 and "cow_multi_clean" not in myParentRun.suite_file:
                            myjob = job(
                                command="CATTLE_RUN_UPLOAD", arguments={
                                    "PK": myParentRun.pk})
                            myjob.save()

                        print "!!!!!!!!!!!!!!!!!!JUST ABOUT TO FILL AE2 RUN INFO!!!!!!!!!!!!!!!!!!!"
                        myae2run.attempted = True
                        myae2run.command_result = results["result"]
                        myae2run.command_message = {
                            "result": myParentRun.run_results,
                            "duration": int(
                                (myParentRun.end_time -
                                 myParentRun.start_time).seconds) +
                            int(
                                (myParentRun.end_time -
                                 myParentRun.start_time).days *
                                86400)}  # 86400 is the number of seconds in a day
                        myae2run.attempt_result = 0
                        myae2run.save()
                        print "!!!!!!!!!!!!!!!!!!DATA SAVED TO JOB HISTORY!!!!!!!!!!!!!!!!!!!!!!!!!"

                        myRun.running = False
                        if not results["result"]:
                            myRun.passed = False
                            myRun.needs_triage = True
                        myRun.save()
                        print "!!!!!!!!!!!!!!!!!!AE2RUN INFO SAVED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

                    except Exception as e:
                        logger.debug(
                            "AN ERROR OCCURED, ATTEMPTING TO PROTECT FROM FALSE RUNNING STATE")
                        logger.debug("ERROR MESSAGE: " + e.message)
                        myae2run.attempted = True
                        myae2run.attempt_result = 5
                        myae2run.save()
                        myRun.running = False
                        myRun.passed = False
                        myRun.save()
                        myParentRun.run_results = 0  # failed
                        myParentRun.end_time = timezone.now()
                        myParentRun.save()
                        if not myRun.muted and cleanup == 0 and "cow_multi_clean" not in myParentRun.suite_file:
                            myjob = job(
                                command="CATTLE_RUN_UPLOAD", arguments={
                                    "PK": myParentRun.pk})
                            myjob.save()

                        try:
                            if cleanup == 0 and "cow_multi_clean" not in myParentRun.suite_file:
                                mydebuglogurl = upload_log(
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run_debug.log",
                                    hostname,
                                    myParentRun.build_number)
                                mybasiclogurl = upload_log(
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run.log",
                                    hostname,
                                    myParentRun.build_number)
                                mystdiologurl = upload_log(
                                    SITE_ROOT + "/logs/stdio.log", hostname, myParentRun.build_number)
                            else:
                                shutil.copyfile(
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run_debug.log",
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run_debug_cleanup_" +
                                    str(cleanup) +
                                    ".log")
                                mydebuglogurl = upload_log(
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run_debug_cleanup_" +
                                    str(cleanup) +
                                    ".log",
                                    hostname,
                                    myParentRun.build_number)
                                shutil.copyfile(
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run.log",
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run_cleanup_" +
                                    str(cleanup) +
                                    ".log")
                                mybasiclogurl = upload_log(
                                    AE2Settings.install_directory +
                                    "/src/logs/cow-ae-run_cleanup_" +
                                    str(cleanup) +
                                    ".log",
                                    hostname,
                                    myParentRun.build_number)
                                shutil.copyfile(
                                    SITE_ROOT + "/logs/stdio.log",
                                    SITE_ROOT + "/logs/stdio_cleanup_" + str(cleanup) + ".log")
                                mystdiologurl = upload_log(
                                    SITE_ROOT +
                                    "/logs/stdio_cleanup_" +
                                    str(cleanup) +
                                    ".log",
                                    hostname,
                                    myParentRun.build_number)
                        except Exception as myerror:
                            raise e

                        raise e

                    return HttpResponse(
                        "!!!Finished running AE2 with runstring:\n" + runstring + "!!!")
            else:
                myae2run.attempted = True
                myae2run.attempt_result = 2
                myae2run.save()
                return HttpResponse(
                    "--ERROR: ATTEMPTED TO RUN AE2 AND ENCOUNTERED MISSING SUITE OR ENVIRONMENT INFORMATION IN ARGUMENTS!!--")
        else:
            myae2run.attempted = True
            myae2run.attempt_result = 2
            myae2run.save()
            return HttpResponse(
                "--ERROR:ATTEMPTED TO RUN AE2 WITH NO ARGUMENTS DEFINED!!!!--")
    else:
        return HttpResponse("--There are no AE2 jobs in the queue--")


def getnextbuildnumber():
    latestrun = Run.objects.all().order_by("-build_number")
    mynextbuild = 0
    if latestrun.exists():
        mynextbuild = latestrun[0].build_number + 1
    try:
        headers = {'content-type': 'application/json'}
        cattle_url = "http://cattle.yourdomain.com/builders/"
        data = json.dumps({'address': socket.gethostname()})
        r = requests.post(
            cattle_url,
            data,
            auth=(
                'root',
                'cleverpassword'),
            headers=headers)
        responsejson = json.loads(r.text)
        if "nextbuild" in responsejson:
            if responsejson["nextbuild"] > mynextbuild:
                return [responsejson["nextbuild"], responsejson]
            else:
                return [mynextbuild, responsejson]
        else:
            return [mynextbuild, responsejson]
    except:
        return [mynextbuild, "connectionproblem"]


def reattempt_failed(request):
    # This should reattempt or flush failed messages/jobs
    return HttpResponse(
        "<html><body>This should reattempt or flush failed messages/jobs.</body></html>")


def upload_log(logaddress, host, build_number, cleanup=""):
    try:
        url = 'http://cowtracks.yourdomain.com/upload/'

        files = {'logfile': open(str(logaddress), 'rb')}
        data = {"name": str(cleanup) + str(logaddress).split('/')
                [-1], "host": str(host), "build_number": int(build_number)}
        r = requests.post(url, files=files, data=data)

        if r.content != "" and "ERROR:" not in r.content:
            return r.content
        else:
            return "ERROR"
    except:
        return "ERROR"


@api_view(['GET', 'POST'])
def api_root(request):
    if request.method == 'POST':
        if request.data["action"] == "enqueue":
            if request.data["command"] == "ae2run":
                # check for running ae2runs
                # check for un-attempted ae2runs
                runInfo = AE2RUN(
                    suite="NA",
                    env="NA",
                    branch="NA",
                    commit="NA",
                    buildnumber=0,
                    running=False,
                    paused=False,
                    passed=True)  # This is in case of no runs existing
                ae2jobs = job.objects.filter(
                    command="ae2run").exclude(
                    attempted=True)
                if ae2jobs.count() > 0:
                    return Response(
                        {
                            "message": "ERROR: There is an existing unfinished AE2 run job on this system.",
                            "jobpk": ae2jobs[0].pk,
                            "returncode": 1})
                elif len(AE2RUN.objects.all()) > 0:
                    runInfo = AE2RUN.objects.latest('updated_at')
                    if runInfo.running:
                        return Response(
                            {
                                "message": "ERROR: There is an existing unfinished AE2 run job on this system.",
                                "jobpk": runInfo.pk,
                                "returncode": 1})

                myjob = job(
                    command="ae2run",
                    arguments=request.data["arguments"])
                myjob.save()

                return Response({"message": "Successfully queued ae2run with arguments: " + str(
                    request.data["arguments"]), "jobpk": myjob.pk, "returncode": 0})
            else:
                myjob = job(
                    command=request.data["command"],
                    arguments=request.data["arguments"])
                myjob.save()

                return Response({"message": "Successfully queued " +
                                 str(request.data["command"]) +
                                 " with arguments: " +
                                 str(request.data["arguments"]), "jobpk": myjob.pk, "returncode": 0})
        elif request.data["action"] == "check":
            myjob = job.objects.all().filter(pk=request.data["jobpk"])
            if myjob.count() > 0:
                myjob = myjob[0]
                return Response(
                    {
                        "message": "Job was found status as follows",
                        "job_status": myjob.attempt_result,
                        "command_return": myjob.command_result})
            else:
                return Response({"message": "No job found with PK " +
                                 str(request.data["jobpk"]), "job_status": -
                                 1, "command_return": -
                                 1})

    return Response(
        {"message": "No command received! Please send a command with a minimum of action, and either command/arguments pair or a jobpk"})
