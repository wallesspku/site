#!/usr/bin/bash

# Process:
# 1. if WALLESS_ROOT is not set, set it to $HOME. cd to this directory.
# 2. if WALLESS_VENV is set, activate it
# 3. wait for internet connection
# 4. source env_setup.sh if it exists
# 5. try to pull the latest version of the code for each git repo
# 6. if venv is set, install the latest version of utils
# 7. if PYTHONEXEC is not set, set it to the python3 in the venv or the system
# 8. run the main script

if [ -z "$WALLESS_ROOT" ]; then
    export WALLESS_ROOT=$HOME
fi
cd $WALLESS_ROOT
if [ -z "$WALLESS_VENV" ] && [ -d $WALLESS_ROOT/walless_venv ]; then
    export WALLESS_VENV=$WALLESS_ROOT/walless_venv
fi

for i in $(seq 10);
do
    if ping -c 1 1.1.1.1; then
        break
    fi
    sleep 2
done
# echo "connected to the internet"

if [ -f ./env_setup.sh ]; then
    source ./env_setup.sh
fi

# pull
for GITPATH in "./site" "./main_config" "./ca" "./utils";
do
    if [ -z $NO_GIT_PULL ] && [ -d $GITPATH ]; then
        git -C $GITPATH pull
    fi
done

if [ ! -z "$WALLESS_VENV" ]; then
    source $WALLESS_VENV/bin/activate
    if [ -d $WALLESS_ROOT/utils ]; then
        pip3 install -U --no-cache-dir $WALLESS_ROOT/utils
    else
        pip3 install -U --no-cache-dir git+https://github.com/wallesspku/utils.git
    fi
fi

if [ -z $PYTHONEXEC ]; then
    if [ $WALLESS_VENV ]; then
        export PYTHONEXEC=$WALLESS_VENV/bin/python3
    else
        export PYTHONEXEC=$(which python3)
    fi
fi

cd $WALLESS_ROOT/site/walless
$PYTHONEXEC manage.py runserver --skip-checks --noreload --no-color 127.0.0.1:9011
