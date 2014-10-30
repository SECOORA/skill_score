#!/bin/bash


#/usr/bin/Xvfb :6  &


/usr/X11R6/bin/Xvfb :6  &

echo $! > /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/codar_compare/codar_xvfb.pid
DISPLAY=localhost:6
export DISPLAY

matlab  -nodesktop < /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/codar_compare/codar_compare_wrapper.m

kill `cat /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/codar_compare/codar_xvfb.pid`
rm /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/codar_compare/codar_xvfb.pid
