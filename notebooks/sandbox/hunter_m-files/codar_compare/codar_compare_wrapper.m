clear all
clear global
clear objects

% Paths.
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/nctoolbox/cdm
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/nctoolbox/cdm/utilities
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/bin
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/seawater
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/roms_wilkin
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/xml
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/roms/utility
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/mexnc/
addpath /home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/toolboxes/snctools
javaaddpath('/home/filipe/Dropbox/REPOS/mymatlab/toolsUI-4.2.jar','-end')

oLog = logger('/home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/codar_compare', 'CODAR_MODEL');


%
%MODELS={'NCOM','ESPRESSO','COAWST','NYHOPS','UMASSHOPS'}
%MODELS={'NCOM_R1','NCOM_US_E'}
%MODELS={'MERCATOR'}
MODELS={'NYHOPS'}
MODELS={'UMASSHOPS'}
info(oLog,'Creating the CODAR data handler');

try
    oCODAR = model_codar_compare_handler('/home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/codar_compare/MODEL_CODAR_COMP.xml', MODELS, oLog);
catch ME
    error(oLog, ME);
    disp(['Error:' ME.message])
    for ie=1:length(ME.stack)
        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
    end
end

info(oLog, 'Aquiring data')

try
    oCODAR = acquire(oCODAR);
catch ME
    error(oLog,ME);
    disp(['Error:' ME.message])
    for ie=1:length(ME.stack)
        disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
    end
end



matlabpool close force
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

%exit
