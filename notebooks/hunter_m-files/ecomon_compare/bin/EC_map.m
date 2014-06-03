function EC_map
codat=load('eastcoast_CL.dat');
bathdata=load('EC_bath');
mnh=min(min(bathdata.H));
bathdata.H(bathdata.H<-500)=-500;
%demcmap(bathdata.H,128)
plot(codat(:,1),codat(:,2),'-k','linewidth',2);
v=-[ 20 50 100:100:1000];
hold on
%[C,p1]=contour(bathdata.lon,bathdata.lat,bathdata.H,v);
%set(p1,'color',[0.85 0.85 0.85])
%pcolor(bathdata.lon,bathdata.lat,bathdata.H);
%shading interp
%set(p1,'color',[0.85 0.85 0.85])
%coast_new=join_cst(codat,0.1);  
%fillseg(coast_new);
hold off


set(gca,'xlim',[-82  -60],'ylim',[   31 47])
set(gca,'dataaspectratio',[1 cos(2*pi*mean(codat(isfinite(codat(:,2)),2)/360)) 1])