classdef model_ecomon_compare_handler < data_handler
    %UNTITLED Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        MODELS
        olog
        lon
        lat
        time
        temp
        sal
        gdata
        nc
    end
    properties (SetAccess=private)
        
    end
    
    methods
        function obj=model_ecomon_compare_handler(xmlfile,MODELS,olog)
            obj = obj@data_handler(xmlfile,'NONE');
            obj.MODELS=MODELS;
            obj.olog=olog;
            if isfield(obj.DB_config,'starttime')
                if strcmp(obj.DB_config.starttime,'NOW')
                    
                    obj.starttime=now-1;
                else
                    obj.starttime=datenum(obj.DB_config.starttime);
                end
            end
            
            
        end
        function obj=check_DB(obj)
            
            
            disp('Checking DB')
            
        end
        function obj=preprocess(obj)
            dt=obj.DB_config.dt/24;
            disp('Processing ECOMON data')
            deployments=obj.DB_config.deploy;
            direc=obj.DB_config.directory
            data=load(fullfile(direc,deployments))
            
            obj.gdata.time=data.time;
            obj.gdata.lat=data.lat;
            obj.gdata.lon=data.lon;
            obj.gdata.salt=data.salt;
            obj.gdata.temp=data.temp;
            obj.gdata.depth=data.depth;
            
            
            
            %figure(4)
            %EC_map
            %hold on
            %plot([obj.gdata.lon],[obj.gdata.lat],'r+')
            %hold off
            
            
        end
        function obj=acquire(obj)
            
            disp('Acquiring GLIDER data')
            direc=obj.DB_config.directory;
            stime=obj.starttime;
            etime=obj.endtime;
            
            info(obj.olog,['Processing from ' datestr(stime) '-' datestr(etime)]);
            for iM=1:length(obj.MODELS)
                gdata=obj.gdata;
                obj.MODELS
                for iD=1:length(obj.gdata)
                    
                    
                    
                    if isfield(obj.DB_config,obj.MODELS{iM})
                        mname=obj.MODELS{iM};
                        disp(['Processing Model - ' mname])
                        info(obj.olog,['Processing Model - ' mname ]);
                        grid=obj.DB_config.(mname).grid;
                        
                        url=[obj.DB_config.directory  '/' obj.DB_config.(mname).nc];
                        
                        if strcmp(mname,'COAWST') | strcmp(mname,'HYCOM') | strcmp(mname,'UMASSHOPS') ...
                                | strcmp(mname,'NYHOPS') | strcmp(mname,'MOCHA') ...
                                | strcmp(mname,'ESPRESSO') | strcmp(mname,'MERCATOR')  | strcmp(mname,'NCOM_R1')
                            url=obj.DB_config.(mname).url;
                        end
                        
                        nc=ncgeodataset(url);
                        ofile=[direc 'SAL_TEMP_ECOMON_2011_' obj.MODELS{iM}];
                        switch grid
                            case 'A'
                                [salt_mod temp_mod]=acquire_a(obj,iD,mname,nc);
                                %
                            case 'C'
                                [salt_mod temp_mod]=acquire_c(obj,iD,mname,nc);
                                %
                            case 'UMASSHOPS'
                                [salt_mod temp_mod]=acquire_umass(obj,iD,mname,nc);
                            case 'NYHOPS'
                                [salt_mod temp_mod]=acquire_nyhops(obj,iD,mname,nc);
                            case 'HYCOM'
                                [salt_mod temp_mod]=acquire_hycom(obj,iD,mname,nc);
                            case 'MOCHA'
                                [salt_mod temp_mod]=acquire_mocha(obj,iD,mname,nc);
                                %
                            otherwise
                                disp('GRID NOT RECOGNIZED')
                                continue
                        end
                        
                        gdata(iD).mtemp=temp_mod;
                        gdata(iD).msalt=salt_mod;
                        
                    else
                        disp('MODEL NOT IN DATABASE')
                    end
                    
                    
                end
                save(ofile,'gdata')
                
            end
            
        end
        function obj=process(obj)
            
            disp('Processing  data')
        end
        function output(obj)
            
            
            disp('Output  data')
        end
        function plot(obj,ind)
            disp('Plot Data')
            tu=obj.cu(ind,:)';
            tv=obj.cv(ind,:)';
            tlon=obj.clon;
            tlat=obj.clat;
            ttime=obj.ctime(ind);
            
            dt=abs(ttime-obj.time);
            [mint, imn]=min(dt)
            [lon lat]=meshgrid(obj.lon,obj.lat);
            
            u=squeeze(obj.u(imn,:,:,:));
            v=squeeze(obj.v(imn,:,:,:));
            
            %figure(1)
            %set(gcf,'renderer','zbuffer')
            %EC_map
            %hold on
            %quiver3(lon(:),lat(:),zeros(size(lon(:))),u(:),v(:),zeros(size(lon(:))),10,'k')
            %hold on
            
            %quiver3(tlon,tlat,zeros(size(tlon)),tu,tv,zeros(size(tlon)),1,'r')
            %hold off
            %hold off
            %title(datestr(ttime))
            %xlabel(datestr(obj.time(imn)))
            
            
            
            
        end
    end
