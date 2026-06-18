from django.core.management.base import NoArgsCommand
from crontab import CronTab
import sys
import os.path
from django.conf import settings
SITE_ROOT = settings.BASE_DIR


class Command(NoArgsCommand):
    help = "This runs the installation script for COW, and sets up crontab entries based on how this session was called."

    def handle_noargs(self, **options):
        self.installCow()
        self.installQueuemaster()

    def installCow(NoArgsCommand):
        print "Running from executable " + sys.executable + " with the project root of " + SITE_ROOT + "."
        cmd = 'manage.py runserver 0.0.0.0:80'
        loggingcmd = ' > ' + SITE_ROOT + '/logs/server.log 2>&1'
        tab = CronTab(user="root")

        cron_job = tab.find_command(cmd)
        if len(list(cron_job)) == 1:
            print "Crontab entry for a COW or similar app is present."
            print "Checking for exact match."
            cron_job = tab.find_command(
                sys.executable + " " + SITE_ROOT + "/" + cmd + loggingcmd)
            if len(list(cron_job)) == 1:
                print "An entry for this instance of cow is already present in Crontab, and no changes are needed."
                return

        # At this point there are either duplicates, a single bad entry, or no
        # COW entries at all.

        cron_job = tab.find_command(cmd)
        tab.remove_all(command=cmd)

        print "Writing new Crontab entry for COW, this means there was none before, or there was a problem with the entry(s) that were found."
        job = tab.new(
            command=sys.executable +
            " " +
            SITE_ROOT +
            "/" +
            cmd +
            loggingcmd)
        job.every_reboot()
        job.enable()
        tab.write()
        print "Crontab entry successfully created."
        return

    def installQueuemaster(NoArgsCommand):
        print "Running from executable " + sys.executable + " with the project root of " + SITE_ROOT + "."
        cmd = 'manage.py queuemaster'
        loggingcmd = ' > ' + SITE_ROOT + '/logs/queuemaster.log 2>&1'
        tab = CronTab(user="root")

        cron_job = tab.find_command(cmd)
        if len(list(cron_job)) == 1:
            print "Crontab entry for a Queuemaster is present."
            print "Checking for exact match."
            cron_job = tab.find_command(
                sys.executable + " " + SITE_ROOT + "/" + cmd + loggingcmd)
            if len(list(cron_job)) == 1:
                print "An entry for this instance of queuemaster is already present in Crontab, and no changes are needed."
                return

        # At this point there are either duplicates, a single bad entry, or no
        # COW entries at all.

        cron_job = tab.find_command(cmd)
        tab.remove_all(command=cmd)

        print "Writing new Crontab entry for queuemaster, this means there was none before, or there was a problem with the entry(s) that were found."
        job = tab.new(
            command=sys.executable +
            " " +
            SITE_ROOT +
            "/" +
            cmd +
            loggingcmd)
        job.every_reboot()
        job.enable()
        tab.write()
        print "Crontab entry successfully created."
        return
