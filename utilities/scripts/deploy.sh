#!/bin/bash

# Make sure user is root
if ( (( EUID != 0 )) || [ ! "$BASH_VERSION" ] ); then
    echo "Please run as root and use bash not sh to invoke." 1>&2
    exit 1
fi

python $CODE_PATH/pipelines/cron/scheduler.py

# Check out /home/shared/code
cd /home/shared/code
git pull
chgrp -f     -R advocacy ..
chmod 771 -f -R          ..

# Check out /var/server/server
cd /var/server/
cp -r /home/shared/code/flask/* server
chgrp -f     -R advocacy        server
chmod 775 -f -R                 server

# restart server
service apache2 restart