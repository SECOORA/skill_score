classdef model_codar_compare_handler < data_handler
%  UNTITLED Summary of this class goes here
%  Detailed explanation goes here
    properties
        MODELS
        olog
        lon
        lat
        time
        u
        v
        cu
        cv
        ctime
        clat
        clon
        nc
    end
    properties (SetAccess=private)

    end

    methods
        function obj=model_codar_compare_handler(xmlfile,MODELS,olog)
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
        function obj=acquire(obj)

            disp('Acquiring CODAR data')
            direc=obj.DB_config.directory;
            load(obj.DB_config.codar_obs);
            stime=obj.starttime;
            etime=obj.endtime;

            info(obj.olog,['Processing from ' datestr(stime) '-' datestr(etime)]);
            It=find(ctide.t>stime & ctide.t<etime);
            obj.ctime = ctide.t(It);
            obj.cu = ctide.U(It,:);
            obj.cv = ctide.V(It,:);
            obj.clon = ctide.Lon;
            obj.clat = ctide.Lat;
            days=unique(floor(obj.ctime));

            s.lat=[min(obj.clat(:)) max(obj.clat(:))];
            s.lon=[min(obj.clon(:)) max(obj.clon(:))];
            s.z_index=[1 2];

            for iM=1:length(obj.MODELS)
                if isfield(obj.DB_config,obj.MODELS{iM})
                    mname=obj.MODELS{iM};

                    info(obj.olog,['Processing Model - ' mname]);
                    grid=obj.DB_config.(mname).grid;
                    nc=ncgeodataset(obj.DB_config.(mname).url);
                    ofile=[direc 'UV_extr_' obj.MODELS{iM}];
                    switch grid
                        case 'A'
                            [u v]=acquire_a(obj,mname,nc,s);

                        case 'C'
                            s.z_index=obj.DB_config.(mname).z;
                            [u v]=acquire_c(obj,mname,nc,s,obj.DB_config.(mname).url);

                        case 'UMASSHOPS'
                            [u v]=acquire_umass(obj,mname,nc,s);
                        case 'NYHOPS'
                            [u v]=acquire_nyhops(obj,mname,nc,s);
                        case 'HYCOM'
                            [u v]=acquire_hycom(obj,mname,nc,s);

                        otherwise
                            disp('GRID NOT RECOGNIZED')
                            continue
                    end

                    cu=obj.cu;
                    cv=obj.cv;
                    ctime=obj.ctime;
                    clat=obj.clat;
                    clon=obj.clon;
                    save(ofile,'u','v','cu','cv','clat','clon','ctime')



                else
                    disp('MODEL NOT IN DATABASE')


                end
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
            size(lon)
            size(lat)
            size(u)
            figure(1)
            set(gcf,'renderer','zbuffer')
            EC_map
            hold on
            quiver3(lon(:),lat(:),zeros(size(lon(:))),u(:),v(:),zeros(size(lon(:))),10,'k')
            %hold on

            quiver3(tlon,tlat,zeros(size(tlon)),tu,tv,zeros(size(tlon)),1,'r')
            hold off
            %hold off
            title(datestr(ttime))
            xlabel(datestr(obj.time(imn)))




        end
    end
end


function [u v]=acquire_a(obj,mname,nc,s)
disp('Acquiring A GRID')

