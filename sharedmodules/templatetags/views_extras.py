from django import template
from django.template.defaultfilters import stringfilter
from jira.client import JIRA
from datetime import datetime, date
import json
import urllib
import time
from django.utils.timezone import utc

register = template.Library()


@register.filter
def format_time(sec):
    """Formats seconds into days:hours:minutes:seconds"""
    sec = int(sec)
    days = sec / 86400
    sec -= 86400 * days

    hrs = sec / 3600
    sec -= 3600 * hrs

    mins = sec / 60
    sec -= 60 * mins

    myReturn = ""
    if days == 0 and hrs == 0:
        myReturn = (str(mins).zfill(2) + ':' + str(sec).zfill(2))
    elif days == 0:
        myReturn = (
            str(hrs) +
            ':' +
            str(mins).zfill(2) +
            ':' +
            str(sec).zfill(2))
    else:
        myReturn = (
            str(days) +
            ':' +
            str(hrs) +
            ':' +
            str(mins).zfill(2) +
            ':' +
            str(sec).zfill(2))

    return myReturn

# #################STATUS CODE RANGES###################
_INNERPASSRANGE_LOW = 1
_INNERPASSRANGE_HIGH = 10
_OUTERPASSRANGE = 120
_INVALIDRANGE_LOW = 11
_INVALIDRANGE_HIGH = 20
# #################SPECIFIC CODES#######################
_PASSOVERIDED_CODE = 2
_INTERUPTED_CODE = 11
_IN_PROGRESS_CODE = 13
_FAILOVERIDE_CODE = 60
_UNDERINVESTIGATION_CODE = 65


@register.filter
def translate_PF(code):
    """Translates PF codes into string format"""
    if code == '' or code is None:
        code = 1
    code = int(code)
    tresults = "PASS"
    if (code >= _INNERPASSRANGE_LOW and code <=
            _INNERPASSRANGE_HIGH) or code >= _OUTERPASSRANGE:
        tresults = "PASS"
        if code == _PASSOVERIDED_CODE:
            tresults = "POVR"
    elif (code >= _INVALIDRANGE_LOW and code <= _INVALIDRANGE_HIGH):
        tresults = "INVL"
        if(code == _INTERUPTED_CODE):
            tresults = "INTR"  # Interrupted status
        if(code == _IN_PROGRESS_CODE):
            tresults = "IPROG"  # Interrupted status
    else:
        tresults = "FAIL"
        if code == _FAILOVERIDE_CODE:
            tresults = "FOVER"
        if code == _UNDERINVESTIGATION_CODE:
            tresults = "INVG"
    return tresults


@register.filter
def translate_PF_class(code):
    """Translates PF codes into class strings"""
    if code == '' or code is None:
        code = 1
    code = int(code)
    trclass = "PASS"
    if (code >= _INNERPASSRANGE_LOW and code <=
            _INNERPASSRANGE_HIGH) or code >= _OUTERPASSRANGE:
        trclass = "PASS"
    elif (code >= _INVALIDRANGE_LOW and code <= _INVALIDRANGE_HIGH):
        trclass = "INVL"
        if(code == _IN_PROGRESS_CODE):
            trclass = "IPROG"  # Interrupted status
    else:
        trclass = "FAIL"
    return trclass


@register.filter
def jira_pull(thebugs):
    """Authenticate against JIRA, pulls, and renders bug information."""
    thereturn = ""
    thebugs = thebugs.replace(" ", "")
    if thebugs != "":
        myBugs = str(thebugs).split(',')
        first_bug = True
        for bugnum in myBugs:
            # #########################CONNECT TO JIRA#########################
            options = {
                'server': 'http://jira.yourdomain.com'
            }
            jira = JIRA(
                options=options,
                basic_auth=(
                    'jirauser',
                    'cleverpassword'))  # change to your credentials
            if first_bug:
                first_bug = False
            else:
                thereturn += "<br />"
            try:
                # Get an issue.
                issue = jira.issue(bugnum)
                thereturn += "<a href = 'http://jira.yourdomain.com/browse/" + \
                    str(bugnum) + "' target = '_EMPTY' class = 'resolution-" + str(issue.fields.resolution) + " " + str(bugnum) + "' >" + str(bugnum) + "</a>"
                thereturn += " " + str(issue.fields.status).split(" ")[0]
                thereturn += '<br>' + str(issue.fields.summary)
            except Exception as e:
                thereturn += "Unable to pull from JIRA: \n" + str(e)
    return thereturn


