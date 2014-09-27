classdef data_handler < handle
    %UNTITLED Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        xmlfile
        type
        DB_config
        starttime
        endtime
        tnc
    end
    
    methods
        function obj=data_handler(xmlfile,type) 
            error(nargchk(2,2,nargin,'struct'))
	        validateattributes(xmlfile,{'char'},{'vector'})
	        validateattributes(type,{'char'},{'vector'})
            
            obj.xmlfile=xmlfile;
            [obj.DB_config] = xml_read(xmlfile);
            obj.type=type;
            if isfield(obj.DB_config,'starttime')
                if strcmp(obj.DB_config.starttime,'NOW')
                    
                    obj.starttime=now;
                else
                    obj.starttime=datenum(obj.DB_config.starttime);
                end
            end
            
            if isfield(obj.DB_config,'endtime')
                if strcmp(obj.DB_config.endtime,'NOW')
                    
                    obj.endtime=now;
                else
                    obj.endtime=datenum(obj.DB_config.endtime);
                end
            end
        end
        
        function check_DB(obj)
        disp('Checking XML Database')
            direc=obj.DB_config.directory;
            platforms=obj.DB_config.platform;
            for i=1:length(platforms)
                ncfile=[direc platforms(i).ncfile];
                if  ~exist(ncfile,'file')
                    disp('NO FILE')
                else
                    disp('FILES EXISTS -  delete')
                    delete(ncfile)
                end
                
                create_netcdf_file(obj.DB_config,ncfile,platforms(i));
            end
		
		
            
        end
        function update_DB(obj)
            Pref.StructItem=false;
            xml_write(obj.xmlfile,obj.DB_config,'config',Pref);
        end
        function obj=acquire(obj,starttime,endtime) 
		disp('Acquiring data')
        obj.tnc=mDataset(obj.DB_config.source);
        
        end
        function process(obj) 
            
		disp('Processing  data')
        
        end
        function output(obj) 
        end
        function plot(obj)
        end
        function delete(obj)
            fclose all

        end
    end
    
end
function create_netcdf_file(DB_config,ncfile,platform)
import ucar.nc2.ncml.*
data=DB_config.netcdf;
% if isfield(platform.netcdf,'variable')
%     data.variable=[data.variable;platform.netcdf.variable];
% end
% if isfield(platform.netcdf,'dimension')
%     data.dimension=[data.dimension;platform.netcdf.dimension];
% end
% if isfield(platform.netcdf,'attribute')
%     data.attribute=[data.attribute;platform.netcdf.attribute];
% end
xml_write(DB_config.ncml_temp,data,'netcdf');
NcMLReader.writeNcMLToFile(DB_config.ncml_temp,ncfile)
end

