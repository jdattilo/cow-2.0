import sys
import os
import shutil
import socket
from cluster.models import cluster_member
import yaml
sys.path.append("/root")
from svn_credentials import user, password
sys.path.remove("/root")


def pullae2(install_directory, branch_address):
    try:
        shutil.rmtree(install_directory)
    except:
        print "No directory to delete... Moving on."

    os.popen(
        'svn co ' +
        install_directory +
        ' ' +
        install_directory +
        ' --username "' +
        user +
        '" --password "' +
        password +
        '" --non-interactive')
    ae2inf()

    return DiscoverOwnedEnvironments(
        ipaddr=addr,
        dirname=install_directory +
        "/src/env_files",
        debug=False)


def checkae2install(install_directory):
    hostname = socket.gethostname()
    addr = socket.gethostbyname(hostname)
    print 'The address of ', hostname, 'is', addr

    return DiscoverOwnedEnvironments(
        ipaddr=addr,
        dirname=install_directory +
        "/src/env_files",
        debug=False)


def ae2info(install_directory):
    infostructure = []
    return os.popen('svn info ' + install_directory)


def OpenYAMLFile(filename=None, debug=False):
    """
    function returns dictionary from a yaml file
    on failure dictionary is empty
    """
    if not filename:
        if debug:
            print 'OpenYAMLFile: invalid argument'
        return {}

    if debug:
        print ('OpenYAMLFile: %s' % filename)
    try:
        f = open(filename, 'r')
    except:
        if debug:
            print ('OpenYAMLFile: unable to open %s' % filename)
        return {}

    try:
        env_dict = yaml.load(f)
    except:
        if debug:
            print 'OpenYAMLFile: unable to load yaml '
        f.close()
        return {}

    f.close()
    return env_dict


def IsEnvironmentOwner(ipaddr=None, full_path_name=None, debug=True):
    """
    The function returns True if the environment files driver is
    that IP address, and false if the environment is not run by
    that IP.
    """
    if not ipaddr or not full_path_name:
        if debug:
            print 'IsEnvironmentOwner: invalid arguments'
        return False

    env_dict = OpenYAMLFile(full_path_name, debug=debug)
    if len(env_dict) <= 0:
        if debug:
            print 'IsEnvironmentOwner: dictionary not found'
        return False

    for key, value in env_dict.items():
        if key in "PYRO_NS_NAME" and ipaddr in value:
            return True

    if debug:
        print 'IsEnvironmentOwner: PYRO_NS_NAME not found'
    return False


def IsValidEnvFile(filename=None, debug=False):
    """
    verifies if env file is proper
    """
    if not filename:
        if debug:
            print 'IsValidEnvFile: invalid arguments'
        return False

    if ".svn" in filename:
        if debug:
            print 'IsValidEnvFile: invalid filename'
        return False

    if debug:
        print ('IsValidEnvFile: %s' % (filename))

    env_dict = OpenYAMLFile(filename, debug=debug)
    if env_dict:
        if len(env_dict) <= 0:
            if debug:
                print 'IsValidEnvFile: dictionary not found'
            return False
    else:
        return False

    """ sanity checks """
    if "PYRO_NS_NAME" not in env_dict:
        if debug:
            print 'IsValidEnvFile: PYRO_NS_NAME not found'
        return False

    """ sanity checks """
    if "SUT_NODES" not in env_dict:
        if debug:
            print 'IsValidEnvFile: SUT_NODES not found'
        return False

    driver = env_dict["PYRO_NS_NAME"]
    node_list = env_dict["SUT_NODES"]

    """
        verify the driver ip is not listed
        as node
    """
    for node in node_list:
        if 'IP' not in node:
            if debug:
                print 'IsValidEnvFile: key IP not found'
            return False
        if driver in node['IP']:
            if debug:
                print 'IsValidEnvFile: driver found in node'
            return False

    return True


def IsValidSuiteFile(filename=None, debug=False):
    """
    verifies if env file is proper
    """
    if not filename:
        if debug:
            print 'IsValidSuiteFile: invalid arguments'
        return False

    if ".svn" in filename:
        if debug:
            print 'IsValidSuiteFile: invalid filename'
        return False

    if debug:
        print ('IsValidSuiteFile: %s' % (filename))

    env_dict = OpenYAMLFile(filename, debug=debug)
    if env_dict:
        if len(env_dict) <= 0:
            if debug:
                print 'IsValidSuiteFile: dictionary not found'
            return False

        """ sanity checks """
        if "TESTLIST" not in env_dict:
            if debug:
                print 'IsValidSuiteFile: TESTLIST not found'
            print 'IsValidSuiteFile: TESTLIST not found'
            return False

        """ sanity checks """
        if "SUITE" not in env_dict:
            if debug:
                print 'IsValidSuiteFile: SUITE not found'
            print 'IsValidSuiteFile: SUITE not found'
            return False
    else:
        return False

    return True


