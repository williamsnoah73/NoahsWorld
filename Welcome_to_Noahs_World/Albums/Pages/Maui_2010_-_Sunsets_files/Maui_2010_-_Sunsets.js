// Created by iWeb 3.0.4 local-build-20140614

function createMediaStream_id3()
{return IWCreatePhotocast("http://noahwilliams.me/Welcome_to_Noahs_World/Albums/Pages/Maui_2010_-_Sunsets_files/rss.xml",false);}
function initializeMediaStream_id3()
{createMediaStream_id3().load('http://noahwilliams.me/Welcome_to_Noahs_World/Albums/Pages',function(imageStream)
{var entryCount=imageStream.length;var headerView=widgets['widget1'];headerView.setPreferenceForKey(imageStream.length,'entryCount');NotificationCenter.postNotification(new IWNotification('SetPage','id3',{pageIndex:0}));});}
function layoutMediaGrid_id3(range)
{createMediaStream_id3().load('http://noahwilliams.me/Welcome_to_Noahs_World/Albums/Pages',function(imageStream)
{if(range==null)
{range=new IWRange(0,imageStream.length);}
IWLayoutPhotoGrid('id3',new IWPhotoGridLayout(3,new IWSize(182,182),new IWSize(182,0),new IWSize(218,197),27,27,0,new IWSize(28,30)),new IWPhotoFrame([IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_01.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_02.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_03.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_06.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_09.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_08.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_07.png'),IWCreateImage('Maui_2010_-_Sunsets_files/techblack-frame_04.png')],null,2,0.875000,0.000000,0.000000,0.000000,0.000000,16.000000,16.000000,16.000000,18.000000,543.000000,380.000000,543.000000,380.000000,null,null,null,0.100000),imageStream,range,null,null,1.000000,{backgroundColor:'rgb(0, 0, 0)',reflectionHeight:100,reflectionOffset:2,captionHeight:100,fullScreen:0,transitionIndex:2},'../../Media/slideshow.html','widget1','widget2','widget3')});}
function relayoutMediaGrid_id3(notification)
{var userInfo=notification.userInfo();var range=userInfo['range'];layoutMediaGrid_id3(range);}
function onStubPage()
{var args=window.location.href.toQueryParams();parent.IWMediaStreamPhotoPageSetMediaStream(createMediaStream_id3(),args.id);}
if(window.stubPage)
{onStubPage();}
setTransparentGifURL('../../Media/transparent.gif');function hostedOnDM()
{return false;}
function onPageLoad()
{IWRegisterNamedImage('comment overlay','../../Media/Photo-Overlay-Comment.png')
IWRegisterNamedImage('movie overlay','../../Media/Photo-Overlay-Movie.png')
loadMozillaCSS('Maui_2010_-_Sunsets_files/Maui_2010_-_SunsetsMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');NotificationCenter.addObserver(null,relayoutMediaGrid_id3,'RangeChanged','id3')
Widget.onload();fixupAllIEPNGBGs();fixAllIEPNGs('../../Media/transparent.gif');fixupIECSS3Opacity('id4');initializeMediaStream_id3()
performPostEffectsFixups()}
function onPageUnload()
{Widget.onunload();}
