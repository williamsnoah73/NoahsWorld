// Created by iWeb 3.0.4 local-build-20140614

function createMediaStream_id4()
{return IWCreatePhotocast("http://noahwilliams.me/Welcome_to_Noahs_World/Travel/Pages/Double_Musky_Express_files/rss.xml",false);}
function initializeMediaStream_id4()
{createMediaStream_id4().load('http://noahwilliams.me/Welcome_to_Noahs_World/Travel/Pages',function(imageStream)
{var entryCount=imageStream.length;var headerView=widgets['widget1'];headerView.setPreferenceForKey(imageStream.length,'entryCount');NotificationCenter.postNotification(new IWNotification('SetPage','id4',{pageIndex:0}));});}
function layoutMediaGrid_id4(range)
{createMediaStream_id4().load('http://noahwilliams.me/Welcome_to_Noahs_World/Travel/Pages',function(imageStream)
{if(range==null)
{range=new IWRange(0,imageStream.length);}
IWLayoutPhotoGrid('id4',new IWPhotoGridLayout(3,new IWSize(182,182),new IWSize(182,0),new IWSize(218,197),27,27,0,new IWSize(28,30)),new IWPhotoFrame([IWCreateImage('Double_Musky_Express_files/techblack-frame_01.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_02.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_03.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_06.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_09.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_08.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_07.png'),IWCreateImage('Double_Musky_Express_files/techblack-frame_04.png')],null,2,0.875000,0.000000,0.000000,0.000000,0.000000,16.000000,16.000000,16.000000,18.000000,543.000000,380.000000,543.000000,380.000000,null,null,null,0.100000),imageStream,range,null,null,1.000000,{backgroundColor:'rgb(0, 0, 0)',reflectionHeight:100,reflectionOffset:2,captionHeight:100,fullScreen:0,transitionIndex:2},'../../Media/slideshow.html','widget1','widget2','widget3')});}
function relayoutMediaGrid_id4(notification)
{var userInfo=notification.userInfo();var range=userInfo['range'];layoutMediaGrid_id4(range);}
function onStubPage()
{var args=window.location.href.toQueryParams();parent.IWMediaStreamPhotoPageSetMediaStream(createMediaStream_id4(),args.id);}
if(window.stubPage)
{onStubPage();}
setTransparentGifURL('../../Media/transparent.gif');function hostedOnDM()
{return false;}
function onPageLoad()
{IWRegisterNamedImage('comment overlay','../../Media/Photo-Overlay-Comment.png')
IWRegisterNamedImage('movie overlay','../../Media/Photo-Overlay-Movie.png')
loadMozillaCSS('Double_Musky_Express_files/Double_Musky_ExpressMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');adjustLineHeightIfTooBig('id3');adjustFontSizeIfTooBig('id3');NotificationCenter.addObserver(null,relayoutMediaGrid_id4,'RangeChanged','id4')
Widget.onload();fixupAllIEPNGBGs();fixAllIEPNGs('../../Media/transparent.gif');fixupIECSS3Opacity('id5');initializeMediaStream_id4()
performPostEffectsFixups()}
function onPageUnload()
{Widget.onunload();}
