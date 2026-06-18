from runs.models import Run
from aetests.models import Test
from models import job
from ae2.models import AE2RUN
import requests
import json
from django.utils import timezone
import logging
import sys
import subprocess
import re
import datetime
import ast

cattleserver = "http://cattle.yourdomain.com"

# JOB_EXIT_CODES= (
#    (0, 'SUCCESS'),
#    (1, 'NOMATCH'),
#    (2, 'PK NOT FOUND'),
#    (3, 'MISSING PK'),
#    (4, 'CURL ERROR'),
#    (5, 'UNCAUGHT EXCEPTION'),
# )


def jobmatrix(myjob):

    myreturn = {"exitcode": 1, "message": "None"}

    if (myjob.command == "CATTLE_RUN_UPLOAD"):
        if myjob.arguments is not None:
            if "PK" in myjob.arguments:
                if len(Run.objects.filter(pk=myjob.arguments["PK"])) > 0:
                    try:
                        myRun = Run.objects.filter(pk=myjob.arguments["PK"])[0]
                        data = json.dumps({
                            "builder": myRun.builder,
                            "revision": myRun.commit,
                            "branch": myRun.parent_branch,
                            "suite": myRun.suite_file,
                            "env": myRun.env_file,
                            "build_number": myRun.build_number,
                            "os": myRun.operating_system,
                            "log_file": myRun.log_file,
                            "results": myRun.run_results,
                            "bug": myRun.caused_bug,
                            "comment": myRun.comment,
                            "start": myRun.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "stop": myRun.end_time.strftime("%Y-%m-%d %H:%M:%S")
                        })

                        headers = {'content-type': 'application/json'}
                        r = requests.post(
                            cattleserver +
                            "/runs/rest/",
                            data,
                            auth=(
                                'root',
                                'cleverpassword'),
                            headers=headers)

                        if "200" in str(r.json):
                            myreturn["exitcode"] = 0
                            myreturn["message"] = "Uploaded run with PK:" + str(myjob.arguments[
                                                                                "PK"]) + " to CATTLE server at " + cattleserver + "\n and returned the following message:" + str(r.text)
                        else:
                            myreturn["exitcode"] = 4
                            myreturn["message"] = "ERROR: Attempted upload of run with PK:" + str(myjob.arguments[
                                                                                                  "PK"]) + " to CATTLE server at " + cattleserver + "\n and returned the following JSON response:" + str(r.json)

                    except Exception as e:
                        myreturn["exitcode"] = 5
                        myreturn["message"] = "ERROR: Uncaught exception during CURL to CATTLE Server: " + \
                            cattleserver + " FAILED with exception " + str(e.message)
                        # raise e #this should only be enabled for debug
                    return myreturn
                else:
                    myreturn["exitcode"] = 2
                    myreturn["message"] = "ERROR: There is no run with PK:" + \
                        str(myjob.arguments["PK"])
                    return myreturn
            else:
                myreturn["exitcode"] = 3
                myreturn[
                    "message"] = "ERROR: No PK provided in your command.arguments dict."
                return myreturn
        else:
            myreturn["exitcode"] = 3
            myreturn[
                "message"] = "ERROR: command.arguments must be a pickled dict object."
            return myreturn

    if (myjob.command == "CATTLE_TEST_UPLOAD"):
        if myjob.arguments is not None:
            if "PK" in myjob.arguments:
                if len(Test.objects.filter(pk=myjob.arguments["PK"])) > 0:
                    try:
                        myTest = Test.objects.filter(
                            pk=myjob.arguments["PK"])[0]

                        data = json.dumps({
                            "builder": myTest.parentrun.builder,
                            "build_number": myTest.parentrun.build_number,
                            "conditions": myTest.test_conditions,
                            "args": myTest.test_args,
                            "sequence": myTest.test_sequence_number,
                            "data_file": myTest.data_file,
                            "results": myTest.test_results,
                            "bug": myTest.caused_bug,
                            "duration": myTest.test_duration,
                            "comment": myTest.comment
                        })

                        headers = {'content-type': 'application/json'}
                        r = requests.post(
                            cattleserver +
                            "/tests/rest/",
                            data,
                            auth=(
                                'root',
                                'cleverpassword'),
                            headers=headers)

                        if "200" in str(r.json):
                            myreturn["exitcode"] = 0
                            myreturn["message"] = "Uploaded test with PK:" + str(myjob.arguments[
                                                                                 "PK"]) + " to CATTLE server at " + cattleserver + "\n and returned the following message:" + str(r.text)
                        else:
                            myreturn["exitcode"] = 4
                            myreturn["message"] = "ERROR: Attempted upload of test with PK:" + str(myjob.arguments[
                                                                                                   "PK"]) + " to CATTLE server at " + cattleserver + "\n and returned the following JSON response:" + str(r.json)

                    except Exception as e:
                        myreturn["exitcode"] = 5
                        myreturn["message"] = "ERROR: Uncaught exception during CURL to CATTLE Server: " + \
                            cattleserver + " FAILED with exception " + str(e.message)
                        # raise e #this should only be enabled for debug
                    return myreturn
                else:
                    myreturn["exitcode"] = 2
                    myreturn[
                        "message"] = "ERROR: There is no test with PK:" + str(myjob.arguments["PK"])
                    return myreturn
            else:
                myreturn["exitcode"] = 3
                myreturn[
                    "message"] = "ERROR: No PK provided in your command.arguments dict."
                return myreturn
        else:
            myreturn["exitcode"] = 3
            myreturn[
                "message"] = "ERROR: command.arguments must be a pickled dict object."
            return myreturn

    # -------------NO JOB FOUND IF CODE GETS TO THIS POINT
    myreturn["exitcode"] = 1
    myreturn["message"] = "ERROR: This job attempts to execute an un-implemented command: " + myjob.command
    return myreturn