s.z_index=[obj.DB_config.(mname).z obj.DB_config.(mname).z];
[yy mm dd hh mi ss]=datevec(obj.ctime);
unc=nc.geovariable(obj.DB_config.(mname).u);
vnc=nc.geovariable(obj.DB_config.(mname).v);
dt=(obj.DB_config.dt/2)/(24);
grid=unc.grid(:,:,:,:);
u=obj.cu*nan;
v=obj.cv*nan;
ind=1;
for iYY=min(yy):max(yy)
    for iMM=1:12
        disp(['Trying ' sprintf('%2.2d',iMM) ' in ' sprintf('%4.4d',iYY)])
        INM=find(yy==iYY & mm==iMM);
        if isempty(INM)
            continue
        end
        sstime=datenum(iYY,iMM,1)-dt;
        setime=datenum(iYY,iMM+1,1)+dt;
        s.time={datestr(sstime) datestr(setime)};
        s
        try
            tic
            sunc=unc.geosubset(s);
            svnc=vnc.geosubset(s);
            toc
        catch ME
            disp(['Error:' ME.message])
            for ie=1:length(ME.stack)
                disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
            end
            continue
        end

        gridu=sunc.grid
        gridv=svnc.grid
        [glon,glat]=meshgrid(gridu.lon,gridu.lat);
        mtime=gridu.time;
        tic

        for it=1:length(obj.ctime)
            itimes=find(mtime>=obj.ctime(it)-dt & mtime<=obj.ctime(it)+dt);
            Imatch=find(mtime==obj.ctime(it));
            if isempty(itimes) | isempty(Imatch)
                continue
            end

            mu=double(squeeze(nanmean(sunc.data(itimes,1,:,:),1)));
            %size(glat)
            %size(glon)
            %size(mu)
            u(it,:)=interp2(double(glon),double(glat),mu,obj.clon,obj.clat);

            mv=double(squeeze(nanmean(svnc.data(itimes,1,:,:),1)));
            v(it,:)=interp2(double(glon),double(glat),mv,obj.clon,obj.clat);


        end
        toc




    end
end
%try
%    figure(1)
%    EC_map
%    hold on
%    plot(glon,glat,'ro');
%    hold off
%catch
%end
%u=[];
%v=[];

end
function [u v]=acquire_c(obj,mname,nc,s,url)


zg=s.z_index;
disp('Acquiring C GRID')
[yy mm dd hh mi ss]=datevec(obj.ctime);
unc=nc.geovariable(obj.DB_config.(mname).u);
vnc=nc.geovariable(obj.DB_config.(mname).v);
tnc=nc.geovariable(obj.DB_config.(mname).angle);
angle=tnc.data(:,:);
dt=(obj.DB_config.dt/2)/(24);

[r1 r2 c1 c2]=geoij(tnc,s);

grid=tnc.grid_interop(:,:,:,:)
gridu=unc.grid_interop(:,:,:,:)
gridv=vnc.grid_interop(:,:,:,:)
rho_dims=size(grid.lon);
if r1==1;r1=3;end
if c1==1;c1=3;end
if r2==rho_dims(1);r2=r2-2;end
if c2==rho_dims(1);c2=c2-2;end

angle=angle(r1:r2,c1:c2);
lon=grid.lon(r1:r2,c1:c2);
lat=grid.lat(r1:r2,c1:c2);

u_dims=size(gridu.lon);
v_dims=size(gridv.lon);


%figure(1)
%plot(lon,lat,'ro');
%hold on
%plot(gridu.lon(r1:r2,c1-1:c2),gridu.lat(r1:r2,c1-1:c2),'g>');
%plot(gridv.lon(r1-1:r2,c1:c2),gridv.lat(r1-1:r2,c1:c2),'b^');
%hold off

zu=gridu.z(:,r1:r2,c1-1:c2);
zv=gridv.z(:,r1-1:r2,c1:c2);
dimzu=size(zu);
dimzv=size(zv);

%for i2=1:dimzu(2)
%    for i3=1:dimzu(3)
%        zul_ind = find(diff(zu>s.z_index)~=0);
%        size(zul_ind)
%    end
%end

tzu=reshape(zu,[dimzu(1) dimzu(2)*dimzu(3)]);
tzv=reshape(zv,[dimzv(1) dimzv(2)*dimzv(3)]);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%ERROR BELOW
%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%
[u I]=max(diff(tzu>zg));
Iubot = sub2ind(size(tzu),I,[1:dimzu(2)*dimzu(3)]);
ubot=tzu(Iubot);
Iutop = sub2ind(size(tzu),I+1,[1:dimzu(2)*dimzu(3)]);
utop=tzu(Iutop);
alphau = (zg-ubot)./(utop-ubot);
Iubot(alphau>1)=dimzu(1);%ERROR
Iutop(alphau>1)=dimzu(1);%ERROR
alphau(alphau>1)=1;

