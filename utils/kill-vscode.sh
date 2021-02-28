
#!/bin/bash
kill_vscode () {
    local xvfb_pids=`ps aux | grep vscode | grep -v grep | awk '{print $2}'`
    if [ "$xvfb_pids" != "" ]; then
        echo "Killing the following vscode processes: $xvfb_pids"
        sudo kill $xvfb_pids
    else
        echo "No xvfb processes to kill"
    fi
}

kill_vscode

