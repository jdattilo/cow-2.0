from django.http import HttpResponse
from cluster.models import cluster_member, cluster_health
import socket
import os
import subprocess
from ae2.models import AE2INSTALL, AE2RUN
from time import sleep
from cluster_collect import fldc_collect

SITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def check(request):
    if AE2INSTALL.objects.count() == 0:
        initialAE2 = AE2INSTALL(
            install_directory=ae2directory,
            branch="UNKNOWN",
            revision="UNKNOWN",
            autopull=False,
            present=False)
        initialAE2.save()

    AE2Settings = AE2INSTALL.objects.all()[0]
    AE2Settings.save()  # this should updated a date time group
    # pull/create cluster health record
    if cluster_health.objects.count() == 0:
        initialHealth = cluster_health()
        initialHealth.save()

    ClusterHealthObject = cluster_health.objects.all()[0]

    # Check cluster members
    if cluster_member.objects.count() > 0:
        ClusterHealthObject.empty = False  # There are cluster members
        ClusterHealthObject.ssh = True  # We use working until proven broken logic
        # It is important not to save before finishing checks because of this
        ClusterHealthObject.rpc = True
        ClusterHealthObject.ping = True
        for sut in cluster_member.objects.all():
            if check_ping(sut.hostname) == 0:
                sut.ping = True
                sut.save()
                if check_port(sut.hostname, 22):
                    sut.ssh = True
                    sut.operating_system = "LINUX"
                    sut.save()
                else:
                    ClusterHealthObject.ssh = False  # annotate ssh failure
                    sut.ssh = False
                    sut.save()
                if check_port(sut.hostname, 135):
                    sut.rpc = True
                    sut.operating_system = "win2k12"
                    sut.save()
                else:
                    ClusterHealthObject.rpc = False  # annotate rpc failure
                    sut.rpc = False
                    sut.save()
            else:
                ClusterHealthObject.ping = False  # annotate ping failure
                sut.ping = False
                sut.ssh = False
                sut.rpc = False
                sut.save()
    else:
        ClusterHealthObject.empty = True  # annotate fact that there are no cluster_members

    ClusterHealthObject.save()  # save overall cluster health

    return HttpResponse("--" +
                        str(cluster_member.objects.all().count()) +
                        " Cluster members checked.--")


def check_ping(hostname):
    response = os.system("ping -c 1 -w 1 " + hostname)
    return response


def check_port(hostname, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((hostname, port))
        print "Port 22 reachable"
        return True
    except socket.error as e:
        print "Error on connect: %s" % e
        return False
    s.close()


def checkfldc(request):
    # This should check the status of FLDC
    return HttpResponse("--unimplemented FLDC checks here--")


def clean_cluster(request):
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
        runInfo = AE2RUN.objects.latest('updated_at')
    if runInfo.running:
        return HttpResponse(
            "--Your request cannot be completed because there is a test running.--")

    cmd = SITE_ROOT + "/cluster/cluster_clean.py -f " + \
        runInfo.env + " -t force_clean -d"

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)

    process.wait()

    stdout = process.stdout.read().replace("\n", "<br>")
    stderr = process.stderr.read().replace("\n", "<br>")

    if stderr != "" and stderr is not None and stderr != "<br>":
        return HttpResponse(
            "--clean cluster FAILED!--<br>Command: " +
            cmd +
            "<br>Output:" +
            str(stdout) +
            "<br>Errors:" +
            str(stderr))
    # no fatal errors encountered, this will work better if we poll for a return code,
    # and give more easy to read stats at the end of the clean script itself.
    sleep(5)
    return HttpResponse(
        "<html><head><script>parent.location.reload();</script></head><body>Clean process successfully queued. If this page does not refresh automatically please do so in 5 seconds.</body></html>")


def collect_cluster(request):
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
        runInfo = AE2RUN.objects.latest('updated_at')

    fldc_collect(runInfo.env, runInfo.buildnumber, bug=None)

    return HttpResponse(
        "<html><head><script>parent.location.reload();</script></head></html>")
