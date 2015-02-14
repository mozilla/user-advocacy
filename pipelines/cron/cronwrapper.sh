#!/bin/bash

export WORKON_HOME=/root/.virtualenvs
export PROJECT_HOME=/root/
source $WORKON_HOME/uabackend/bin/virtualenvwrapper.sh

workon uabackend

cd $CODE_PATH

python $1

deactivate
