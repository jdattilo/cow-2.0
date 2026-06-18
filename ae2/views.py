from django.shortcuts import render
from django.shortcuts import loader, render
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from time import sleep
from svn_code import pullae2
from models import AE2INSTALL
from models import AE2RUN
from models import suite, env
from runs.models import Run
import os.path
import subprocess
from enqueued.models import job
import functions
import socket
import shutil
import re
import os
import signal
from activities.views import logActivity
from ae2.functions import ChangeEnvironment
from enqueued.views import upload_log
from django.utils import timezone

SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def changedirectory(request):
    ae2directory = request.GET.get('ae2directory', '')

    logActivity(
        request=request,
        action="Changed/refreshed directory of AE2 install",
        arguments={
            "ae2directory": ae2directory})

    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch="UNKNOWN",
            revision="UNKNOWN",
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]
    if ae2directory != '':
        AE2Settings.install_directory = ae2directory

    if SITE_ROOT in AE2Settings.install_directory:
        return HttpResponse(
            "<html><body>ERROR CANNOT PUT AE2 INTO COW DIRECTORY!<br>Tried to load ae2 into:" +
            AE2Settings.install_directory +
            "<br>Cow root is:" +
            SITE_ROOT +
            "</body></html>")
    elif ae2directory == '':
        return HttpResponse(
            "<html><body>ERROR: No ae2directory get variable present.</body></html>")
    else:
        AE2Settings.save()

        if populate_files(ae2directory):
            return HttpResponse(
                "<html><head><script>parent.location.reload();</script></head></html>")

    return HttpResponse(
        "<html><head><script></script></head><body>Failed to populate env and suite files fully. Check populate_files function in ae2.views</body></html>")


def populate_files(ae2directory):

    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch="UNKNOWN",
            revision="UNKNOWN",
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]
    if ae2directory != '':
        AE2Settings.install_directory = ae2directory

    AE2Settings.save()
    # note that we do not pull ae2 here because this is a directory change only
    hostname = socket.gethostname()
    addr = socket.gethostbyname(hostname)
    # print 'The address of ', hostname, 'is', addr

    env.objects.all().delete()
    env_dict = functions.DiscoverAllEnvironments(
        dirname=SITE_ROOT + "/static/env_files/", debug=True)
    if not env_dict:
        env_dict = functions.DiscoverOwnedEnvironments(
            ipaddr=addr, dirname=ae2directory + "/src/env_files/", debug=True)
    else:
        svn_envs = functions.DiscoverOwnedEnvironments(
            ipaddr=addr, dirname=ae2directory + "/src/env_files/", debug=True)
        if svn_envs:
            env_dict = env_dict + svn_envs

    if not env_dict:
        print 'DiscoverOwnedEnvironments with owner %s failed' % addr
    else:
        for foundenvironment in env_dict:
            if ae2directory in foundenvironment:
                myenv = env(
                    location=foundenvironment,
                    name=foundenvironment.replace(
                        ae2directory +
                        "/src/env_files/",
                        ""))
            elif SITE_ROOT in foundenvironment:
                myenv = env(
                    location=foundenvironment,
                    name=foundenvironment.replace(
                        SITE_ROOT +
                        "/static/env_files/",
                        "local - "))
            else:
                myenv = env(location=foundenvironment, name=foundenvironment)
            myenv.save()

    suite.objects.all().delete()

    suite_dict = functions.DiscoverSuiteFiles(
        dirname=SITE_ROOT + "/static/suite_files/", debug=False)
    if suite_dict:
        suite_dict = suite_dict + \
            functions.DiscoverSuiteFiles(dirname=ae2directory + "/src/suite_files/", debug=False)
    else:
        suite_dict = functions.DiscoverSuiteFiles(
            dirname=ae2directory + "/src/suite_files/", debug=False)

    if not suite_dict:
        print 'DiscoverSuiteFiles failed \n'
    else:
        for foundsuite in suite_dict:
            if ae2directory in foundsuite:
                mysuite = suite(
                    location=foundsuite,
                    name=foundsuite.replace(
                        ae2directory +
                        "/src/suite_files/",
                        ""))
            elif SITE_ROOT in foundsuite:
                mysuite = suite(
                    location=foundsuite,
                    name=foundsuite.replace(
                        SITE_ROOT +
                        "/static/suite_files/",
                        "local - "))
            else:
                mysuite = suite(location=foundsuite, name=foundsuite)
            mysuite.save()

    if os.path.exists(AE2Settings.install_directory + "/src/ae2.py"):
        AE2Settings.present = True
        AE2Settings.save()
    else:
        AE2Settings.present = False
        AE2Settings.save()
    return True