def StartTest(
        index=-1,
        start_time=None,
        test_name=None,
        test_num=None,
        test_args=None,
        test_start_time=None,
        test_dat_file=None,
        line_number=0,
        myParentRun=None,
        myAE2RUN=None):
    # if line_number:
    #      print '*** %s' % line_number
    # print " StartTest *** index=%d start time %s" % (index,start_time)
    # print " StartTest *** index=%d name %s" % (index,test_name)
    # print " StartTest *** index=%d number %s" % (index,test_num)
    # print " StartTest *** index=%d args %s" % (index,test_args)
    myTestToQueue = Test(test_results=13,
                         parentrun=myParentRun,
                         test_conditions=test_name,
                         test_args=test_args,
                         test_sequence_number=test_num,
                         data_file=test_dat_file,
                         test_duration=0)
    myTestToQueue.save()
    if not myAE2RUN.muted and myAE2RUN.cleanup == 0:
        myjob = job(
            command="CATTLE_TEST_UPLOAD",
            arguments={
                "PK": myTestToQueue.pk})
        myjob.save()

    return myTestToQueue


def EndTest(
        index=-1,
        end_time=None,
        test_name=None,
        status="FAILED",
        line_number=0,
        TestToEnd=None,
        myAE2RUN=None):
    # if line_number:
    #   print '*** %s' % line_number
    # print " EndTest *** index=%d end time %s" % (index,end_time)
    # print " EndTest *** index=%d name %s" % (index,test_name)
    # print " EndTest *** index=%d status %s" % (index,status)
    if "success" not in status and "PASSED" not in status:

        TestToEnd.test_results = 0
        TestToEnd.end_time = timezone.now()
        TestToEnd.test_duration = int(
            (TestToEnd.end_time - TestToEnd.start_time).total_seconds())
        TestToEnd.comment = "Status was: " + status
    else:
        TestToEnd.end_time = timezone.now()
        TestToEnd.test_duration = int(
            (TestToEnd.end_time - TestToEnd.start_time).total_seconds())
        TestToEnd.test_results = 1

    TestToEnd.save()
    if not myAE2RUN.muted and myAE2RUN.cleanup == 0:
        myjob = job(
            command="CATTLE_TEST_UPLOAD",
            arguments={
                "PK": TestToEnd.pk})
        myjob.save()


