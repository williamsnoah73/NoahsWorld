// Created by iWeb 3.0.4 local-build-20140614

function createMediaStream_id3()
{return IWCreateMediaCollection("http://noahwilliams.me/Welcome_to_Noahs_World/Travel/Travel_files/rss.xml",true,255,["No photos yet","%d photo","%d photos"],["","%d clip","%d clips"]);}
function initializeMediaStream_id3()
{createMediaStream_id3().load('http://noahwilliams.me/Welcome_to_Noahs_World/Travel',function(imageStream)
{var entryCount=imageStream.length;var headerView=widgets['widget6'];headerView.setPreferenceForKey(imageStream.length,'entryCount');NotificationCenter.postNotification(new IWNotification('SetPage','id3',{pageIndex:0}));});}
function layoutMediaGrid_id3(range)
{createMediaStream_id3().load('http://noahwilliams.me/Welcome_to_Noahs_World/Travel',function(imageStream)
{if(range==null)
{range=new IWRange(0,imageStream.length);}
IWLayoutPhotoGrid('id3',new IWPhotoGridLayout(2,new IWSize(303,227),new IWSize(303,32),new IWSize(336,274),27,27,0,new IWSize(89,74)),new IWPhotoFrame([IWCreateImage('Travel_files/spiralboook_ul.png'),IWCreateImage('Travel_files/spiralboook_top.png'),IWCreateImage('Travel_files/spiralboook_ur.png'),IWCreateImage('Travel_files/spiralboook_right.png'),IWCreateImage('Travel_files/spiralboook_lr.png'),IWCreateImage('Travel_files/spiralboook_bottom.png'),IWCreateImage('Travel_files/spiralboook_ll.png'),IWCreateImage('Travel_files/spiralboook_left.png')],null,1,0.800000,0.000000,10.000000,0.000000,19.000000,62.000000,49.000000,48.000000,72.000000,20.000000,1.000000,20.000000,1.000000,null,null,null,0.100000),imageStream,range,(null),null,1.000000,null,'../Media/slideshow.html','widget6',null,'widget7',{showTitle:true,showMetric:true})});}
function relayoutMediaGrid_id3(notification)
{var userInfo=notification.userInfo();var range=userInfo['range'];layoutMediaGrid_id3(range);}
function onStubPage()
{var args=window.location.href.toQueryParams();parent.IWMediaStreamPhotoPageSetMediaStream(createMediaStream_id3(),args.id);}
if(window.stubPage)
{onStubPage();}
setTransparentGifURL('../Media/transparent.gif');function hostedOnDM()
{return false;}
function onPageLoad()
{IWRegisterNamedImage('comment overlay','../Media/Photo-Overlay-Comment.png')
IWRegisterNamedImage('movie overlay','../Media/Photo-Overlay-Movie.png')
loadMozillaCSS('Travel_files/TravelMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');NotificationCenter.addObserver(null,relayoutMediaGrid_id3,'RangeChanged','id3')
Widget.onload();fixupAllIEPNGBGs();fixAllIEPNGs('../Media/transparent.gif');fixupIECSS3Opacity('id4');initializeMediaStream_id3()
performPostEffectsFixups()}
function onPageUnload()
{Widget.onunload();}
