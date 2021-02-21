
#!/bin/bash
kill_python () {
    local xvfb_pids=`ps aux | grep python3 | grep -v grep | awk '{print $2}'`
    if [ "$xvfb_pids" != "" ]; then
        echo "Killing the following xvfb processes: $xvfb_pids"
        sudo kill $xvfb_pids
    else
        echo "No xvfb processes to kill"
    fi
}

kill_python


