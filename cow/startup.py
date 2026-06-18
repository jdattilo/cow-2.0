from django.conf import settings
from crontab import CronTab
import sys
import os.path
SITE_ROOT = settings.BASE_DIR


def check_and_update_crontab():
    print "Running from executable " + sys.executable + " with the project root of " + SITE_ROOT + "."

    cmd = 'manage.py runserver 0.0.0.0:80'
    tab = CronTab(user="root")

    cron_job = tab.find_command(cmd)
    if len(list(cron_job)) == 1:
        print "Crontab entry for a COW or similar app is present."
        print "Checking for exact match."
        cron_job = tab.find_command(
            sys.executable + " " + SITE_ROOT + "/" + cmd)
        if len(list(cron_job)) == 1:
            print "An entry for this instance of cow is already present in Crontab, and no changes are needed."
            return True

    # At this point there are either duplicates, a single bad entry, or no COW
    # entries at all.

    # cron_job = tab.find_command(cmd)
    # tab.remove_all(cmd)

    # print "Writing new Crontab entry for COW, this means there was none before, or there was a problem with the entry(s) that were found."
    # job = tab.new(command=sys.executable + " " + SITE_ROOT+"/"+cmd)
    # job.every_reboot()
    # job.enable()
    # tab.write()
    # print "Crontab entry successfully created."
    print "There is a problem with your crontab setup, make sure you run manage.py install if this is intended as a permanent COW install."
    return True
