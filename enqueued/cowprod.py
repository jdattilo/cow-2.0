#!/opt/python2.7/bin/python2.7
import requests
import json
from time import sleep
import argparse
import sys

_targetcow = ""
_fldccommit = ""
_fldcbranch = ""
_ae2suite = ""
_ae2env = ""
_toolsexe = ""
_fldcexe = ""

# #########################PROCESS ARGUMENTS using argparse################
# #########################################################################
parser = argparse.ArgumentParser(
    description='Contacts Cerberus and initiates a log dump.')
parser.add_argument(
    'passedinfo',
    metavar='log-URL',
    type=str,
    nargs='+',
    help='Variables to pass along in form "VARIABLE|VALUE etc..., you should include: commit, build, builder, results, suite, env, and sysos.')

args = parser.parse_args()

for myArgument in args.passedinfo:
    myArgument = myArgument.split('|')
    if len(myArgument) > 1:
        if myArgument[0] == "targetcow":
            _targetcow = myArgument[1]
            print "_targetcow = " + _targetcow
        if myArgument[0] == "fldccommit":
            _fldccommit = myArgument[1]
            print "_fldccommit = " + _fldccommit
        if myArgument[0] == "fldcbranch":
            _fldcbranch = myArgument[1]
            print "_fldcbranch = " + _fldcbranch
        if myArgument[0] == "ae2suite":
            _ae2suite = myArgument[1]
            print "_ae2suite = " + _ae2suite
        if myArgument[0] == "ae2env":
            _ae2env = myArgument[1]
            print "_ae2env = " + _ae2env
        if myArgument[0] == "toolsexe":
            _toolsexe = myArgument[1]
            print "_toolsexe = " + _toolsexe
        if myArgument[0] == "fldcexe":
            _fldcexe = myArgument[1]
            print "_fldcexe = " + _fldcexe

# #########################################################################


def safesleep(delay):
    try:
        sleep(delay)
        return True
    except:
        return False


def enqueue(cow, suite, env, branch="na", commit=0, tools="", rpm=""):
    myreturn = {"exitcode": -1, "runcode": -1, "message": "Did not execute"}

    myjobpk = None

    data = json.dumps({"action": "enqueue",
                       "command": "ae2run",
                       "arguments": {
                           "branch": branch,
                           "commit": commit,
                           "env": env,
                           "suite": suite,
                           "tools": tools,
                           "rpm": rpm,
                           "muted": False}
                       })

    headers = {'content-type': 'application/json'}
    r = requests.post(
        "http://" +
        cow +
        ".yourdomain.com/enqueued/rest",
        data,
        auth=(
            'root',
            'cleverpassword'),
        headers=headers)

    if "200" in str(r.json):
        myjson = json.loads(r.text)
        # print myjson["message"]
        myjobpk = myjson["jobpk"]
        myreturn["exitcode"] = 0
        myreturn["message"] = "Job queued with PK:" + \
            str(myjson["jobpk"]) + " to cow server at " + cow + "\n and returned the following message:" + str(r.text)
        if myjson["returncode"] != 0:
            myreturn["exitcode"] = 1
            myreturn["message"] = "ERROR:" + str(myjson["jobpk"]) + " is already running on " + \
                cow + "\n the following message was returned:" + str(r.text)

    else:
        myreturn["exitcode"] = 4
        myreturn["message"] = "ERROR: Json returned the following JSON response:" + \
            str(r.json) + " " + str(r.text)

    if myreturn["exitcode"] == 0 and myjobpk:
        print "Starting job poll loop."
        finished = False

        while not finished:
            # change this to something bigger like 60 or 120 seconds
            safesleep(60)

            data = json.dumps({"action": "check",
                               "jobpk": myjobpk
                               })

            headers = {'content-type': 'application/json'}
            r = requests.post(
                "http://" +
                cow +
                ".yourdomain.com/enqueued/rest",
                data,
                auth=(
                    'root',
                    'cleverpassword'),
                headers=headers)
            myjson = json.loads(r.text)
            if myjson["message"]:
                print("Test is still running on <a href ='http://" +
                      cow + ".yourdomain.com'>" + cow + "</a>")
            if "200" in str(r.json):
                myjson = json.loads(r.text)
                if myjson["command_return"] is not None:
                    print r.text
                    myreturn["runcode"] = myjson["command_return"]
                    break
            else:
                myreturn["exitcode"] = 6
                myreturn[
                    "message"] = "ERROR: PROBLEM WITH REST PROTOCOL:" + str(r.text)
                break

    return myreturn


# command line call example
# /opt/python2.7/bin/python2.7 cowprod.py "targetcow|bs01" "ae2suite|/root/ae2/src/suite_files/examples/hello_suite.cfg" "ae2env|/root/cow/static/env_files/bt18_env.cfg" "fldcbranch|branches/san_buildbot/BRN-2047/" "fldccommit|44263" "toolsexe|http://nfs5.yourdomain.com/exports/build_n_test/BURNSIDE/full/branches/san_buildbot/BRN-2047/44263/win2k12/TCP/Setup-Support-TCP-2_1_0_44263-Debug.exe" "fldcexe|http://nfs5.yourdomain.com/exports/build_n_test/BURNSIDE/full/branches/san_buildbot/BRN-2047/44263/win2k12/TCP/Setup-FluidCache-TCP-2_1_0_44263-Debug.exe"


if __name__ == '__main__':
    print "---> COMMANDING " + _targetcow + " <---"
    jobreturn = enqueue(cow=_targetcow,
                        suite=_ae2suite,
                        env=_ae2env,
                        branch=_fldcbranch,
                        commit=_fldccommit,
                        tools=_toolsexe,
                        rpm=_fldcexe)
    print "---> Execution completed on " + _targetcow + " and returned message as follows <---"
    print jobreturn["message"]

    if jobreturn["exitcode"] == 0 and jobreturn["runcode"] == 1:
        print "run passed."
        sys.exit(0)
    else:
        print "run failed with cowprod exit code: " + str(jobreturn["exitcode"]) + " and cow run exit code of: " + str(jobreturn["runcode"]) + "\nand Message:" + jobreturn["message"]
        sys.exit(1)