def pull(request):
    ae2directory = request.GET.get('ae2directory', '')
    ae2branch = request.GET.get('ae2branch', 'nothing')
    ae2revision = request.GET.get('ae2revision', 'nothing')

    logActivity(
        request=request,
        action="Pulling fresh copy of Automation Express",
        arguments={
            "ae2directory": ae2directory,
            "ae2branch": ae2branch,
            "ae2revision": ae2revision})

    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch=ae2branch,
            revision=ae2revision,
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]
    if ae2directory != '':
        AE2Settings.install_directory = ae2directory
    if ae2branch != '':
        AE2Settings.branch = ae2branch
    if ae2revision != '':
        AE2Settings.revision = ae2revision

    if SITE_ROOT in AE2Settings.install_directory:
        return HttpResponse(
            "<html><body>ERROR CANNOT PUT AE2 INTO COW DIRECTORY!<br>Tried to load ae2 into:" +
            AE2Settings.install_directory +
            "<br>Cow root is:" +
            SITE_ROOT +
            "</body></html>")
    elif ae2directory == '':
        return HttpResponse(
            "<html><body>ERROR: No ae2directory get variable present.</body></html>")
    else:
        AE2Settings.save()

        pullae2(ae2directory, ae2branch, ae2revision)

        if populate_files(ae2directory):
            return HttpResponse(
                "<html><head><script>parent.location.reload();</script></head></html>")
    return HttpResponse(
        "<html><head><script></script></head><body>Failed to populate env and suite files fully. Check populate_files function in ae2.views</body></html>")


def run(request):
    ae2python = "/opt/python2.7/bin/python2.7"
    ae2suite = request.GET.get('ae2suite', '')
    ae2env = request.GET.get('ae2env', '')
    fldcrpm = request.GET.get('fldcrpm', '')
    fldctools = request.GET.get('fldctools', '')
    fldcbranch = request.GET.get('fldcbranch', '')
    fldccommit = request.GET.get('fldccommit', 0)
    fldcmuted = request.GET.get('fldcmuted', 0)
    cleanup = request.GET.get('cleanup', 0)

    logActivity(
        request=request,
        action="Queued a manual test run.",
        arguments={
            "suite": ae2suite,
            "env": ae2env,
            "rpm": fldcrpm,
            "tools": fldctools,
            "branch": fldcbranch,
            "commit": fldccommit,
            "muted": fldcmuted,
            "cleanup": cleanup})

    if fldcmuted == "false":
        fldcmuted = 0
    AE2Settings = AE2INSTALL.objects.all()[0]
    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('created_at')

    ae2jobs = job.objects.filter(command="ae2run").exclude(
        attempted=True)  # disables queuing of multiple jobs

    if runInfo.running or ae2jobs.count() > 0:
        return HttpResponse(
            "<html><head><script></script></head><body>Your request cannot be completed because there is already a test running.</body></html>")
    else:
        myjob = job(
            command="ae2run",
            arguments={
                "suite": ae2suite,
                "env": ae2env,
                "rpm": fldcrpm,
                "tools": fldctools,
                "branch": fldcbranch,
                "commit": fldccommit,
                "muted": fldcmuted,
                "cleanup": cleanup})
        myjob.save()
        sleep(5)
        # /opt/python2.7/bin/python2.7 /root/ae2/src/ae2.py /root/ae2/src/suite_files/examples/hello_suite.cfg /root/ae2/src/env_files/users/jdattilo/env_minimal_qavm53_54.cfg clean_log=true subunit=true
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your run has been added to the queue</body></html>")


