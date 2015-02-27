#!/bin/bash
#Gets us in to our virtualenv and runs python

echo $HOME
export WORKON_HOME=$HOME/.virtualenvs
echo $WORKON_HOME
export PROJECT_HOME=$HOME/
echo $PROJECT_HOME
source $WORKON_HOME/uabackend/bin/virtualenvwrapper.sh

workon uabackend
cd $CODE_PATH

echo "PYTHONPATH IS $PYTHONPATH"
echo "CODE_PATH IS $CODE_PATH"
echo "PATH IS $(pwd)"

python $1

deactivate
