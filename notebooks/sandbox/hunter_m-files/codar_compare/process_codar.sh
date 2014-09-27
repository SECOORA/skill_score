#!/bin/bash


#/usr/bin/Xvfb :6  &


/usr/X11R6/bin/Xvfb :6  &

echo $! > /home/hunter/roms/codar_comp/codar_xvfb.pid
DISPLAY=localhost:6
export DISPLAY 
 
/opt/matlab//bin/matlab  -nodesktop < /home/hunter/roms/codar_comp/codar_compare_wrapper.m

kill `cat /home/hunter/roms/codar_comp/codar_xvfb.pid`
rm /home/hunter/roms/codar_comp/codar_xvfb.pid