end

%%
function [salt temp]=acquire_a(obj,iD,mname,nc,s)
disp('Acquiring A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);


salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;

dt=obj.DB_config.(mname).dt/(24);

grid=snc.grid_interop(:,:,:,:);


dlat=1;
dlon=1;

for il=1:length(gdata.time)
    
    ctime=gdata.time(il);
    s.lat=[gdata.lat(il)-dlat gdata.lat(il)+dlat];
    s.lon=[gdata.lon(il)-dlon gdata.lon(il)+dlon];
    sstime=gdata.time(il)-dt;
    setime=gdata.time(il)+dt;
    s.time={datestr(sstime) datestr(setime)};
    
    try
        tic
        ssnc=snc.geosubset(s);
        stnc=tnc.geosubset(s);
        toc
    catch ME
        disp(['Error:' ME.message])
        for ie=1:length(ME.stack)
            disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
        end
        disp('ERROR getting data')
    end
    
    grid=ssnc.grid(:,:,:,:)
    nsalt=ssnc.data(:,:,:,:);
    ntemp=stnc.data(:,:,:,:);
    [glon,glat]=meshgrid(grid.lon,grid.lat);
    mtime=grid.time;
    mdep=grid.z;
    
    if length(mtime)<2
        disp('Not enough data found')
        
        continue
    end
    
    
    dtime=abs(mtime-ctime);
    w=1./dtime;
    
    ts=squeeze((w(1).*nsalt(1,:,:,:)+w(2).*nsalt(2,:,:,:))/sum(w));
    tt=squeeze((w(1).*ntemp(1,:,:,:)+w(2).*ntemp(2,:,:,:))/sum(w));
    
    warning off
    zs=double(mdep*nan);
    zt=double(mdep*nan);
    for iz=1:length(mdep)
        
        zs(iz)=interp2(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(il),gdata.lat(il));
        zt(iz)=interp2(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(il),gdata.lat(il));
        
        
    end
    
    disp(il)
    
    
    salt(:,il)=interp1(abs(mdep),zs,abs(gdata.depth));
    temp(:,il)=interp1(abs(mdep),zt,abs(gdata.depth));
end


%
%
%end

%
%
%




end
%%
function [salt temp]=acquire_c(obj,iD,mname,nc)
disp('Acquiring C GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);
dt=(obj.DB_config.(mname).dt)/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;

grid=snc.grid_interop(:,:,:,:)


dlat=1;
dlon=1;

for il=1:length(gdata.time)
    
    ctime=gdata.time(il);
    s.lat=[gdata.lat(il)-dlat gdata.lat(il)+dlat];
    s.lon=[gdata.lon(il)-dlon gdata.lon(il)+dlon];
    sstime=gdata.time(il)-dt;
    setime=gdata.time(il)+dt;
    s.time={datestr(sstime) datestr(setime)};
    disp(s)
    try
        tic
        ssnc=snc.geosubset(s);
        stnc=tnc.geosubset(s);
        toc
    catch
        disp('ERROR getting data')
        continue
    end
    
    grid=ssnc.grid(:,:,:,:)
    nsalt=double(ssnc.data(:,:,:,:));
    ntemp=double(stnc.data(:,:,:,:));
    
    
    glon=grid.lon;
    glat=grid.lat;
    
    mtime=grid.time;
    
    mdep=grid.z;
    zdim=size(mdep)
    
    if length(mtime)<2 | zdim(2)<4  
        disp('Not enough data found')
        
        continue
    end
    
    
    
    dtime=abs(mtime-ctime);
    w=1./dtime;
    
    ts=squeeze((w(1).*nsalt(1,:,:,:)+w(2).*nsalt(2,:,:,:))/sum(w));
    tt=squeeze((w(1).*ntemp(1,:,:,:)+w(2).*ntemp(2,:,:,:))/sum(w));
    
    
    zs=nan(zdim(1),1);
    zt=nan(zdim(1),1);
    zd=nan(zdim(1),1);
    
            
    for iz=1:zdim(1)
        zs(iz)=griddata(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(il),gdata.lat(il));
        zt(iz)=griddata(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(il),gdata.lat(il));
        zd(iz)=griddata(double(glon),double(glat),squeeze(mdep(iz,:,:)),gdata.lon(il),gdata.lat(il));

    end
    
    
    valid = ~any(isnan([zd zs]),2);
    
    if length(find(valid))<2
        [abs(zd(valid)) zs(valid) zt(valid)]
        disp('NOT ENOUGH BINS')
        continue
    end
     salt(:,il)=interp1(abs(zd),zs,abs(gdata.depth));
     temp(:,il)=interp1(abs(zd),zt,abs(gdata.depth));
     warning on
end

%

%
% s.lat=[min(gdata.lat(:))-dlat-0.05 max(gdata.lat(:))+dlat+0.05];
% s.lon=[min(gdata.lon(:))-dlon-0.05  max(gdata.lon(:))+dlon+0.05];
%
% sstime=min(gdata.time)-dt;
% setime=max(gdata.time)+dt;
% s.time={datestr(sstime) datestr(setime)};
%
% try
%     tic
%     ssnc=snc.geosubset(s);
%     stnc=tnc.geosubset(s);
%     toc
% catch
%     disp('ERROR getting data')
% end
%
% grid=ssnc.grid(:,:,:,:)
% tsalt=double(ssnc.data(:,:,:,:));
% ttemp=double(stnc.data(:,:,:,:));
%
%
% glon=grid.lon;
% glat=grid.lat;
%
% mtime=grid.time;
% tic
% mdep=grid.z;
% zdim=size(mdep);
% %
% for it=1:length(gdata.time)
%     disp([datestr(gdata.time(it)) '-' datestr(max(gdata.time))])
%     Imatch=find(mtime==gdata.time(it));
%     if ~isempty(Imatch)
%
%         ts=squeeze(tsalt(Imatch,:,:,:));
%         tt=squeeze(ttemp(Imatch,:,:,:));
%     else
%         continue
%     end
%
%
%
%
%     [gdata.lon(it) gdata.lat(it)]
%     warning off
%     zs=nan(zdim(1),1);
%     zt=nan(zdim(1),1);
%     zd=nan(zdim(1),1);
%     for iz=1:zdim(1)
%         %squeeze(ts(iz,:,:))
%         %double(glon)
%         %double(glat)
%         zs(iz)=griddata(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(it),gdata.lat(it));
%
%
%         zt(iz)=griddata(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(it),gdata.lat(it));
%         zd(iz)=griddata(double(glon),double(glat),squeeze(mdep(iz,:,:)),gdata.lon(it),gdata.lat(it));
%
%
%         %plot(double(glon),double(glat),'k+',gdata.lon(it),gdata.lat(it),'ro')
%         %pause
%     end
%     [zd zt zs]
%     salt(:,it)=interp1(abs(zd),zs,abs(gdata.depth));
%     temp(:,it)=interp1(abs(zd),zt,abs(gdata.depth));
%     warning on
%
%     %
%     %
% end
%          toc
% %

end
%%
function [salt temp]=acquire_umass(obj,iD,mname,nc)

disp('Acquiring UMASS A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);
dnc=nc.variable(obj.DB_config.(mname).depth);


dt=obj.DB_config.(mname).dt/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;



grid=snc.grid_interop(:,:,:,:);

grid
dlat=1;
dlon=1;


%for il=1:length(gdata.time)
for il=190:length(gdata.time)
    
    ctime=gdata.time(il);
    s.lat=[gdata.lat(il)-dlat gdata.lat(il)+dlat];
    s.lon=[gdata.lon(il)-dlon gdata.lon(il)+dlon];
    sstime=gdata.time(il)-dt;
    setime=gdata.time(il)+dt;
    s.time={datestr(sstime) datestr(setime)};
    disp(s)
    tic
    [r1 r2 c1 c2]=geoij(tnc,s);
    rho_dims=size(grid.lon);

    %if r1==1;r1=3;end
    %if c1==1;c1=3;end
    %if r2==rho_dims(1);r2=r2-2;end
    %if c2==rho_dims(1);c2=c2-2;end
    
    
    disp('getting lonlat')
    glon=grid.lon(r1:r2,c1:c2);
    glat=grid.lat(r1:r2,c1:c2);
    
    tw=tnc.timewindowij(sstime,setime);
    size(tw)
    %2009-05-11T00:00:00Z" 
    disp('getting data')
    if isempty(tw.index) | length(tw.index)<2
        disp('not enough times in range')
        continue
    end
    nsalt=double(snc.data(tw.index,r1:r2,c1:c2,:));
    ntemp=double(tnc.data(tw.index,r1:r2,c1:c2,:));

    ndep=double(dnc.data(:,r1:r2,c1:c2));
    size(ndep)
    datestr(tw.time)
    mtime=tw.time;
    dtime=abs(mtime-ctime);
    w=1./dtime;
    
    ts=squeeze((w(1).*nsalt(1,:,:,:)+w(2).*nsalt(2,:,:,:))/sum(w));
    tt=squeeze((w(1).*ntemp(1,:,:,:)+w(2).*ntemp(2,:,:,:))/sum(w));
    td=ndep;
    size(td)

    toc
    mtime=grid.time(tw.index);
 
    mdep=grid.z;
    zdim=size(td);
    disp(zdim)
    
    warning off
    zs=nan(zdim(1),1);
    zt=nan(zdim(1),1);
    zd=nan(zdim(1),1);
    for iz=1:zdim(1)
        
        zs(iz)=griddata(double(glon),double(glat),squeeze(ts(:,:,iz)),gdata.lon(il),gdata.lat(il));
        zt(iz)=griddata(double(glon),double(glat),squeeze(tt(:,:,iz)),gdata.lon(il),gdata.lat(il));
        zd(iz)=griddata(double(glon),double(glat),squeeze(td(iz,:,:)),gdata.lon(il),gdata.lat(il));
        
        
    end
    
    valid = ~any(isnan([zd zs]),2);
    
    if length(find(valid))<2
        [abs(zd(valid)) zs(valid) zt(valid)]
        disp('NOT ENOUGH BINS')
        continue
    end
    salt(:,il)=interp1(abs(zd),zs,abs(gdata.depth));
    temp(:,il)=interp1(abs(zd),zt,abs(gdata.depth));
    warning on
    
    %
    %
end

end
%%
function [salt temp]=acquire_nyhops(obj,iD,mname,nc)
disp('Acquiring NYHOPS A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);


salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;


dt=obj.DB_config.(mname).dt/(24);

grid=snc.grid_interop(:,:,:,:);


dlat=1;
dlon=1;

for il=1:length(gdata.time)
    
    ctime=gdata.time(il);
    s.lat=[gdata.lat(il)-dlat gdata.lat(il)+dlat];
    s.lon=[gdata.lon(il)-dlon gdata.lon(il)+dlon];
    sstime=gdata.time(il)-dt;
    setime=gdata.time(il)+dt;
    s.time={datestr(sstime) datestr(setime)};
    
    try
        tic
        ssnc=snc.geosubset(s);
        stnc=tnc.geosubset(s);
        toc
    catch ME
        disp(['Error:' ME.message])
        for ie=1:length(ME.stack)
            disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
        end
        disp('ERROR getting data')
        continue
    end
    
    
    grid=ssnc.grid(:,:,:,:)
    nsalt=double(ssnc.data(:,:,:,:));
    ntemp=double(stnc.data(:,:,:,:));
    
    glon=grid.lon;
    glat=grid.lat;
    
    mtime=grid.time;
    tic
    mdep=grid.z;
    zdim=size(mdep);
    if length(mtime)<2 | length(glon) < 4
        disp('Not enough data found')
        
        continue
    end
    
    
    
    dtime=abs(mtime-ctime);
    w=1./dtime;
    
    ts=squeeze((w(1).*nsalt(1,:,:,:)+w(2).*nsalt(2,:,:,:))/sum(w));
    tt=squeeze((w(1).*ntemp(1,:,:,:)+w(2).*ntemp(2,:,:,:))/sum(w));
        
        %size(ts)
        warning off
        zs=nan(zdim(1),1);
        zt=nan(zdim(1),1);
        zd=nan(zdim(1),1);
        for iz=1:zdim(1)
            
            zs(iz)=griddata(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(il),gdata.lat(il));
            
            
            zt(iz)=griddata(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(il),gdata.lat(il));
            zd(iz)=griddata(double(glon),double(glat),squeeze(mdep(iz,:,:)),gdata.lon(il),gdata.lat(il));
            
            
        end
        
        disp(il)
        disp([zd zt zs])
            valid = ~any(isnan([zd zs]),2);
            
            if length(find(valid))<2
                [abs(zd(valid)) zs(valid) zt(valid)]
                disp('NOT ENOUGH BINS')
                continue
            end
            
        salt(:,il)=interp1(abs(zd),zs,abs(gdata.depth));
        temp(:,il)=interp1(abs(zd),zt,abs(gdata.depth));
 
        warning on
        
        %
        %
    end
    toc
    %
    
    
    
end
%%
    function [salt temp]=acquire_hycom(obj,iD,mname,nc)
        disp('Acquiring HYCOM A GRID')
        
        gdata=obj.gdata(iD);
        snc=nc.geovariable(obj.DB_config.(mname).salt);
        tnc=nc.geovariable(obj.DB_config.(mname).temp);
        dnc=nc.geovariable(obj.DB_config.(mname).depth);
        
        dt=(24)/(24);
        
        salt=gdata.salt*nan;
        temp=gdata.temp*nan;
        ind=1;
        
        grid=snc.grid_interop(:,:,:,:);
        
        dlat=1;
        dlon=1;
        
        for il=1:length(gdata.time)
            ctime=gdata.time(il);
            s.lat=[gdata.lat(il)-dlat gdata.lat(il)+dlat];
            s.lon=[gdata.lon(il)-dlon gdata.lon(il)+dlon];
            sstime=gdata.time(il)-dt;
            setime=gdata.time(il)+dt;
            s.time={datestr(sstime) datestr(setime)};
            %disp(s)
            
            
            try
                tic
                ssnc=snc.geosubset(s);
                stnc=tnc.geosubset(s);
                sdnc=dnc.geosubset(s);
                toc
            catch ME
                disp(['Error:' ME.message])
                for ie=1:length(ME.stack)
                    disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
                end
                disp('ERROR getting data')
            end
            
            grid=ssnc.grid(:,:,:,:);
            nsalt=ssnc.data(:,:,:,:);
            ntemp=stnc.data(:,:,:,:);
            ndep=sdnc.data(:,:,:,:);
            [glon,glat]=meshgrid(grid.lon,grid.lat);
            mtime=grid.time;
            mdep=grid.z;
            
            dtime=abs(mtime-ctime);
            w=1./dtime;
            
            ts=squeeze((w(1).*nsalt(1,:,:,:)+w(2).*nsalt(2,:,:,:))/sum(w));
            tt=squeeze((w(1).*ntemp(1,:,:,:)+w(2).*ntemp(2,:,:,:))/sum(w));
            td=squeeze((w(1).*ndep(1,:,:,:)+w(2).*ndep(2,:,:,:))/sum(w));
            size(ts)
            
            warning off
            zs=double(mdep*nan);
            zt=double(mdep*nan);
            zd=double(mdep*nan);
            
            for iz=1:length(mdep)
                
                zs(iz)=interp2(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(il),gdata.lat(il));
                zt(iz)=interp2(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(il),gdata.lat(il));
                zd(iz)=interp2(double(glon),double(glat),squeeze(td(iz,:,:)),gdata.lon(il),gdata.lat(il));
                
                
            end
            
            disp(il)
            valid = ~any(isnan([zd zs]),2);
            
            if length(find(valid))<2
                [abs(zd(valid)) zs(valid) zt(valid)]
                disp('NOT ENOUGH BINS')
                continue
            end
            
            salt(:,il)=interp1(abs(zd(valid)),zs(valid),abs(gdata.depth));
            temp(:,il)=interp1(abs(zd(valid)),zt(valid),abs(gdata.depth));
            
        end
        
        %
        %
        % tic
        %
        % %
        % for it=1:length(gdata.time)
        %
        %     Imatch=find(mtime==gdata.time(it));
        %     if ~isempty(Imatch)
        %
        %         ts=squeeze(tsalt(Imatch,:,:,:));
        %         tt=squeeze(ttemp(Imatch,:,:,:));
        %         td=squeeze(tdep(Imatch,:,:,:));
        %     else
        %         continue
        %     end
        %
        %
        %
        %
        %
        %     for gi=1:length(grid.lon)
        %         for gj=1:length(grid.lat)
        %             tmps=ts(:,gj,gi);
        %             tmpt=tt(:,gj,gi);
        %
        %             lastone=max(find(isfinite(tmps)));
        %             tmps(lastone+1:end)=tmps(lastone);
        %
        %             lastone=max(find(isfinite(tmpt)));
        %             tmpt(lastone+1:end)=tmpt(lastone);
        %
        %
        %             ts(:,gj,gi)=tmps;
        %             tt(:,gj,gi)=tmpt;
        %
        %         end
        %     end
        %
        %
        %     warning off
        %     [zd Ia]=unique(zd);
        %     zs=zs(Ia);
        %     zt=zt(Ia);
        %     zt=zt(isfinite(zd));
        %     zs=zs(isfinite(zd));
        %     zd=zd(isfinite(zd));
        %     if length(zd)<2
        %         continue
        %     end
        %     warning off
        %     salt(:,it)=interp1(abs(zd),zs,abs(gdata.depth));
        %     temp(:,it)=interp1(abs(zd),zt,abs(gdata.depth));
        %     salt(isnan(gdata.salt(:,it)),it)=nan;
        %     temp(isnan(gdata.temp(:,it)),it)=nan;
        %
        %
        %     warning on
        %
        % end
        %          toc
        
        
        
    end
    
    %%
    function [salt temp]=acquire_mocha(obj,iD,mname,nc)
disp('Acquiring MOCHA A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt)
tnc=nc.geovariable(obj.DB_config.(mname).temp)


salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;


dt=obj.DB_config.(mname).dt/(24);

grid=snc.grid_interop(:,:,:,:);

dlat=1;
dlon=1;
 
 for il=1:length(gdata.time)
     tic
     ctime=gdata.time(il);
     s.lat=[gdata.lat(il)-dlat gdata.lat(il)+dlat];
     s.lon=[gdata.lon(il)-dlon gdata.lon(il)+dlon];
     sstime=gdata.time(il)-dt;
     setime=gdata.time(il)+dt;
     s.time={datestr(sstime) datestr(setime)};
     
     try
         
         ssnc=snc.geosubset(s);
         stnc=tnc.geosubset(s);
         
     catch ME
         disp(['Error:' ME.message])
         for ie=1:length(ME.stack)
             disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
         end
         disp('ERROR getting data')
         continue
     end
     
     
     grid=ssnc.grid(:,:,:,:);
     nsalt=double(ssnc.data(:,:,:,:));
     ntemp=double(stnc.data(:,:,:,:));
%     
     glon=grid.lon;
     glat=grid.lat;
%     
     mtime=grid.time;
%     tic
     mdep=grid.depth;
     zdim=size(mdep);
     if length(mtime)<2 | length(glon) < 4
         disp('Not enough data found')
         datestr(grid.time)
         datestr(sstime)
         datestr(setime)
         continue
     end
%     
 
    

        dtime=mtime-ctime;
        Itop=find(dtime>0);
        Ibot=find(dtime<0);
        
        
        if isempty(Itop) | isempty(Ibot)
            disp('BAD POINT. DATA MISSING ON ONE SIDE')
       continue
        
        end
        
        t1=Itop(1);
        t2=Ibot(end);
        datestr(mtime(t2))
        datestr(ctime)
        datestr(mtime(t1))
        
     dtime=abs(mtime-ctime);
     w=1./dtime;
     size(w)
     ts=squeeze((w(t1).*nsalt(t1,:,:,:)+w(t2).*nsalt(t2,:,:,:))/sum(w));
     tt=squeeze((w(t1).*ntemp(t1,:,:,:)+w(t2).*ntemp(t2,:,:,:))/sum(w));
%         
%         %size(ts)
         warning off
         zs=nan(zdim(1),1);
         zt=nan(zdim(1),1);
         zd=nan(zdim(1),1);
         for iz=1:zdim(1)
             
             zs(iz)=griddata(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(il),gdata.lat(il));
             
             
             zt(iz)=griddata(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(il),gdata.lat(il));
             
             
         end
%         
%         disp(il)
%        disp([ zt zs])
      %       valid = ~any(isnan([zt zs]),2);
      %       zd=
      %       if length(find(valid))<2
      %           [abs(zd(valid)) zs(valid) zt(valid)]
      %           disp('NOT ENOUGH BINS')
      %           continue
      %       end
%             

         salt(:,il)=interp1(abs(mdep),zs,abs(gdata.depth));
         temp(:,il)=interp1(abs(mdep),zt,abs(gdata.depth));
        
%  
%         warning on
%         
%         %
%         %
toc
     end
%     toc
%     %
%     
    
    
end