[v I]=max(diff(tzv>zg));
Ivbot = sub2ind(size(tzv),I,[1:dimzv(2)*dimzv(3)]);
vbot=tzv(Ivbot);
Ivtop = sub2ind(size(tzv),I+1,[1:dimzv(2)*dimzv(3)]);
vtop=tzv(Ivtop);
alphav = (zg-vbot)./(vtop-vbot);
Ivbot(alphav>1)=dimzv(1);%ERROR
Ivtop(alphav>1)=dimzv(1);%ERROR
alphav(alphav>1)=1;

%disp([utop' ubot' (utop-ubot)' alphau'])
%disp([vtop' vbot' (vtop-vbot)'])


u=obj.cu*nan;
v=obj.cv*nan;


%
for iYY=min(yy):max(yy)
    for iMM=1:12
        INM=find(yy==iYY & mm==iMM);
        disp([iYY iMM])
        if isempty(INM)
            continue
        end
        sstime=datenum(iYY,iMM,1)-dt;
        setime=datenum(iYY,iMM+1,1)+dt;
        s.time={datestr(sstime) datestr(setime)};
        try
            tw=unc.timewindowij(sstime,setime);
            tic

            mu_v=[];
            mv_v=[];

            for izz=1:dimzu(1)
                tmp=unc.data(tw.index,izz,r1:r2,c1-1:c2);
                mu_v=cat(2,mu_v,tmp);
            end

            for izz=1:dimzv(1)
                tmp=vnc.data(tw.index,izz,r1-1:r2,c1:c2);
                mv_v=cat(2,mv_v,tmp);
            end



            dimu=size(mu_v)
            dimv=size(mv_v);

            mu=nan(dimu(1),1,dimu(3),dimu(4));
            mv=nan(dimv(1),1,dimv(3),dimv(4));
            toc
            % pause




            tic
            for i1=1:dimu(1)
                %  dimu
                %  dimzu
                tmpu=squeeze(mu_v(i1,:,:,:));
                datau=reshape(tmpu,[dimzu(1) dimzu(2)*dimzu(3)]);
                upr=datau(Iubot).*alphau+datau(Iutop).*(1-alphau);

                % disp([datau(Iubot(310:320))' datau(Iutop(310:320))' upr(310:320)'])
                tmpv=squeeze(mv_v(i1,:,:,:));
                datav=reshape(tmpv,[dimzv(1) dimzv(2)*dimzv(3)]);
                vpr=datav(Ivbot).*alphav+datav(Ivtop).*(1-alphav);
                % disp([datav(Iubot(310:320))' datav(Iutop(310:320))' vpr(310:320)'])
                mu(i1,1,:,:)=reshape(upr,dimzu(2),dimzu(3));
                mv(i1,1,:,:)=reshape(vpr,dimzv(2),dimzv(3));


                %pause
            end

            toc
            %
        catch ME
            disp(['Error:' ME.message])
            for ie=1:length(ME.stack)
                disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
            end
            continue
        end
        mtime=tw.time;
        tic

        for it=1:length(obj.ctime)
            itimes=find(mtime>=obj.ctime(it)-dt & mtime<=obj.ctime(it)+dt);
            Imatch=find(mtime==obj.ctime(it));
            if isempty(itimes) | isempty(Imatch)
                continue
            end

            tmu=double(squeeze(nanmean(mu(itimes,1,:,:),1)));
            tmu=av2(tmu')';
            tmv=double(squeeze(nanmean(mv(itimes,1,:,:),1)));
            tmv=av2(tmv);


            uveitheta = (tmu+sqrt(-1)*tmv).*exp(sqrt(-1)*angle);
            tmpu = real(uveitheta);
            tmpv = imag(uveitheta);


            u(it,:)=griddata(double(lon),double(lat),tmpu,obj.clon,obj.clat);
            v(it,:)=griddata(double(lon),double(lat),tmpv,obj.clon,obj.clat);

            % rotate coordinates if required

        end
        toc

    end
end
end
%%
function [u v]=acquire_umass(obj,mname,nc,s)

disp('Acquiring UMASS A GRID')
[yy mm dd hh mi ss]=datevec(obj.ctime);
unc=nc.geovariable(obj.DB_config.(mname).u);
vnc=nc.geovariable(obj.DB_config.(mname).v);
dnc=nc.variable('z_v');
dt=(obj.DB_config.dt/2)/(24);
zg=obj.DB_config.(mname).z;
[r1 r2 c1 c2]=geoij(unc,s)
grid=unc.grid_interop(:,:,:,:);
u=obj.cu*nan;
v=obj.cv*nan;
rho_dims=size(grid.lon);
if r1==1;r1=3;end
if c1==1;c1=3;end
if r2==rho_dims(1);r2=r2-2;end
if c2==rho_dims(1);c2=c2-2;end

size(grid.lon)
size(grid.lat)
size(dnc.data)
lon=grid.lon(r1:r2,c1:c2);
lat=grid.lat(r1:r2,c1:c2);
z=double(dnc.data(:,r1:r2,c1:c2));


dimz=size(z);

tz=reshape(z,[dimz(1) dimz(2)*dimz(3)]);

[tuj I]=max(diff(tz<zg));
Iutop = sub2ind(size(tz),I,[1:dimz(2)*dimz(3)]);


utop=tz(Iutop);

%I(I==1)=2;
Iubot = sub2ind(size(tz),I+1,[1:dimz(2)*dimz(3)]);
ubot=tz(Iubot);
alpha = (zg-ubot)./(utop-ubot);

alpha(alpha>1)=0;

[ubot(1:150)' utop(1:150)' alpha(1:150)']


talpha=reshape(alpha,dimz(2),dimz(3));

figure(1)
set(gcf,'renderer','zbuffer')
EC_map
hold on
pcolor(lon,lat,squeeze(talpha));
shading flat
caxis([0 1])
% plot(lon,lat,'k+')
hold
colorbar
print(gcf,'-dpng','test1.png')

u=obj.cu*nan;
v=obj.cv*nan;
ind=1;
for iYY=min(yy):max(yy)
    for iMM=1:12
        INM=find(yy==iYY & mm==iMM);
        disp([iYY iMM])
        if isempty(INM)
            continue
        end
        sstime=datenum(iYY,iMM,1)-dt;
        setime=datenum(iYY,iMM+1,1)+dt;
        s.time={datestr(sstime) datestr(setime)};

        try
            tw=unc.timewindowij(sstime,setime);

            tic

            grid=unc.grid_interop(:,:,:,:)
            %grid.z;
            %size(vnc.data(:,:,:,:))
            tmu=unc.data(tw.index,r1:r2,c1:c2,:);
            tmv=vnc.data(tw.index,r1:r2,c1:c2,:);
            dims=size(tmu)
            mu=nan(dims(1),dims(2),dims(3));
            mv=nan(dims(1),dims(2),dims(3));

            for i1=1:dims(1)
                tmpu=squeeze(tmu(i1,:,:,:));
                tmpu=shiftdim(tmpu,2);
                datau=reshape(tmpu,[dimz(1) dimz(2)*dimz(3)]);
                upr=datau(Iubot).*alpha+datau(Iutop).*(1-alpha);

                tmpv=squeeze(tmv(i1,:,:,:));
                tmpv=shiftdim(tmpv,2);
                datav=reshape(tmpv,[dimz(1) dimz(2)*dimz(3)]);
                vpr=datav(Iubot).*alpha+datav(Iutop).*(1-alpha);


                mu(i1,:,:)=reshape(upr,dimz(2),dimz(3));
                mv(i1,:,:)=reshape(vpr,dimz(2),dimz(3));

            end

%
%                 disp([i1 dims(1)])
%                 for i2=1:dims(2)
%                     for i3=1:dims(3)
%                         mu(i1,i2,i3,1)=interp1(squeeze(z(:,i2,i3)),squeeze(tmu(i1,i2,i3,:)),zg);
%                         mv(i1,i2,i3,1)=interp1(squeeze(z(:,i2,i3)),squeeze(tmv(i1,i2,i3,:)),zg);
%
%                     end
%                 end
%             end

            mtime=grid.time(tw.index);
            datestr(mtime(1:2))
            %mu(1,:,:)
            toc
        catch
            continue
        end
        %
        for it=1:length(obj.ctime)
            itimes=find(mtime>=obj.ctime(it)-dt & mtime<=obj.ctime(it)+dt);
            Imatch=find(mtime==obj.ctime(it));
            if isempty(itimes) | isempty(Imatch)
                continue
            end

            tmu=double(squeeze(nanmean(mu(itimes,:,:),1)));
         %   size(tmu)
         %   it
         %   size(u)
         %   size(lat)
            u(it,:)=griddata(double(lon),double(lat),tmu,obj.clon,obj.clat);
            tmv=double(squeeze(nanmean(mv(itimes,:,:),1)));
            v(it,:)=griddata(double(lon),double(lat),tmv,obj.clon,obj.clat);

        end
        toc




    end
end

end

%%
function [u v]=acquire_nyhops(obj,mname,nc,s)
disp('Acquiring NYHOPS A GRID')
s.z_index=[1 11];
zg=obj.DB_config.(mname).z;

[yy mm dd hh mi ss]=datevec(obj.ctime);
unc=nc.geovariable(obj.DB_config.(mname).u);
vnc=nc.geovariable(obj.DB_config.(mname).v);
anc=nc.geovariable(obj.DB_config.(mname).angle);
dnc=nc.geovariable(obj.DB_config.(mname).depth);



[r1 r2 c1 c2]=geoij(unc,s)
dt=(obj.DB_config.dt/2)/(24);
gridu=unc.grid(:,:,:,:)
gridv=vnc.grid(:,:,:,:)

lon=gridu.lon(r1:r2,c1:c2);
lat=gridu.lat(r1:r2,c1:c2);
angle=double(anc.data(r1:r2,c1:c2));
d=double(dnc.data(r1:r2,c1:c2));
dims=size(d)
z=nan(length(gridu.sigma),dims(1),dims(2));
size(z)
for i1=1:dims(1)
    for i2=1:dims(2)
        z(:,i1,i2)=d(i1,i2)*gridu.sigma;
    end
end


disp(z(:,20,20))
dimz=size(z);

tz=reshape(z,[dimz(1) dimz(2)*dimz(3)]);

[tuj I]=max(diff(tz<zg));
Iutop = sub2ind(size(tz),I,[1:dimz(2)*dimz(3)]);


utop=tz(Iutop);

%I(I==1)=2;
Iubot = sub2ind(size(tz),I+1,[1:dimz(2)*dimz(3)]);
ubot=tz(Iubot);
alpha = (zg-ubot)./(utop-ubot);
%Iubot(alpha>1)=dimz(1);
%Iutop(alpha>1)=dimz(1);
alpha(alpha>1)=0;

[ubot(1:150)' utop(1:150)' alpha(1:150)']

tz(:,1)

        talpha=reshape(alpha,dimz(2),dimz(3));

%
%             figure(1)
%             set(gcf,'renderer','zbuffer')
%
%             EC_map
%              hold on
%              pcolor(lon,lat,squeeze(talpha));
%              shading flat
%            % plot(lon,lat,'k+')
%             hold
%             colorbar
%             print(gcf,'-dpng','test1.png')
%             figure(1)
%             set(gcf,'renderer','zbuffer')
%
%             EC_map
%              hold on
%              pcolor(lon,lat,squeeze(d));
%              shading flat
%            % plot(lon,lat,'k+')
%             hold off
%             colorbar
%             print(gcf,'-dpng','test2.png')

     %       return

%


u=obj.cu*nan;
v=obj.cv*nan;
 ind=1;


%
for iYY=min(yy):max(yy)
    for iMM=1:12
%for iYY=max(yy):max(yy)
%    for iMM=5:5
        INM=find(yy==iYY & mm==iMM);
        disp([iYY iMM])
        if isempty(INM)
            continue
        end
        sstime=datenum(iYY,iMM,1)-dt;
        setime=datenum(iYY,iMM+1,1)+dt;
        s.time={datestr(sstime) datestr(setime)};
        try
            tw=unc.timewindowij(sstime,setime);
            tic

            mu_v=[];
            mv_v=[];
            tw

            for izz=1:11
                disp('u')
                disp(izz)
                tmp=unc.data(tw.index,izz,r1:r2,c1:c2);
                mu_v=cat(2,mu_v,tmp);
                pause(0.1)
            end

            for izz=1:11
                disp('v')
                disp(izz)
                tmp=vnc.data(tw.index,izz,r1:r2,c1:c2);
                mv_v=cat(2,mv_v,tmp);
                pause(0.1)
            end

            mu_v=double(mu_v);
            mv_v=double(mv_v);

            dimu=size(mu_v);
            dimv=size(mv_v);

            mu=nan(dimu(1),1,dimu(3),dimu(4));
            mv=nan(dimv(1),1,dimv(3),dimv(4));
            toc
            tic
            for i1=1:dimu(1)
                tmpu=squeeze(mu_v(i1,:,:,:));
                datau=reshape(tmpu,[dimz(1) dimz(2)*dimz(3)]);
                upr=datau(Iubot).*alpha+datau(Iutop).*(1-alpha);
                tmpv=squeeze(mv_v(i1,:,:,:));
                datav=reshape(tmpv,[dimz(1) dimz(2)*dimz(3)]);
                vpr=datav(Iubot).*alpha+datav(Iutop).*(1-alpha);
                mu(i1,1,:,:)=reshape(upr,dimz(2),dimz(3));
                mv(i1,1,:,:)=reshape(vpr,dimz(2),dimz(3));
            end
            toc
        catch ME
            disp(['Error:' ME.message])
            for ie=1:length(ME.stack)
                disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
            end
            continue
        end
        mtime=tw.time;

        tic

        for it=1:length(obj.ctime)

            itimes=find(mtime>=obj.ctime(it)-dt & mtime<=obj.ctime(it)+dt);
            Imatch=find(mtime==obj.ctime(it));
            if isempty(itimes)
            %    disp('EMPTY')
                continue
            end

           % mu(itimes(1),1,:,:)
           % disp('FOUND')
            tmu=double(squeeze(nanmean(mu(itimes,1,:,:),1)));
           % tmu=av2(tmu')';
            tmv=double(squeeze(nanmean(mv(itimes,1,:,:),1)));
           % tmv=av2(tmv);



            uveitheta = (tmu+sqrt(-1)*tmv).*exp(sqrt(-1)*angle);
            tmpu = real(uveitheta);
            tmpv = imag(uveitheta);

            %length(find(isfinite(tmpu)))
            %length(find(isfinite(tmpv)))

            u(it,:)=griddata(double(lon),double(lat),tmpu,obj.clon,obj.clat);
            v(it,:)=griddata(double(lon),double(lat),tmpv,obj.clon,obj.clat);

            %[tmpu(1:100)' u(it,1:100)]
            % rotate coordinates if required

        end
        toc

    end
end

 % for iYY=min(yy):max(yy)
%     for iMM=1:12
%         INM=find(yy==iYY & mm==iMM);
%         disp([iYY iMM])
%         if isempty(INM)
%             continue
%         end
%         sstime=datenum(iYY,iMM,1)-dt;
%         setime=datenum(iYY,iMM+1,1)+dt;
%         s.time={datestr(sstime) datestr(setime)};
%
% %         try
% %             tic
% %             sunc=unc.geosubset(s);
% %             svnc=vnc.geosubset(s);
% %             toc
% %         catch ME
% %             disp(['Error:' ME.message])
% %             for ie=1:length(ME.stack)
% %                 disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
% %             end
% %
% %             continue
% %         end
%    %     gridu=sunc.grid
%    %     gridv=svnc.grid
%         %[glon,glat]=meshgrid(gridu.lon,gridu.lat);
%
%
%         try
%             tic
%             tw=unc.timewindowij(sstime,setime);
%
%
%             mu_v=[];
%             mv_v=[];
%
%             for izz=1:11
%                 tmp=unc.data(tw.index,izz,r1:r2,c1:c2);
%                 mu_v=cat(2,mu_v,tmp);
%             end
%
%             for izz=1:11
%                 tmp=vnc.data(tw.index,izz,r1:r2,c1:c2);
%                 mv_v=cat(2,mv_v,tmp);
%             end
%
%             toc
%         catch ME
%             disp(['Error:' ME.message])
%             for ie=1:length(ME.stack)
%                 disp([ME.stack(ie).name ' : line ' num2str(ME.stack(ie).line) ': file -  ' ME.stack(ie).file ])
%             end
%
%             continue
%         end
%
%         glon=gridu.lon;
%         glat=gridu.lat;
% %        mtime=round(gridu.time*24*60)/(24*60);
%         mtime=tw.time;
%         datestr(min(mtime))
%         datestr(max(mtime))
%         tic
%         for it=1:length(obj.ctime)
%
%             itimes=find(mtime>=obj.ctime(it)-dt & mtime<=obj.ctime(it)+dt);
%             size(itimes)
%             Imatch=find(mtime==obj.ctime(it));
%             if isempty(itimes)
%                 continue
%             end
%
%             %mu=double(squeeze(nanmean(sunc.data(itimes,:,:,:),1)));
%             %mv=double(squeeze(nanmean(svnc.data(itimes,:,:,:),1)));
%
%             %mu_v=[];
%             %mv_v=[];
%
%            % for izz=1:11
%            %     tmp=unc.data(itimes,izz,:,:);
%            %     mu_v=cat(2,mu_v,tmp);
%            % end
%
%            % for izz=1:dimzv(1)
%            %     tmp=vnc.data(itimes,izz,:,:);
%            %     mv_v=cat(2,mv_v,tmp);
%            % end
%
%
%
%
%             mu_v=double(squeeze(nanmean(sunc.data(itimes,:,:,:),1)));
%
%             mv_v=double(squeeze(nanmean(svnc.data(itimes,:,:,:),1)));
%
%             dimu=size(mu_v)
%             dimv=size(mv_v);
%
%             mu=nan(dimu(1),1,dimu(3),dimu(4));
%             mv=nan(dimv(1),1,dimv(3),dimv(4));
%
%
%
%             size(mu)
%
%             tic
%             for i1=1:dimu(1)
%                 tmpu=squeeze(mu_v(i1,:,:,:));
%                 datau=reshape(tmpu,[dimz(1) dimz(2)*dimz(3)]);
%                 upr=datau(Iubot).*alpha+datau(Iutop).*(1-alpha);
%
%                 tmpv=squeeze(mv_v(i1,:,:,:));
%                 datav=reshape(tmpv,[dimz(1) dimz(2)*dimz(3)]);
%                 vpr=datav(Ivbot).*alpha+datav(Ivtop).*(1-alpha);
%                 % disp([datav(Iubot(310:320))' datav(Iutop(310:320))' vpr(310:320)'])
%                 mu(i1,1,:,:)=reshape(upr,dimzu(2),dimzu(3));
%                 mv(i1,1,:,:)=reshape(vpr,dimzv(2),dimzv(3));
%
%
%                 %pause
%             end
%
%             toc
%
%
%
%             uveitheta = (mu+sqrt(-1)*mv).*exp(sqrt(-1)*angle);
%             tmpu= real(uveitheta);
%             tmpv= imag(uveitheta);
%             %whos tmpu tmpv
%             u(it,:) =griddata(double(glon),double(glat),tmpu,obj.clon,obj.clat);
%             v(it,:) =griddata(double(glon),double(glat),tmpv,obj.clon,obj.clat);
%
%         end
%         toc
%
%
%
%
%     end
% end
% %u=[];
%v=[];
try
    figure(1)
    EC_map
    hold on
    plot(glon,glat,'ro');
    hold off
catch
end
end

function [u v]=acquire_hycom(obj,mname,nc,s)
disp('Acquiring HYCOM A GRID')
[yy mm dd hh mi ss]=datevec(obj.ctime);
unc=nc.geovariable(obj.DB_config.(mname).u);
vnc=nc.geovariable(obj.DB_config.(mname).v);
[r1 r2 c1 c2]=geoij(unc,s);
dt=(obj.DB_config.dt/2)/(24);
u=obj.cu*nan;
v=obj.cv*nan;
ind=1;
for iYY=min(yy):max(yy)
    for iMM=1:12
        INM=find(yy==iYY & mm==iMM);
        if isempty(INM)
            continue
        end
        sstime=datenum(iYY,iMM,1)-dt;
        setime=datenum(iYY,iMM+1,1)+dt;
        s.time={datestr(sstime) datestr(setime)};
        try
            tic
            sunc=unc.geosubset(s);
            svnc=vnc.geosubset(s);
            toc
        catch
            continue
        end
        gridu=sunc.grid;
        gridv=svnc.grid;
        %[glon,glat]=meshgrid(gridu.lon,gridu.lat);
        glon=gridu.lon;
        glat=gridu.lat;
        griflat=gridu.lat;
        mtime=round(gridu.time*24*60)/(24*60);
        tic
        for it=1:length(obj.ctime)

            itimes=find(mtime>=obj.ctime(it)-dt & mtime<=obj.ctime(it)+dt);
            Imatch=find(mtime==obj.ctime(it));
            if isempty(itimes)
                continue
            end

            %size(itimes)
            %disp(it)
            %datestr(obj.ctime(it))
            %disp(' ')
            %datestr(mtime(itimes))
            mu=double(squeeze(nanmean(sunc.data(itimes,1,:,:),1)));

            mv=double(squeeze(nanmean(svnc.data(itimes,1,:,:),1)));



            u(it,:) =griddata(double(glon),double(glat),mu,obj.clon,obj.clat);
            v(it,:) =griddata(double(glon),double(glat),mv,obj.clon,obj.clat);

        end
        toc




    end
end
%u=[];
%v=[];
try
    figure(1)
    EC_map
    hold on
    plot(glon,glat,'ro');
    hold off
catch
end
end

function a = av2(a)
%AV2    grid average function.
%       If A is a vector [a(1) a(2) ... a(n)], then AV2(A) returns a
%   vector of averaged values:
%   [ ... 0.5(a(i+1)+a(i)) ... ]
%
%       If A is a matrix, the averages are calculated down each column:
%   AV2(A) = 0.5*(A(2:m,:) + A(1:m-1,:))
%
%   TMPX = AV2(A)   will be the averaged A in the column direction
%   TMPY = AV2(A')' will be the averaged A in the row direction
%
%   John Wilkin 21/12/93

[m,n] = size(a);
if m == 1
    a = 0.5 * (a(2:n) + a(1:n-1));
else
    a = 0.5 * (a(2:m,:) + a(1:m-1,:));
end
end
