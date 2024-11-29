#!/usr/bin/bash

if [ -z "$WALLESS_ROOT" ]; then
    export WALLESS_ROOT=$HOME
fi
cd $WALLESS_ROOT

if [ ! -z "$WALLESS_VENV" ]; then
    source $WALLESS_VENV/bin/activate
fi

for i in $(seq 1000); do
    if ping -c 1 1.1.1.1; then
        break
    fi
    sleep 2
done
export EARLY_SETUP=1

tmux new-session -d -s walless -n site
sleep 3
tmux send-keys -t walless:site "cd $WALLESS_ROOT/site/walless" C-m
tmux send-keys -t walless:site "git pull" C-m
if [ ! -z "$WALLESS_VENV" ]; then
    tmux send-keys -t walless:site "source $WALLESS_VENV/bin/activate" C-m
fi
tmux send-keys -t walless:site "python3 manage.py runserver 127.0.0.1:9011" C-m
