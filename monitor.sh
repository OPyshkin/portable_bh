#!/bin/sh

myscript(){
    sudo python3 /root/new_opi/main.py 
}

until myscript; do
    echo "'main.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done
