classdef model_glider_compare_handler < data_handler
%  UNTITLED Summary of this class goes here
%  Detailed explanation goes here
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
        function obj=model_glider_compare_handler(xmlfile,MODELS,olog)
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
            disp('Processing Glider data')
            deployments=obj.DB_config.deploy;
            for id=1:length(deployments)
                disp(id)
                deployments{id}
                url=[obj.DB_config.glider_url deployments{id} '.nc'];
                omatfile=[obj.DB_config.directory deployments{id}  '/' deployments{id} '.mat'];

                nc=ncgeodataset(url);
                gvar=nc.variable('salinity');
                tsalt=gvar.data{:};
                gvar=nc.variable('temperature');
                ttemp=gvar.data{:};
                gvar=nc.variable('time');
                ttime=gvar.data{:};
                gvar=nc.variable('depth');
                tdepth=gvar.data{:};
                gvar=nc.variable('longitude');
                tlon=gvar.data{:};
                gvar=nc.variable('latitude');
                tlat=gvar.data{:};


                ntime=[ceil(min(ttime)):dt:floor(max(ttime))];


                mlat=[];
                mlon=[];
                mtemp=[];
                msalt=[];
                for it=1:length(ntime);
                    Ip=find(ttime>=ntime(it)-dt & ttime<=ntime(it)+dt);

                    if length(Ip)>1
                        mlat(it)=nanmean(tlat(Ip));
                        mlon(it)=nanmean(tlon(Ip));

                        msalt(:,it)=nanmean(tsalt(Ip,:));
                        mtemp(:,it)=nanmean(ttemp(Ip,:));
                    else
                        mlat(it)=nan;
                        mlon(it)=nan;
                        msalt(:,it)=nan;
                        mtemp(:,it)=nan;

                    end

                end
                mlon(isnan(mlat))=[];
                mtemp(:,isnan(mlat))=[];
                msalt(:,isnan(mlat))=[];
                ntime(isnan(mlat))=[];
                mlat(isnan(mlat))=[];


                %                 figure(1)
                %                 EC_map
                %                 hold on
                %                 plot(tlon,tlat,'r*',mlon,mlat,'k*')
                %                 hold off
                %
                %                 figure(2)
                %                 subplot(2,1,1)
                %                 pcolor(ttime,tdepth,ttemp')
                %                 shading flat
                %                 colorbar
                %                 subplot(2,1,2)
                %                 pcolor(ntime,tdepth,mtemp)
                %                 shading flat
                %                 colorbar
                %
                %
                %                 figure(3)
                %                 subplot(2,1,1)
                %                 pcolor(ttime,tdepth,tsalt')
                %                 shading flat
                %                 colorbar
                %                 subplot(2,1,2)
                %                 pcolor(ntime,tdepth,msalt)
                %                 shading flat
                %                 colorbar
                %

                dlat=diff(mlat)*60*1853;
                dlon=diff(mlon)*60*1853.*cos(mlat(1:end-1)*pi/180);

                dx=sqrt(dlat.^2+dlon.^2);


                %figure(1)
                %EC_map
                %hold on
                %plot(mlon,mlat,'r+')
                %hold off

                %figure(2)
                %hist(dx,100)
                %drawnow
                %pause
                obj.gdata(id).time=ntime+datenum(2006,1,1);
                obj.gdata(id).lat=mlat;
                obj.gdata(id).lon=mlon;
                obj.gdata(id).salt=msalt;
                obj.gdata(id).temp=mtemp;
                obj.gdata(id).depth=tdepth;
                obj.gdata(id).dist=dx;
                obj.gdata(id).name=deployments{id};


                save(omatfile,'ntime','mlon','mlat','msalt','mtemp','tdepth','dx')

            end


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
                        disp(['Processing Model - ' mname ',' obj.gdata(iD).name])
                        info(obj.olog,['Processing Model - ' mname ',' obj.gdata(iD).name]);
                        grid=obj.DB_config.(mname).grid;

                        url=[obj.DB_config.directory  obj.gdata(iD).name '/' obj.DB_config.(mname).nc];

                        if strcmp(mname,'COAWST') | strcmp(mname,'HYCOM') | strcmp(mname,'UMASSHOPS') ...
                                 | strcmp(mname,'NYHOPS') | strcmp(mname,'MOCHA') ...
                                 | strcmp(mname,'ESPRESSO') | strcmp(mname,'MERCATOR')  | strcmp(mname,'NCOM_R1')
                            url=obj.DB_config.(mname).url;
                        end

                        nc=ncgeodataset(url);
                        ofile=[direc 'SAL_TEMP_extr_' obj.MODELS{iM}];
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


function [salt temp]=acquire_a(obj,iD,mname,nc,s)
disp('Acquiring A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);

dt=(obj.DB_config.dt/2)/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;

grid=snc.grid_interop(:,:,:,:);

dlat=abs(max(diff(grid.lat)));
dlon=abs(max(diff(grid.lon)));
s.lat=[min(gdata.lat(:))-dlat max(gdata.lat(:))+dlat];
s.lon=[min(gdata.lon(:))-dlon max(gdata.lon(:))+dlon];

sstime=min(gdata.time)-dt;
setime=max(gdata.time)+dt;
It=find(grid.time>=sstime & grid.time<=setime);

if isempty(It)
    return
end


s.time={datestr(sstime) datestr(setime)};



try
    tic
    ssnc=snc.geosubset(s);
    stnc=tnc.geosubset(s);
    toc
catch
    disp('ERROR getting data')
end

grid=ssnc.grid(:,:,:,:);
tsalt=ssnc.data(:,:,:,:);
ttemp=stnc.data(:,:,:,:);

[glon,glat]=meshgrid(grid.lon,grid.lat);
mtime=grid.time;
mdep=double(grid.z);
tic
%
for it=1:length(gdata.time)

    Imatch=find(mtime==gdata.time(it));
    if ~isempty(Imatch)


        ts=squeeze(tsalt(Imatch,:,:,:));
        tt=squeeze(ttemp(Imatch,:,:,:));
    else
        continue
    end


    for gi=1:length(grid.lon)
        for gj=1:length(grid.lat)
            tmps=ts(:,gj,gi);
            tmpt=tt(:,gj,gi);

            lastone=max(find(isfinite(tmps)));
            tmps(lastone+1:end)=tmps(lastone);

            lastone=max(find(isfinite(tmpt)));
            tmpt(lastone+1:end)=tmpt(lastone);


            ts(:,gj,gi)=tmps;
            tt(:,gj,gi)=tmpt;

        end
    end

    zs=double(mdep*nan);
    zt=double(mdep*nan);
    lastbin=max(abs(gdata.depth(isfinite(gdata.temp(:,it)))));
    Iinterp=find(abs(mdep)<abs(lastbin));

    for iz=Iinterp'

        zs(iz)=interp2(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(it),gdata.lat(it));
        zt(iz)=interp2(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(it),gdata.lat(it));


    end

    warning off


    salt(:,it)=interp1(abs(mdep),zs,abs(gdata.depth));
    temp(:,it)=interp1(abs(mdep),zt,abs(gdata.depth));
    warning on
    %
    %
end
         toc
%
%
%




end
function [salt temp]=acquire_c(obj,iD,mname,nc)
disp('Acquiring C GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt)
tnc=nc.geovariable(obj.DB_config.(mname).temp)
dt=(obj.DB_config.dt/2)/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;

methods(snc)
grid=snc.grid_interop(:,:,:,:)


dlat=max([max(max(abs(diff(grid.lat)))) max(max(abs(diff(grid.lat'))))]);
dlon=max([max(max(abs(diff(grid.lon)))) max(max(abs(diff(grid.lon'))))]);




s.lat=[min(gdata.lat(:))-dlat-0.05 max(gdata.lat(:))+dlat+0.05];
s.lon=[min(gdata.lon(:))-dlon-0.05  max(gdata.lon(:))+dlon+0.05];

sstime=min(gdata.time)-dt;
setime=max(gdata.time)+dt;
s.time={datestr(sstime) datestr(setime)};

try
    tic
    ssnc=snc.geosubset(s);
    stnc=tnc.geosubset(s);
    toc
catch
    disp('ERROR getting data')
end

grid=ssnc.grid(:,:,:,:)
tsalt=double(ssnc.data(:,:,:,:));
ttemp=double(stnc.data(:,:,:,:));


glon=grid.lon;
glat=grid.lat;

mtime=grid.time;
tic
mdep=grid.z;
zdim=size(mdep);
%
for it=1:length(gdata.time)
    disp([datestr(gdata.time(it)) '-' datestr(max(gdata.time))])
    Imatch=find(mtime==gdata.time(it));
    if ~isempty(Imatch)

        ts=squeeze(tsalt(Imatch,:,:,:));
        tt=squeeze(ttemp(Imatch,:,:,:));
    else
        continue
    end




    [gdata.lon(it) gdata.lat(it)]
    warning off
    zs=nan(zdim(1),1);
    zt=nan(zdim(1),1);
    zd=nan(zdim(1),1);
    for iz=1:zdim(1)
        %squeeze(ts(iz,:,:))
        %double(glon)
        %double(glat)
        zs(iz)=griddata(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(it),gdata.lat(it));


        zt(iz)=griddata(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(it),gdata.lat(it));
        zd(iz)=griddata(double(glon),double(glat),squeeze(mdep(iz,:,:)),gdata.lon(it),gdata.lat(it));


        %plot(double(glon),double(glat),'k+',gdata.lon(it),gdata.lat(it),'ro')
        %pause
    end
    [zd zt zs]
    salt(:,it)=interp1(abs(zd),zs,abs(gdata.depth));
    temp(:,it)=interp1(abs(zd),zt,abs(gdata.depth));
    warning on

    %
    %
end
         toc
%

end
function [salt temp]=acquire_umass(obj,iD,mname,nc)

disp('Acquiring UMASS A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);
dnc=nc.variable(obj.DB_config.(mname).depth);

 dt=(obj.DB_config.dt/2)/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;



grid=snc.grid_interop(:,:,:,:);


dlat=max([max(max(abs(diff(grid.lat)))) max(max(abs(diff(grid.lat'))))]);
dlon=max([max(max(abs(diff(grid.lon)))) max(max(abs(diff(grid.lon'))))]);




s.lat=[min(gdata.lat(:))-dlat max(gdata.lat(:))+dlat];
s.lon=[min(gdata.lon(:))-dlon max(gdata.lon(:))+dlon];

sstime=min(gdata.time)-dt;
setime=max(gdata.time)+dt;
s.time={datestr(sstime) datestr(setime)};

[r1 r2 c1 c2]=geoij(tnc,s);
rho_dims=size(grid.lon);
if r1==1;r1=3;end
if c1==1;c1=3;end
if r2==rho_dims(1);r2=r2-2;end
if c2==rho_dims(1);c2=c2-2;end

glon=grid.lon(r1:r2,c1:c2);
glat=grid.lat(r1:r2,c1:c2);

 tw=tnc.timewindowij(sstime,setime);



tsalt=double(snc.data(tw.index,r1:r2,c1:c2,:));
ttemp=double(tnc.data(tw.index,r1:r2,c1:c2,:));

tdep=double(dnc.data(:,r1:r2,c1:c2));




mtime=grid.time(tw.index);
tic
mdep=grid.z;
zdim=size(mdep);
%
datestr(mtime)
for it=1:length(gdata.time)
    Imatch=find(mtime==gdata.time(it));
    if ~isempty(Imatch)

        ts=squeeze(tsalt(Imatch,:,:,:));
        tt=squeeze(ttemp(Imatch,:,:,:));
    else
        continue
    end


    warning off
    zs=nan(zdim(1),1);
    zt=nan(zdim(1),1);
    zd=nan(zdim(1),1);
    for iz=1:zdim(1)

        zs(iz)=griddata(double(glon),double(glat),squeeze(ts(:,:,iz)),gdata.lon(it),gdata.lat(it));


        zt(iz)=griddata(double(glon),double(glat),squeeze(tt(:,:,iz)),gdata.lon(it),gdata.lat(it));
        zd(iz)=griddata(double(glon),double(glat),squeeze(tdep(iz,:,:)),gdata.lon(it),gdata.lat(it));


    end

    salt(:,it)=interp1(abs(zd),zs,abs(gdata.depth));
    temp(:,it)=interp1(abs(zd),zt,abs(gdata.depth));
    warning on

    %
    %
end
         toc
%

end
function [salt temp]=acquire_nyhops(obj,iD,mname,nc)
disp('Acquiring NYHOPS A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);
%dnc=nc.variable(obj.DB_config.(mname).depth);

dt=(obj.DB_config.dt/2)/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;



grid=snc.grid_interop(:,:,:,:);
disp(grid)


dlat=max([max(max(abs(diff(grid.lat)))) max(max(abs(diff(grid.lat'))))]);
dlon=max([max(max(abs(diff(grid.lon)))) max(max(abs(diff(grid.lon'))))]);
s.lat=[min(gdata.lat(:))-dlat max(gdata.lat(:))+dlat]
s.lon=[min(gdata.lon(:))-dlon max(gdata.lon(:))+dlon]

sstime=min(gdata.time)-dt;
setime=max(gdata.time)+dt;
s.time={datestr(sstime) datestr(setime)}

try
    tic
    ssnc=snc.geosubset(s);
    stnc=tnc.geosubset(s);
    toc
catch
    disp('ERROR getting data')
end


grid=ssnc.grid(:,:,:,:)
tsalt=double(ssnc.data(:,:,:,:));
ttemp=double(stnc.data(:,:,:,:));

size(tsalt)
glon=grid.lon;
glat=grid.lat;

mtime=grid.time;
tic
mdep=grid.z;
zdim=size(mdep);



for it=1:length(gdata.time)
    %disp([datestr(gdata.time(it)) '-' datestr(max(gdata.time))])
    %datestr(mtime)
    Imatch=find(mtime>=gdata.time(it)-dt & mtime<=gdata.time(it)+dt );
    if ~isempty(Imatch)

        ts=squeeze(nanmean(tsalt(Imatch,:,:,:)));
        tt=squeeze(nanmean(ttemp(Imatch,:,:,:)));
    else
        disp('NO MATCH')
        continue
    end


    %size(ts)
    warning off
    zs=nan(zdim(1),1);
    zt=nan(zdim(1),1);
    zd=nan(zdim(1),1);
    %[max(max(glon))  min(min(glon)) max(max(glat))  min(min(glat))]

    %gdata.lon(it)
    %gdata.lat(it)
    for iz=1:zdim(1)

        zs(iz)=griddata(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(it),gdata.lat(it));


        zt(iz)=griddata(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(it),gdata.lat(it));
        zd(iz)=griddata(double(glon),double(glat),squeeze(mdep(iz,:,:)),gdata.lon(it),gdata.lat(it));


    end

   try
    salt(:,it)=interp1(abs(zd),zs,abs(gdata.depth));
    temp(:,it)=interp1(abs(zd),zt,abs(gdata.depth));
   catch
    disp('NOT IN LL RANGE')
   end
    warning on

    %
    %
end
         toc
%



end
function [salt temp]=acquire_hycom(obj,iD,mname,nc)
disp('Acquiring HYCOM A GRID')

gdata=obj.gdata(iD);
snc=nc.geovariable(obj.DB_config.(mname).salt);
tnc=nc.geovariable(obj.DB_config.(mname).temp);
dnc=nc.geovariable(obj.DB_config.(mname).depth);

dt=(obj.DB_config.dt/2)/(24);

salt=gdata.salt*nan;
temp=gdata.temp*nan;
ind=1;

grid=snc.grid_interop(:,:,:,:);

dlat=abs(max(diff(grid.lat)));
dlon=abs(max(diff(grid.lon)));
s.lat=[min(gdata.lat(:))-dlat max(gdata.lat(:))+dlat];
s.lon=[min(gdata.lon(:))-dlon max(gdata.lon(:))+dlon];

sstime=min(gdata.time)-dt;
setime=max(gdata.time)+dt;
s.time={datestr(sstime) datestr(setime)};
disp(s)
try
    tic
    ssnc=snc.geosubset(s);
    stnc=tnc.geosubset(s);
    sdnc=dnc.geosubset(s);
    toc
catch
    disp('ERROR getting data')
end

grid=ssnc.grid(:,:,:,:);
tsalt=ssnc.data(:,:,:,:);
ttemp=stnc.data(:,:,:,:);
tdep=sdnc.data(:,:,:,:);

[glon,glat]=meshgrid(grid.lon,grid.lat);
mtime=grid.time;
tic
mdep=grid.z;
%
for it=1:length(gdata.time)

    Imatch=find(mtime==gdata.time(it));
    if ~isempty(Imatch)

        ts=squeeze(tsalt(Imatch,:,:,:));
        tt=squeeze(ttemp(Imatch,:,:,:));
        td=squeeze(tdep(Imatch,:,:,:));
    else
        continue
    end





    for gi=1:length(grid.lon)
        for gj=1:length(grid.lat)
            tmps=ts(:,gj,gi);
            tmpt=tt(:,gj,gi);

            lastone=max(find(isfinite(tmps)));
            tmps(lastone+1:end)=tmps(lastone);

            lastone=max(find(isfinite(tmpt)));
            tmpt(lastone+1:end)=tmpt(lastone);


            ts(:,gj,gi)=tmps;
            tt(:,gj,gi)=tmpt;

        end
    end


    warning off
    zs=double(mdep*nan);
    zt=double(mdep*nan);
    zd=double(mdep*nan);




    for iz=1:length(mdep)

        zs(iz)=interp2(double(glon),double(glat),squeeze(ts(iz,:,:)),gdata.lon(it),gdata.lat(it));
        zt(iz)=interp2(double(glon),double(glat),squeeze(tt(iz,:,:)),gdata.lon(it),gdata.lat(it));
        zd(iz)=interp2(double(glon),double(glat),squeeze(td(iz,:,:)),gdata.lon(it),gdata.lat(it));


    end
    warning off
    [zd Ia]=unique(zd);
    zs=zs(Ia);
    zt=zt(Ia);
    zt=zt(isfinite(zd));
    zs=zs(isfinite(zd));
    zd=zd(isfinite(zd));
    if length(zd)<2
        continue
    end
    warning off
    salt(:,it)=interp1(abs(zd),zs,abs(gdata.depth));
    temp(:,it)=interp1(abs(zd),zt,abs(gdata.depth));
    salt(isnan(gdata.salt(:,it)),it)=nan;
    temp(isnan(gdata.temp(:,it)),it)=nan;


    warning on

    %
    %
end
         toc
%
%
%




end
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
