#!/bin/bash

#kill buildslave
pkill -f "buildslave"

#kill queuemaster
#kill cow
pkill -f "manage.py"

#svn update
svn update $1

#run install_requirements script
#/bin/bash $1/install_requirements.sh

/opt/python2.7/bin/python2.7 /root/cow/manage.py makemigrations
/opt/python2.7/bin/python2.7 /root/cow/manage.py migrate
#yes | /opt/python2.7/bin/python2.7 manage.py install



#/etc/init.d/crond stop
#/etc/init.d/crond start

/opt/python2.7/bin/python2.7 /root/cow/manage.py runserver 0.0.0.0:80 > /root/cow/logs/server.log 2>&1 &

/opt/python2.7/bin/python2.7 /root/cow/manage.py queuemaster > /root/cow/logs/queuemaster.log 2>&1 &

disown #disowns jobs so that manage.py can run in the background

#reboot is no longer used on updates
#reboot now
