
#!/bin/bash
kill_xvfb () {
    local xvfb_pids=`ps aux | grep Xvfb | grep -v grep | awk '{print $2}'`
    if [ "$xvfb_pids" != "" ]; then
        echo "Killing the following xvfb processes: $xvfb_pids"
        sudo kill $xvfb_pids
    else
        echo "No xvfb processes to kill"
    fi
}
kill_x11vnc () {
    local xvfb_pids=`ps aux | grep X11vnc | grep -v grep | awk '{print $2}'`
    if [ "$xvfb_pids" != "" ]; then
        echo "Killing the following x11vnc processes: $xvfb_pids"
        sudo kill $xvfb_pids
    else
        echo "No x11vnc processes to kill"
    fi
}
kill_x11vnc
kill_xvfb

