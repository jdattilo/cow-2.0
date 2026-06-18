import sys
import os
import shutil

sys.path.append("/root")
from svn_credentials import user, password
sys.path.remove("/root")


def pullae2(ae2directory, ae2branch, ae2revision):
    try:
        shutil.rmtree(ae2directory)
    except:
        print "No directory to delete... Moving on."

    os.popen(
        'svn co ' +
        ae2branch +
        ' ' +
        ae2directory +
        ' --username "' +
        user +
        '" --password "' +
        password +
        '" --non-interactive')