def performtriage(request):
    bug = request.GET.get('bug', '')
    comment = request.GET.get('comment', '')
    results = request.GET.get('results', 0)
    start_buildslave = request.GET.get('start_buildslave', 1)
    if start_buildslave == "false":
        start_buildslave = 0
    else:
        start_buildslave = 1

    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.order_by('-pk')[0]
        runInfo = AE2RUN.objects.filter(
            buildnumber=runInfo.buildnumber).order_by('pk')
        runInfo = runInfo[0]
    else:
        return HttpResponse(
            "<html><head><script></script></head><body>No AE2 runs present to perform triage on.</body></html>")

    if runInfo.running:
        return HttpResponse(
            "<html><head><script></script></head><body>Your request cannot be completed because the test is still running. Please stop the run before proceeding.</body></html>")
    elif runInfo.needs_triage:
        myRun = Run.objects.all().filter(build_number=runInfo.buildnumber)[0]
        myRun.comment = comment
        myRun.caused_bug = bug
        myRun.run_results = int(results)
        if str(results) == "1" or str(results) == "2":
            runInfo.passed = True
        runInfo.needs_triage = False
        myRun.save()
        runInfo.save()
        if not runInfo.muted and (
                myRun.comment != "" or myRun.caused_bug != "" or myRun.run_results != 0):
            myjob = job(
                command="CATTLE_RUN_UPLOAD",
                arguments={
                    "PK": myRun.pk})
            myjob.save()

        if start_buildslave:
            # #########CHECK FOR BUILDSLAVE#############
            if os.path.isfile("/usr/bin/buildslave"):
                os.system(
                    "/usr/bin/buildslave start /root/buildslave/buildslave")

        logActivity(
            request=request,
            action="Submitted triage completion",
            arguments={
                "bug": bug,
                "comment": comment,
                "results": results,
                "start_buildslave": start_buildslave,
                "Run_PK": myRun.pk})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your run has been triaged, and the results value was as follows: " +
            str(
                myRun.run_results) +
            "</body></html>")
    else:
        return HttpResponse(
            "<html><head><script></script></head><body>Triage is not needed at this time.</body></html>")


def startbuildslave(request):
    # #########CHECK FOR TRIAGE LOCK & Mode ###########
    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch=ae2branch,
            revision=ae2revision,
            autopull=False,
            present=False)
        initialAE2.save()
    AE2Settings = AE2INSTALL.objects.all()[0]

    if AE2Settings.cow_mode != 0:
        return HttpResponse(
            "<html><head><script></script></head><body>ERROR: This cow is not in its stall, please enable Automation Mode from the AE2/Automation Management Tab.</body></html>")

    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        branch="NA",
        commit="NA",
        buildnumber=0,
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.order_by('-pk')[0]
        runInfo = AE2RUN.objects.filter(
            buildnumber=runInfo.buildnumber).order_by('pk')
        runInfo = runInfo[0]
    if runInfo.needs_triage or runInfo.running:
        return HttpResponse(
            "<html><head><script></script></head><body>ERROR: This system is triage locked, or in a running state. Please perform triage before attempting to restart your buildslave.</body></html>")

    # #########CHECK FOR BUILDSLAVE#############
    if os.path.isfile("/usr/bin/buildslave"):
        os.system("/usr/bin/buildslave start /root/buildslave/buildslave")
        logActivity(
            request=request,
            action="Buildslave has been started.",
            arguments={})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Buildslave has been started.</body></html>")
    else:
        logActivity(
            request=request,
            action="Buildslave start attempted, but buildslave is not available on this machine.",
            arguments={})
        return HttpResponse(
            "<html><head><script></script></head><body>ERROR: NO BUILDSLAVE INSTALLED ON THIS SYSTEM!</body></html>")


