#!/bin/bash

# Make sure user is root
if ( (( EUID != 0 )) || [ ! "$BASH_VERSION" ] ); then
    echo "Please run as root and use bash not sh to invoke." 1>&2
    exit 1
fi

export WORKON_HOME=/root/.virtualenvs
export PROJECT_HOME=/root/
source $WORKON_HOME/uabackend/bin/virtualenvwrapper.sh

workon uabackend

if [[ -n $CODE_PATH ]]
then

    # Check out $CODE_PATH
    cd $CODE_PATH
    git pull
    chgrp -f     -R advocacy ..
    chmod 771 -f -R          ..

    # Check out /var/server/server
    cd /var/server/
    cp -r $CODE_PATH/flask/* server
    chgrp -f     -R advocacy        server
    chmod 775 -f -R                 server
    if [[ -n $UPLOAD_PATH ]]
    then
        chown -R www-data:www-data $UPLOAD_PATH
    else
        chown -R www-data:www-data server/useradvocacy/reports/uploads
    fi

    python $CODE_PATH/pipelines/cron/scheduler.py

else
    exit 1

fi

deactivate

# restart server
service apache2 restart
