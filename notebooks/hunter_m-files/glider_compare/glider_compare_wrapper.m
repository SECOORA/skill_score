clear all
clear global
clear objects


% 
addpath /home/om/matlab/data_hunter/nctoolbox/cdm
addpath /home/om/matlab/data_hunter/nctoolbox/cdm/utilities
addpath /home/hunter/roms/glider_comp/bin/
addpath /home/om/matlab/data_hunter/seawater
addpath /home/om/matlab/roms_wilkin
addpath /home/om/matlab/xml
javaaddpath('/home/om/matlab/classes/toolsUI-4.2.jar','-end')
oLog=logger('/home/hunter/roms/glider_comp/','GLIDER_MODEL');


% 
%addpath F:\om/matlab/data_hunter/nctoolbox/cdm
%addpath F:\om/matlab/data_hunter/nctoolbox/cdm/utilities
%addpath W:\roms/codar_comp/bin/
%addpath F:\om/matlab/data_hunter/seawater
%addpath F:\om/matlab/roms_wilkin
%addpath F:\om/matlab/xml
%javaaddpath('F:\om/matlab/classes/toolsUI-4.2.jar','-end')
%oLog=logger('W:\/roms/codar_comp/','CODAR_MODEL');


%MODELS={'NCOM','ESPRESSO','COAWST','NYHOPS','UMASSHOPS'}
%MODELS={'NCOM_R1','NCOM_US_E'}
%MODELS={'MERCATOR'}
%MODELS={'COAWST','NYHOPS'}
%MODELS={'UMASSHOPS','MERCATOR','NCOM_R1'}
MODELS={'MOCHA'}
info(oLog,'Creating the GLIDER data handler');
try
    oG=model_glider_compare_handler('/home/hunter/roms/glider_comp/MODEL_GLIDER_COMP.xml',MODELS,oLog);
   % oCODAR=model_codar_compare_handler('W:\roms/codar_comp/MODEL_CODAR_COMP_win.xml',MODELS);
catch ME
    error(oLog,ME);
    disp(['Error:' ME.message])
    for ie=1:length(ME.stack)
        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
    end
end


info(oLog,'Preprocesssing data')
try
    oG=preprocess(oG);
catch ME
    error(oLog,ME);
    disp(['Error:' ME.message])
    for ie=1:length(ME.stack)
        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
    end
end


% 
 info(oLog,'Aquiring data')
 try
     oG=acquire(oG);
 catch ME
     error(oLog,ME);
     disp(['Error:' ME.message])
     for ie=1:length(ME.stack)
         disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
     end
 end
 
 
 






%info(oLog,'Plot Some data')
%try
%   plot(oCODAR,5050);
%catch ME
%    error(oLog,ME);
%    disp(['Error:' ME.message])
%    for ie=1:length(ME.stack)
%        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
%    end
%end


exit