def stopbuildslave(request):
    # #########CHECK FOR BUILDSLAVE#############
    if os.path.isfile("/usr/bin/buildslave"):
        os.system("/usr/bin/buildslave stop /root/buildslave/buildslave")
        logActivity(
            request=request,
            action="Buildslave has been sent a stop signal",
            arguments={})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Buildslave has been sent a stop signal.</body></html>")
    else:
        logActivity(
            request=request,
            action="Attempted to stop Buildslave, but it was not present.",
            arguments={})
        return HttpResponse(
            "<html><head><script></script></head><body>ERROR: NO BUILDSLAVE INSTALLED ON THIS SYSTEM!</body></html>")


def newsuite(request):
    name = request.GET.get('name', '').replace(" ", "_")
    if ".cfg" not in name:
        name = name + ".cfg"
    if name is not None and name != '':
        open(SITE_ROOT + "/static/suite_files/" + str(name), 'w+')
        mysuite = suite(
            location=SITE_ROOT +
            "/static/suite_files/" +
            str(name),
            name="local - " +
            name)
        mysuite.save()  # This should add the suite to the suite list
        logActivity(
            request=request,
            action="Created new suite file.",
            arguments={
                "name": name})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your suite file has been created.</body></html>")
    else:
        logActivity(
            request=request,
            action="Attempted to create a suite file with an invalid name.",
            arguments={
                "name": name})
        return HttpResponse(
            "<html><head><script></script></head><body>" +
            str(name) +
            " is not a valid file name.</body></html>")


def newenv(request):
    name = request.GET.get('name', '').replace(" ", "_")
    if ".cfg" not in name:
        name = name + ".cfg"
    if name is not None and name != '':
        open(SITE_ROOT + "/static/env_files/" + str(name), 'w+')
        myenv = env(
            location=SITE_ROOT +
            "/static/env_files/" +
            str(name),
            name="local - " +
            name)
        myenv.save()  # This should add the suite to the suite list
        logActivity(
            request=request,
            action="Created new Env file.",
            arguments={
                "name": name})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your env file has been created.</body></html>")
    else:
        logActivity(
            request=request,
            action="Attempted to create an env file with an invalid name.",
            arguments={
                "name": name})
        return HttpResponse(
            "<html><head><script></script></head><body>" +
            str(name) +
            " is not a valid file name.</body></html>")


def copysuite(request):
    original = request.GET.get('original', '')
    name = request.GET.get('name', '').replace(" ", "_")
    if ".cfg" not in name:
        name = name + ".cfg"
    if name is not None and name != '' and original != '' and original is not None:
        shutil.copy2(original, SITE_ROOT + "/static/suite_files/" + str(name))
        mysuite = suite(
            location=SITE_ROOT +
            "/static/suite_files/" +
            str(name),
            name="local - " +
            name)
        mysuite.save()  # This should add the suite to the suite list
        logActivity(
            request=request,
            action="Successfully copied a suite file.",
            arguments={
                "original": original,
                "name": name})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your suite file has been created.</body></html>")
    else:
        logActivity(
            request=request,
            action="Attempted to copy a suite file and provided an invalid name.",
            arguments={
                "original": original,
                "name": name})

        return HttpResponse(
            "<html><head><script></script></head><body>" +
            str(name) +
            " is not a valid file name. <br> or " +
            str(original) +
            " is not a valid original.</body></html>")


def copyenv(request):
    original = request.GET.get('original', '')
    name = request.GET.get('name', '').replace(" ", "_")
    if ".cfg" not in name:
        name = name + ".cfg"
    if name is not None and name != '' and original != '' and original is not None:
        shutil.copy2(original, SITE_ROOT + "/static/env_files/" + str(name))
        myenv = env(
            location=SITE_ROOT +
            "/static/env_files/" +
            str(name),
            name="local - " +
            name)
        myenv.save()  # This should add the suite to the suite list
        logActivity(
            request=request,
            action="Successfully copied an ENV file.",
            arguments={
                "original": original,
                "name": name})
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your env file has been created.</body></html>")
    else:
        logActivity(
            request=request,
            action="Attempted to copy an ENV file and provided an invalid name.",
            arguments={
                "original": original,
                "name": name})
        return HttpResponse(
            "<html><head><script></script></head><body>" +
            str(name) +
            " is not a valid file name. <br> or " +
            str(original) +
            " is not a valid original.</body></html>")


