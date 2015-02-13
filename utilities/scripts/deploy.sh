#!/bin/bash
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

sudo service apache2 restart