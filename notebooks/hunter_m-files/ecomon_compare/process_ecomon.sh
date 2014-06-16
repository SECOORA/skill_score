#!/bin/bash


#/usr/X11R6/bin/Xvfb :6  &
#echo $! > /home/hunter/roms/glider_comp/glider_xvfb.pid
#DISPLAY=localhost:6
#export DISPLAY 
 
/opt/MatlabR2008b//bin/matlab  -nodesktop -nosplash < /home/hunter/roms/ecomon_comp/ecomon_compare_wrapper.m

#kill `cat /home/hunter/roms/glider_comp/glider_xvfb.pid`
#rm /home/hunter/roms/glider_comp/glider_xvfb.pid