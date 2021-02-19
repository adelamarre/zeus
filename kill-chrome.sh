
#!/bin/bash
kill_chrome () {
    local xvfb_pids=`ps aux | grep chrome | grep -v grep | awk '{print $2}'`
    if [ "$xvfb_pids" != "" ]; then
        echo "Killing the following chrome processes: $xvfb_pids"
        sudo kill $xvfb_pids
    else
        echo "No xvfb processes to kill"
    fi
}


kill_chrome

