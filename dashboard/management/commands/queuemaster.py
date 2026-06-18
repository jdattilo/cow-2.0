from django.core.management.base import NoArgsCommand
from crontab import CronTab
import sys
import os.path
from django.conf import settings

import urllib2
import threading
from time import sleep
import datetime
import logging

keepalive = True
cowaddress = "http://localhost"

# logging.basicConfig(level=logging.INFO,
# format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s:
# %(message)s', datefmt="%Y-%m-%d %H:%M:%S")


logger = logging.getLogger('queuemaster_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S")
ch_stream = logging.StreamHandler()
ch_stream.setFormatter(formatter)
ch_stream.setLevel(logging.DEBUG)
logger.addHandler(ch_stream)


def safesleep(delay):
    try:
        sleep(delay)
        return True
    except:
        logger.warning("Failed to sleep, moving on...")
        return False


def safeurlopen(address):
    try:
        return urllib2.urlopen(address).read()
    except:
        return "Error: " + address + " un-reachable."


def startBuildSlave():
    logger.info("Waiting 1 minute for startup.")
    safesleep(60)
    logger.info("Attempting to start a buildslave.")
    pagefeedback = safeurlopen(cowaddress + "/ae2/startbuildslave")
    if 'error' in pagefeedback.lower():
        logger.error("Couldn't start the buildslave:" + pagefeedback)
    else:
        logger.info("Successfully started buildslave:" + pagefeedback)


def clusterChecks():
    while keepalive:
        safesleep(30)
        logger.info("Checking cluster")
        pagefeedback = safeurlopen(cowaddress + "/cluster/check")
        if 'error' in pagefeedback.lower():
            logger.error(
                "Finished cluster check, got the following back:" +
                pagefeedback)
        else:
            logger.info(
                "Finished cluster check, got the following back:" +
                pagefeedback)
    logger.error("Cluster checks stopping.")


def systemChecks():
    while keepalive:
        safesleep(60)
        logger.info("Checking system status")
        pagefeedback = safeurlopen(cowaddress + "/system/check")
        if 'error' in pagefeedback.lower():
            logger.error(
                "Finished system check, got the following back:" +
                pagefeedback)
        else:
            logger.info(
                "Finished system check, got the following back:" +
                pagefeedback)

    logger.error("System checks stopping.")


def fldcChecks():
    while keepalive:
        safesleep(120)
        logger.info("Checking FLDC status")
        pagefeedback = safeurlopen(cowaddress + "/cluster/checkfldc")
        if 'error' in pagefeedback.lower():
            logger.error(
                "Finished FLDC check, got the following back:" +
                pagefeedback)
        else:
            logger.info(
                "Finished FLDC check, got the following back:" +
                pagefeedback)
    logger.error("FLDC checks stopping.")


def jobmonitor():
    while keepalive:
        safesleep(15)
        logger.info("Checking job queue")
        pagefeedback = safeurlopen(cowaddress + "/enqueued/runnext")
        if 'error' in pagefeedback.lower():
            logger.error(
                "Finished job check, got the following back:" +
                pagefeedback)
        else:
            logger.info(
                "Finished job check, got the following back:" +
                pagefeedback)

    logger.error("jobmonitor worker stopping.")


def ae2runner():
    while keepalive:
        safesleep(5)
        logger.info("Checking for AE2 Runs")
        pagefeedback = safeurlopen(cowaddress + "/enqueued/runae2")
        if 'error' in pagefeedback.lower():
            logger.error(
                "Finished ae2 job check, got the following back:" +
                pagefeedback)
        else:
            logger.info(
                "Finished ae2 job check, got the following back:" +
                pagefeedback)
    logger.error("AE2 worker stopping.")


class Command(NoArgsCommand):
    help = "This runs the Queuemaster thread manager that makes sure everything is monitored."

    def handle_noargs(self, **options):
        global keepalive
        startBuildSlave()
        logging.info("Starting all threads.")
        clusterchecker = threading.Thread(
            target=clusterChecks, args=(), kwargs={})
        clusterchecker.start()  # will run "clusterChecks()"

        systemchecker = threading.Thread(
            target=systemChecks, args=(), kwargs={})
        systemchecker.start()  # will run "systemChecks()"

        fldcchecker = threading.Thread(target=fldcChecks, args=(), kwargs={})
        fldcchecker.start()  # will run "fldcChecks()"

        ae2worker = threading.Thread(target=ae2runner, args=(), kwargs={})
        ae2worker.start()  # will run "ae2runner()"

        worker1 = threading.Thread(target=jobmonitor, args=(), kwargs={})
        worker1.start()  # will run "jobmonitor()"

        safesleep(7.5)

        worker2 = threading.Thread(target=jobmonitor, args=(), kwargs={})
        worker2.start()  # will run "jobmonitor()"

        while True:
            if clusterchecker.is_alive:
                logger.info("#Cluster checker is alive")
            else:
                logger.error("->Cluster checker died, restarting it")
                clusterchecker.start()

            if systemchecker.is_alive:
                logger.info("#System checker is alive")
            else:
                logger.error("->System checker died, restarting it")
                systemchecker.start()

            if fldcchecker.is_alive:
                logger.info("#FLDC checker is alive")
            else:
                logger.error("->FLDC checker died, restarting it")
                fldcchecker.start()

            if worker1.is_alive:
                logger.info("#worker1 is alive")
            else:
                logger.error("->worker1 died, restarting it")
                worker1.start()

            if worker2.is_alive:
                logger.info("#worker1 is alive")
            else:
                logger.error("->worker1 died, restarting it")
                worker2.start()

            if ae2worker.is_alive:
                logger.info("#ae2worker is alive")
            else:
                logger.error("->ae2worker died, restarting it")
                ae2worker.start()

            sleep(15)

        logger.critical("!Setting keepalive=False!")
        keepalive = False

        logger.critical("!Joining all threads!")

        ae2worker.join()
        clusterchecker.join()
        systemchecker.join()
        fldcchecker.join()
        worker1.join()
        worker2.join()

        logger.critical(
            "!!All threads successfully joined, threadmaster now exiting.!!")

        return