def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)


def editfile(request):
    location = request.GET.get('location', '')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        # now created before und stuff
        # check whether it's valid:
        output = request.POST.get('output', '')
        with open(location, 'w+') as f:
            f.write(output)
        logActivity(
            request=request,
            action="Edited a file.",
            arguments={
                "location": location})
        return HttpResponseRedirect("/")

    with open(location, 'r') as f:
        read_data = f.read()

        template = loader.get_template('ae2/editfileyaml.html')
        context = RequestContext(request, {
            "read_data": read_data,
        })
        return HttpResponse(template.render(context))
    return HttpResponse(
        "<html><head><script></script></head><body> Error reading " +
        str(location) +
        "</body></html>")


def safesleep(delay):
    try:
        sleep(delay)
        return True
    except:
        logger.warning("Failed to sleep, moving on...")
        return False


def halt_ae2(request):

    logActivity(
        request=request,
        action="Attempted to terminate the currently running test.",
        arguments={})

    # This should call clean_cluster
    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        branch="NA",
        commit="NA",
        buildnumber=0,
        running=False,
        paused=False,
        passed=True)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('created_at')

        myParentRun = Run

        if runInfo.running:
            process_alive = True
            try:
                os.kill(runInfo.pid, signal.SIGINT)
            except OSError:
                process_alive = False
                # already dead, but shows as running

            if process_alive:
                for num in range(0, 40):
                    safesleep(30)
                    try:
                        os.kill(runInfo.pid, 0)  # check if process is alive
                    except OSError:
                        process_alive = False
                        break
                if process_alive:
                    try:
                        # hard kill of the process
                        os.kill(runInfo.pid, signal.SIGKILL)
                    except OSError:
                        process_alive = False

            AE2Settings = AE2INSTALL.objects.all()[0]
            myParentRun = Run.objects.all().filter(
                build_number=runInfo.buildnumber)[0]
            hostname = socket.gethostname()

            if runInfo.cleanup == 0 and "cow_multi_clean" not in myParentRun.suite_file:
                upload_log(
                    AE2Settings.install_directory +
                    "/src/logs/cow-ae-run_debug.log",
                    hostname,
                    myParentRun.build_number)
                upload_log(
                    AE2Settings.install_directory +
                    "/src/logs/cow-ae-run.log",
                    hostname,
                    myParentRun.build_number)
                upload_log(
                    SITE_ROOT +
                    "/logs/stdio.log",
                    hostname,
                    myParentRun.build_number)
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

            # clear the ae2run jobs
            ae2jobs = job.objects.filter(
                command="ae2run").exclude(
                attempted=True)
            if ae2jobs.count() > 0:
                myae2run = ae2jobs[0]
                myae2run.attempted = True
                myae2run.needs_triage = True
                myae2run.save()

            runInfo.running = False
            runInfo.passed = False
            runInfo.needs_triage = True
            runInfo.save()
            myParentRun.run_results = 0  # failed
            myParentRun.end_time = timezone.now()
            myParentRun.save()
            if not runInfo.muted and runInfo.cleanup == 0:
                myjob = job(
                    command="CATTLE_RUN_UPLOAD", arguments={
                        "PK": myParentRun.pk})
                myjob.save()

            # fail_all_running_runs()
            logActivity(
                request=request,
                action="AE PID " +
                str(
                    runInfo.pid) +
                " successfully killed and cleaned up.",
                arguments={
                    "myParentRun": myParentRun})
            return HttpResponse(
                "<html><head><script>parent.location.reload();</script></head><body>PID " + str(
                    runInfo.pid) + " successfully killed and cleaned up.</body></html>")

    logActivity(
        request=request,
        action="AE Termination error: There is no currently running AE process",
        arguments={})
    return HttpResponse(
        "<html><head><script></script></head><body>ERROR: There is no currently running AE2 process</body></html>")


