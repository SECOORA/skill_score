clear all
clear global
clear objects


addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/nctoolbox/cdm
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/nctoolbox/cdm/utilities
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/bin
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/seawater
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/roms_wilkin
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/xml
javaaddpath('/home/filipe/Dropbox/REPOS/mymatlab/toolsUI-4.2.jar','-end')

oLog = logger('~/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/glider_compare','GLIDER_MODEL');

%  MODELS={'NCOM','ESPRESSO','COAWST','NYHOPS','UMASSHOPS'}
%  MODELS={'NCOM_R1','NCOM_US_E'}
%  MODELS={'MERCATOR'}
%  MODELS={'COAWST','NYHOPS'}
%  MODELS={'UMASSHOPS','MERCATOR','NCOM_R1'}
MODELS = {'MOCHA'}
info(oLog, 'Creating the GLIDER data handler');
try
    oG=model_glider_compare_handler('/home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/glider_compare/MODEL_GLIDER_COMP.xml', MODELS, oLog);
catch ME
    error(oLog,ME);
    disp(['Error:' ME.message])
    for ie=1:length(ME.stack)
        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
    end
end


info(oLog, 'Preprocesssing data')
try
    oG = preprocess(oG);
catch ME
    error(oLog,ME);
    disp(['Error:' ME.message])
    for ie = 1:length(ME.stack)
        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
    end
end


 info(oLog, 'Aquiring data')
 try
     oG = acquire(oG);
 catch ME
     error(oLog,ME);
     disp(['Error:' ME.message])
     for ie=1:length(ME.stack)
         disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
     end
 end

%  info(oLog, 'Plot Some data')
%  try
%     plot(oCODAR, 5050);
%  catch ME
%      error(oLog, ME);
%      disp(['Error:' ME.message])
%      for ie = 1:length(ME.stack)
%          disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
%      end
%  end
exit
