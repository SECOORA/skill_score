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
javaaddpath('/home/filipe/Dropbox/REPOS/mymatlab/toolsUI-4.2.jar', '-end')

oLog = logger('/home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/ecomon_compare/' , 'ECOMON_MODEL');


MODELS={'MOCHA'}
info(oLog, 'Creating the ECOMON data handler');
try
    oG = model_ecomon_compare_handler('/home/filipe/IOOS/SECOORA/notebooks/sandbox/hunter_m-files/ecomon_compare/MODEL_ECOMON_COMP.xml', MODELS, oLog);
catch ME
    error(oLog,ME);
    disp(['Error:' ME.message])
    for ie = 1:length(ME.stack)
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

%exit