@register.filter
def jira_pull_br(thebugs):
    """Authenticate against JIRA, pulls, and renders bug information for buildreports."""
    thereturn = ""
    thebugs = thebugs.replace(" ", "")
    if thebugs != "":
        myBugs = str(thebugs).split(',')
        first_bug = True
        for bugnum in myBugs:
            # #########################CONNECT TO JIRA#########################
            options = {
                'server': 'http://jira.yourdomain.com'
            }
            jira = JIRA(
                options=options,
                basic_auth=(
                    'jirauser',
                    'cleverpassword'))  # change to jira credentials
            if first_bug:
                first_bug = False
            else:
                thereturn += "<br />"
            try:
                # Get an issue.
                issue = jira.issue(bugnum)
                thereturn += "<div onmouseout='unhighlight_class(\"" + str(
                    bugnum) + "\")' onmouseover='highlight_class(\"" + str(bugnum) + "\")'><span class ='" + str(bugnum) + "' >"
                thereturn += "<a href = 'http://jira.yourdomain.com/browse/" + \
                    str(bugnum) + "' target = '_EMPTY' class = 'resolution-" + str(issue.fields.resolution) + " " + str(bugnum) + "' >" + str(bugnum) + "</a>"
                thereturn += " <b>Status:</b>" + \
                    str(issue.fields.status).split(" ")[0]
                if str(issue.fields.status).split(" ")[0] == "In":
                    thereturn += " Progress"
                thereturn += ' <b>Summary:</b> ' + \
                    str(issue.fields.summary) + "</span></div>"
            except Exception as e:
                thereturn += "Unable to pull from JIRA: \n" + str(e)
    return thereturn


@register.filter
def address_tail(address):
    """Pulls the tail of the address url"""
    # this could provide addressing as well in the future as long as a |safe
    # is used in the call.
    return str(address).split('/')[-1]


@register.filter
def suite_link(address):
    """Pulls the tail of the suite url"""
    # this should access scruffy suite pages
    return str(address).split('/')[-1]


@register.filter
def env_link(address):
    """Pulls the tail of the env url"""
    # in the future this should link to the machines that were actually
    # running somehow
    return str(address).split('/')[-1]


# This is used by getbuilderstate
def getbuildbotproperty(myproperties, myfield):
    """Translates data from properties inside buildbot JSON"""
    myreturn = "NA"
    for prop in myproperties:
        try:
            if(prop[0] == myfield):
                myreturn = prop[1]
                break
        except Exception as e:
            myreturn = "<!-- " + str(e) + " -->"
    return myreturn

# microtime function for calculations of time difference


def microtime(get_as_float=False):
    """converts an integer or float to microtime"""
    if get_as_float:
        return time.time()
    else:
        return '%f %d' % math.modf(time.time())


@register.filter()
def subtractdate(value, arg):
    """Calculate difference in seconds between two dates."""
    days = int((value - arg).days * 86400)
    seconds = int((value - arg).seconds)
    return int(days + seconds)


@register.filter()
def subtractnow(value):
    """Calculate difference in seconds between two dates."""
    arg = datetime.utcnow().replace(tzinfo=utc)
    value = (arg - value).total_seconds()
    return int(value)


@register.filter()
def getbuilderstate(value):
    """Pulls report from buildbot JSON and generates output rendering."""
    builderstate = "unreachable"
    builderreport = ""
    try:
        loadedjson = urllib.urlopen(
            str(value).split("builders")[0] +
            "json/builders" +
            str(value).split("builders")[1] +
            "?as_text=1").read()
        result = json.loads(loadedjson)
        builderreport = "<a href = '" + value + \
            "' target='_EMPTY'>" + value.split('/')[-1] + "</a>"
        builderreport = builderreport + '<br />State:' + result['state']
        builderstate = result['state']
        loadedjson = urllib.urlopen(
            str(value).split("builders")[0] +
            "json/builders" +
            str(value).split("builders")[1] +
            "/builds/-1?as_text=1").read()
        result = json.loads(loadedjson)
        builderreport = builderreport + '<br /> Build:<a href = "' + str(value) + '/builds/' + str(
            result['number']) + '" target="_EMPTY">' + str(
            result['number']) + '</a><br />Branch:' + result['sourceStamps'][0]['branch']
        builderreport = builderreport + '<br /> Commit:' + \
            getbuildbotproperty(result['properties'], "got_revision")
        if result['times'][1] is not None:
            builderreport = builderreport + "<!--Start Time Defined as: " + \
                str(result['times'][0]) + "-->"
            builderreport = builderreport + "<!--End Time Defined as: " + \
                str(result['times'][1]) + "-->"
            builderreport = builderreport + '<br /> Run Time: '
            builderreport = builderreport + \
                str(format_time(int(result['times'][1] - result['times'][0])))
        else:
            builderreport = builderreport + "<!--Start Time Defined as: " + \
                str(result['times'][0]) + "-->"
            endtime = microtime(True)
            builderreport = builderreport + \
                "<!--End Time Determined to be current time: " + str(endtime) + "-->"
            builderreport = builderreport + '<br /> Run Time: '
            builderreport = builderreport + \
                str(format_time(int(endtime - result['times'][0])))
    except Exception as e:
        # decoding failed
        builderreport = builderreport + "<!-- Failed to parse/load JSON" + \
            str(value) + "/builds/-1?as_text=1 " + str(e) + "-->"
    builderreport = '<div class="' + builderstate + \
        '" style= "width:100%;height:100%;">' + builderreport + '</div>'
    return str(builderreport)
