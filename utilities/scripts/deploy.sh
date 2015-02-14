#!/bin/bash

# Make sure user is root
if ( (( EUID != 0 )) || [ ! "$BASH_VERSION" ] ); then
    echo "Please run as root and use bash not sh to invoke." 1>&2
    exit 1
fi

source /root/.virtualenvs/uabackend/bin/activate

python $CODE_PATH/pipelines/cron/scheduler.py

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

deactivate

# restart server
service apache2 restart
