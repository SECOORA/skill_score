classdef logger < handle
%  UNTITLED Summary of this class goes here
%  Detailed explanation goes here

    properties
        direc
        prefix
    end

    methods
        function obj=logger(direc,prefix)
            error(nargchk(2,2,nargin,'struct'))
            validateattributes(direc,{'char'},{'vector'})
            validateattributes(prefix,{'char'},{'vector'})

            obj.direc=direc;
            obj.prefix=prefix;
        end

        function obj=info(obj,infostr)

            validateattributes(infostr,{'char'},{'vector'});
            file=[obj.direc obj.prefix '_process.log'];
           [ret,name]=system('hostname');
       name=deblank(name);
        % if ispc
           %     name=getenv('COMPUTERNAME');
           % else
           %     name=getenv('HOSTNAME');
           % end
            fid=fopen(file,'a+');
            fprintf(fid,'INF0: %s : %s : %s \n',name, datestr(now),infostr);
            fclose(fid);
        end



        function obj=error(obj,ME)

            file=[obj.direc obj.prefix '_process.log'];
       [ret,name]=system('hostname');
       name=deblank(name);
           % if ispc
           %     name=getenv('COMPUTERNAME');
           % else
           %     name=getenv('HOSTNAME');
           % end

            fid=fopen(file,'a+');
            fprintf(fid,'ERROR: %s : %s : %s \n',name, datestr(now),ME.message);

            for ie=1:length(ME.stack)

                fprintf(fid,'ERROR: %s : %s : %s \n',name, datestr(now),...
                    [ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ]);

            end
            fclose(fid);
        end
    end
end
