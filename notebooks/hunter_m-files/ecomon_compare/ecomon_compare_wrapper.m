clear all
clear global
clear objects


% 
% 
%addpath F:\om/matlab/data_hunter/nctoolbox/cdm
%addpath F:\om/matlab/data_hunter/nctoolbox/cdm/utilities
%addpath C:\work/roms/ecomon_compare/bin/
%addpath F:\om/matlab/data_hunter/seawater
%addpath F:\om/matlab/roms_wilkin
%addpath F:\om/matlab/xml
%javaaddpath('F:\om/matlab/classes/toolsUI-4.2.jar','-end')
%oLog=logger('C:\work/roms/ecomon_compare\','ECOMON_MODEL');


addpath /home/om/matlab/data_hunter/nctoolbox/cdm
addpath /home/om/matlab/data_hunter/nctoolbox/cdm/utilities
addpath /home/hunter/roms/ecomon_compare/bin/
addpath /home/om/matlab/data_hunter/seawater
addpath /home/om/matlab/roms_wilkin
addpath /home/om/matlab/xml
javaaddpath('/home/om/matlab/classes/toolsUI-4.2.jar','-end')
oLog=logger('/home/hunter/roms/ecomon_compare/' , 'ECOMON_MODEL');


MODELS={'MOCHA'}
info(oLog,'Creating the ECOMON data handler');
try
    %oG=model_ecomon_compare_handler('C:\work/roms/ecomon_compare/MODEL_ECOMON_COMP.xml',MODELS,oLog);
    oG=model_ecomon_compare_handler('/home/hunter/roms/ecomon_compare/MODEL_ECOMON_COMP.xml',MODELS,oLog);
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
% 
% % 
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
%  
 
 






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







