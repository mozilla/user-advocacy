#!/bin/bash
#Gets us in to our virtualenv and runs python

export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/
source $WORKON_HOME/uabackend/bin/virtualenvwrapper.sh

workon uabackend
cd $CODE_PATH
eval "$@"
deactivate