def DiscoverOwnedEnvironments(ipaddr=None, dirname=None, debug=True):
    """
    Given an IP address and directory address on the local system the
    function returns all valid environments in the form of an array of
    file addresses.
    """
    # if debug:
    print 'Starting'
    if not ipaddr or not dirname:
        print 'DiscoverOwnedEnvironments: invalid arguments'
        return False
    if dirname[len(dirname) - 1] != '/':
        dirname = dirname + '/'
    if debug:
        print "got past dirname"
    valid_env_files = []
    abs_dirname = os.path.abspath(dirname)
    for curs, dirs, files in os.walk(abs_dirname):
        if debug:
            print "Walking files"
        for files in os.listdir(curs):
            abs_path_name = curs + '/' + files
            if debug:
                print abs_path_name
            if IsValidEnvFile(
                    filename=abs_path_name,
                    debug=debug) and IsEnvironmentOwner(
                    ipaddr=ipaddr,
                    full_path_name=abs_path_name,
                    debug=debug):
                valid_env_files.append(abs_path_name)
    if debug:
        print "About to check env list length before returning"
    if len(valid_env_files):
        return valid_env_files
    else:
        if debug:
            print 'DiscoverOwnedEnvironments: no valid env files found'
        return None


def DiscoverAllEnvironments(dirname=None, debug=False):
    """
    Given a directory address on the local system the
    function returns all environments in the form of an array of
    file addresses.
    """
    if not dirname:
        print 'DiscoverOwnedEnvironments: invalid arguments'
        return False
    if dirname[len(dirname) - 1] != '/':
        dirname = dirname + '/'

    valid_env_files = []
    abs_dirname = os.path.abspath(dirname)
    for curs, dirs, files in os.walk(abs_dirname):
        for files in os.listdir(curs):
            abs_path_name = curs + '/' + files
            if debug:
                print abs_path_name
            if IsValidEnvFile(filename=abs_path_name, debug=debug):
                valid_env_files.append(abs_path_name)

    if len(valid_env_files):
        return valid_env_files
    else:
        if debug:
            print 'DiscoverOwnedEnvironments: no valid env files found'
        return None


def ChangeEnvironment(ipaddr=None, full_path_name=None, debug=False):
    """
    ChangeEnvironment function given an environment file location and ip address (of driver/cow).
    The function first validates ownership, and then reads
    information about each cluster member into a dictionary of dictionaries.
    """
    if not ipaddr or not full_path_name:
        if debug:
            print 'ChangeEnvironment: invalid arguments'
        return False

    cluster_member.objects.all().delete()  # removes existing cluster members

    env_dict = OpenYAMLFile(full_path_name, debug=debug)
    if len(env_dict) <= 0:
        if debug:
            print 'ChangeEnvironment: env file not found'
        return False

    if IsValidEnvFile(
            filename=full_path_name,
            debug=debug) and IsEnvironmentOwner(
            ipaddr=ipaddr,
            full_path_name=full_path_name,
            debug=debug):
        for key, value in env_dict.items():
            if key in 'SUT_NODES':
                node_list = value
                for node in node_list:
                    if 'HOSTNAME' not in node:
                        continue
                    try:
                        hostname = str(node["HOSTNAME"])
                        mymember = cluster_member(
                            hostname=hostname, operating_system=(
                                node["OS_TYPE"]))
                        mymember.save()
                        # print ('cluster node:%s os:%s' % (node['HOSTNAME'], node['OS_TYPE']))
                    except:
                        hostname = str(node["HOSTNAME"])
                        mymember = cluster_member(
                            hostname=hostname, operating_system="UNKNOWN")
                        mymember.save()
                        if debug:
                            print 'ChangeEnvironment: OS_TYPE not found'
                        # print ('cluster node:%s' % node['HOSTNAME'])


def DiscoverSuiteFiles(dirname=None, debug=False):
    """
    Discovers ae2 suite files and returns a list
    """
    if not dirname:
        if debug:
            print 'DiscoverSuiteFiles: invalid arguments'
        return []

    if dirname[len(dirname) - 1] != '/':
        dirname = dirname + '/'

    valid_suite_files = []
    abs_dirname = os.path.abspath(dirname)
    for curs, dirs, files in os.walk(abs_dirname):
        for files in os.listdir(curs):
            abs_path_name = curs + '/' + files
            if debug:
                print abs_path_name
            if IsValidSuiteFile(filename=abs_path_name, debug=debug):
                valid_suite_files.append(abs_path_name)

    if len(valid_suite_files):
        return valid_suite_files
    else:
        if debug:
            print 'DiscoverSuiteFiles: no valid suite files found'
        return []