def change_env(request):

    ae2env = request.GET.get('ae2env', '')
    logActivity(
        request=request,
        action="Changed currently assigned env.",
        arguments={
            "ae2env": ae2env})

    runInfo = AE2RUN(
        suite="NA",
        env="NA",
        running=False,
        paused=False,
        passed=True,
        commit=-
        1)  # This is in case of no runs existing
    if len(AE2RUN.objects.all()) > 0:
        runInfo = AE2RUN.objects.latest('created_at')

    runInfo.pk = None
    runInfo.env = ae2env

    ae2jobs = job.objects.filter(command="ae2run").exclude(attempted=True)
    if runInfo.running or ae2jobs.count() > 0 or ae2env == '':
        return HttpResponse(
            "<html><head><script></script></head><body>Your request cannot be completed because there is already a test running, or ae2env argument is not set.</body></html>")
    else:
        hostname = socket.gethostname()
        addr = socket.gethostbyname(hostname)
        # print 'The address of ', hostname, 'is', addr
        # this changes the cluster to match the loaded env file
        ChangeEnvironment(ipaddr=addr, full_path_name=ae2env, debug=False)

        runInfo.save()  # This should create a new run with the current env
        return HttpResponse(
            "<html><head><script>parent.location.reload();</script></head><body>Your env has been changed</body></html>")


def change_cow_mode(request):

    cowmode = request.GET.get('cowmode', 0)

    logActivity(
        request=request,
        action="Changed cow mode of system.",
        arguments={
            "cowmode": cowmode})

    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch=ae2branch,
            revision=ae2revision,
            autopull=False,
            present=False)
        initialAE2.save()
    AE2Settings = AE2INSTALL.objects.all()[0]

    AE2Settings.cow_mode = cowmode
    AE2Settings.mode_username = request.user.username
    AE2Settings.mode_dtg = timezone.now()

    AE2Settings.save()
    if cowmode == 1 or cowmode == 2:
        stopbuildslave(request)
    else:
        startbuildslave(request)

    return HttpResponse(
        "<html><head><script>parent.location.reload();</script></head><body>Cow mode successfully changed. Please close modal view or refresh your dashboard.</body></html>")


def change_automation(request):

    ae2env = request.GET.get('ae2env', 'Unset')
    ae2suite = request.GET.get('ae2suite', 'Unset')
    name = request.GET.get('name', 'Unset')
    description = request.GET.get('description', 'Unset')
    myos = request.GET.get('os', 'Unset')
    scheduler = request.GET.get('scheduler', 'Unset')
    compiler = request.GET.get('compiler', 'Unset')

    logActivity(
        request=request,
        action="Permanently changed default automation settings for this system.",
        arguments={
            "ae2env": ae2env,
            "ae2suite": ae2suite,
            "Tester Name": name,
            "Tester Description": description,
            "OS": myos,
            "Scheduler": scheduler,
            "compiler": compiler})

    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch=ae2branch,
            revision=ae2revision,
            autopull=False,
            present=False)
        initialAE2.save()
    AE2Settings = AE2INSTALL.objects.all()[0]

    AE2Settings.automated_env = ae2env
    AE2Settings.automated_suite = ae2suite
    AE2Settings.automated_name = name
    AE2Settings.automated_description = description
    AE2Settings.automated_os = myos
    AE2Settings.automated_scheduler = scheduler
    AE2Settings.automated_compiler = compiler
    AE2Settings.save()

    return HttpResponse(
        "<html><head><script>parent.location.reload();</script></head><body>Automation setting permanently changed on this host. Please close modal view or refresh your dashboard.</body></html>")
