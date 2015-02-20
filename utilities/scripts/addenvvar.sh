#!/local/bin/bash

##########
#
# Crude script to add environment variables that will be loaded when you workon
# virtualenvs. You need to set up virtualenvs with virtualenvwrapper to get this to work.
#
##########

echo "Adding stuff to virtualenv load variables..."

read -p "Name of virtualenv: " venv
read -p "Name of variable (will be uppercased): " var
read -p "Value to set to: " val

var=$(echo "$var" | tr '[:lower:]' '[:upper:]')

actfile=~/.virtualenvs/$venv/bin/postactivate
deactfile=~/.virtualenvs/$venv/bin/predeactivate

echo "if [[ -n $"$var" ]]" >> $actfile
echo "then" >> $actfile
echo "    export "$var"_BACKUP=$"$var >> $actfile
echo "fi" >> $actfile
echo "export "$var"="$val >> $actfile
echo "" >> $actfile

echo "if [[ -n $"$var"_BACKUP ]]" >> $deactfile
echo "then" >> $deactfile
echo "    export "$var"=$"$var"_BACKUP" >> $deactfile
echo "    unset "$var"_BACKUP" >> $deactfile
echo "else" >> $deactfile
echo "    unset "$var >> $deactfile
echo "fi" >> $deactfile
echo "" >> $deactfile


