#!/bin/bash

export WORKON_HOME=/root/.virtualenvs
export PROJECT_HOME=/root/
source $WORKON_HOME/uabackend/bin/virtualenvwrapper.sh

workon uabackend

cd $CODE_PATH

echo CODE_PATH IS $CODE_PATH

pwd

python $1

deactivate