def run_ae2(cmd, myParentRun=None, myAE2RUN=None, logger=logging):
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    myAE2RUN.pid = process.pid
    myAE2RUN.save()
    test_status = None
    start_time = None
    test_dat_file = None
    test_num = 0
    test_args = None
    test_start_time = None
    test_name = None
    valid_ae_log = False
    index = 1
    lines_processed = 0
    currentTest = None
    runresult = True
    polledstatus = None
    line = "starting"
    while line != "" and line is not None:
        line = process.stdout.readline()

        lines_processed += 1
        logger.info(line.strip())
        # capture error messages

        if line != "":
            if re.search("AE STARTING", line):
                valid_ae_log = True

            if not test_status and re.search("Test Start", line):
                test_status = "Test Start"
                test_start_time = str(datetime.datetime.now())
                toks = line.split(' ')
                if len(toks) < 6:
                    logger.debug('Invalid Test Start line %s' % line)
                    # break
                test_name = toks[5]

            if test_status == "Test Start" and re.search("._prep_test", line):
                if re.search("CaseArgs", line):
                    toks = line.split(' ')
                    if toks[5] != 'CaseArgs':
                        logger.debug('COW->Invalid CaseArgs line %s' % line)
                    # break
                    test_args_list = line[line.rfind("CaseArgs") + 8:len(line)]
                    test_args_list = test_args_list.replace('[', '')
                    test_args_list = test_args_list.replace(']', '')
                    test_args_list = test_args_list.replace('{', '')
                    test_args_list = test_args_list.replace('}', '')
                    test_args_list = test_args_list.replace('\'', '')
                    test_args = test_args_list.split(':')
                    test_num = test_num + 1
                    # test_num=toks[4]
                    # test_num=test_num.replace('[','')
                    # test_num=test_num.replace(']','')

            if test_status == "Test Start" and re.search(
                    ".report_start", line):
                data = line[line.rfind(":") + 1:len(line)]
                test_dat_file = data.split('-')
                test_dat_file = [n.strip() for n in test_dat_file]
                test_status = "progress"
                test_args = [n.strip() for n in test_args]
                currentTest = StartTest(
                    index=index,
                    start_time=test_start_time,
                    test_name=test_name,
                    test_num=test_num,
                    test_args=test_args,
                    test_dat_file=test_dat_file,
                    line_number=lines_processed,
                    myParentRun=myParentRun,
                    myAE2RUN=myAE2RUN)

            if test_status == "progress" and re.search(
                    "Test End", line) and currentTest is not None:
                test_end_time = str(datetime.datetime.now())
                toks = line.split(' ')
                if len(toks) < 8:
                    logger.debug('Invalid Test End line %s' % line)
                    # break
                test_name = toks[5]
                test_status_line = line[line.rfind(":") + 1:len(line)]
                test_status = test_status_line.strip()
                EndTest(
                    index=index,
                    end_time=test_end_time,
                    test_name=test_name,
                    status=test_status,
                    line_number=lines_processed,
                    TestToEnd=currentTest,
                    myAE2RUN=myAE2RUN)
                if "success" not in test_status and "PASSED" not in test_status:
                    runresult = False
                index = index + 1
                test_status = None

            if not valid_ae_log and lines_processed > 100:
                logger.debug('invalid ae log file AE START not found')
                # break

            if re.search("AE FINISHED", line):
                if test_status and currentTest is not None:
                    EndTest(
                        index=index,
                        end_time='****',
                        test_name=test_name,
                        status="FAILED",
                        line_number=lines_processed,
                        TestToEnd=currentTest,
                        myAE2RUN=myAE2RUN)
                    runresult = False
                elif test_status or not valid_ae_log:
                    runresult = False
    logger.info(
        "Process ended with the following return code:" +
        str(polledstatus))

    if test_status and currentTest is not None:
        EndTest(
            index=index,
            end_time='****',
            test_name=test_name,
            status="FAILED",
            line_number=lines_processed,
            TestToEnd=currentTest,
            myAE2RUN=myAE2RUN)
        logger.error(
            "AE2 exited while running a test, changing to failed status!")
        runresult = False
    elif not valid_ae_log or test_num == 0:
        logger.error("Invalid AE2 execution!")
        runresult = False

    errorline = process.stderr.readline()
    while errorline != "" and errorline is not None:
        logger.error(errorline.strip())
        errorline = process.stderr.readline()

    process.wait()
    return {"result": runresult}
