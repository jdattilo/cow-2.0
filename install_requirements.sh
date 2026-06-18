#!/bin/bash

yum -y install python-setuptools
yum -y install python-devel
yum -y install openldap-devel
yum -y install subversion-devel
yum -y install sqlite-devel.x86_64
yum -y install bzip2-devel

yes | curl "https://bootstrap.pypa.io/get-pip.py" > "/root/get-pip.py"
yes | /opt/python2.7/bin/python2.7 /root/get-pip.py

yes | /opt/python2.7/bin/pip install Django==1.8
yes | /opt/python2.7/bin/pip install python-ldap
yes | /opt/python2.7/bin/pip install django-auth-ldap
yes | /opt/python2.7/bin/pip install pysqlite
yes | /opt/python2.7/bin/pip install django-simple-history
yes | /opt/python2.7/bin/pip install python-crontab
yes | /opt/python2.7/bin/pip install django-picklefield
yes | /opt/python2.7/bin/pip install eventlet
yes | /opt/python2.7/bin/pip install PyYAML
yes | /opt/python2.7/bin/pip install requests
yes | /opt/python2.7/bin/pip install djangorestframework
#yes | /opt/python2.7/bin/pip install django-wysiwyg
yes | /opt/python2.7/bin/pip install jira

chmod 777 cluster/cluster_clean.py

#stores credentials for svnuser to be used by cow
echo "user, password='svnuser', 'cleverpassword'" > /root/svn_credentials.py

#copies working sqlite3 binaries from python2.6
yes | cp /usr/lib64/python2.6/lib-dynload/_sqlite3.so /opt/python2.7/lib/python2.7/site-packages/

#rebuild python
cd /root/packages/Python-2.7.2
./configure --prefix=/opt/python2.7
make
make altinstall
echo "/opt/python2.7/lib" >> /etc/ld.so.conf.d/opt-python2.7.conf
ldconfig

cd /root/cow

#install the latest winexe
yes | cp ae2/winexe /usr/bin/winexe
yes | chmod +x /usr/bin/winexe 


/opt/python2.7/bin/python2.7 manage.py makemigrations
/opt/python2.7/bin/python2.7 manage.py migrate
/opt/python2.7/bin/python2.7 manage.py install

if [ "$1" == "makesuperuser" ];then
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('root', 'cow@yourdomain.com', 'cleverpassword')" | /opt/python2.7/bin/python2.7 manage.py shell
fi
