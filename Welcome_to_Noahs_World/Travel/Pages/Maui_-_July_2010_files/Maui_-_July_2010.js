// Created by iWeb 3.0.4 local-build-20140614

function createMediaStream_id4()
{return IWCreatePhotocast("Maui_-_July_2010_files/rss.xml",false);}
function initializeMediaStream_id4()
{createMediaStream_id4().load('..',function(imageStream)
{var entryCount=imageStream.length;var headerView=widgets['widget1'];headerView.setPreferenceForKey(imageStream.length,'entryCount');NotificationCenter.postNotification(new IWNotification('SetPage','id4',{pageIndex:0}));});}
function layoutMediaGrid_id4(range)
{createMediaStream_id4().load('..',function(imageStream)
{if(range==null)
{range=new IWRange(0,imageStream.length);}
IWLayoutPhotoGrid('id4',new IWPhotoGridLayout(3,new IWSize(190,190),new IWSize(190,0),new IWSize(214,205),27,27,0,new IWSize(22,23)),new IWPhotoFrame([IWCreateImage('Maui_-_July_2010_files/techblack-frame_01.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_02.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_03.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_06.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_09.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_08.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_07.png'),IWCreateImage('Maui_-_July_2010_files/techblack-frame_04.png')],null,2,0.666667,0.000000,0.000000,0.000000,0.000000,16.000000,16.000000,16.000000,18.000000,543.000000,380.000000,543.000000,380.000000,null,null,null,0.100000),imageStream,range,null,null,1.000000,{backgroundColor:'rgb(0, 0, 0)',reflectionHeight:100,reflectionOffset:2,captionHeight:100,fullScreen:0,transitionIndex:2},'../../Media/slideshow.html','widget1','widget2','widget3')});}
function relayoutMediaGrid_id4(notification)
{var userInfo=notification.userInfo();var range=userInfo['range'];layoutMediaGrid_id4(range);}
function onStubPage()
{var args=window.location.href.toQueryParams();parent.IWMediaStreamPhotoPageSetMediaStream(createMediaStream_id4(),args.id);}
if(window.stubPage)
{onStubPage();}
setTransparentGifURL('../../Media/transparent.gif');function applyEffects()
{var registry=IWCreateEffectRegistry();registry.registerEffects({reflection_0:new IWReflection({opacity:1.00,offset:1.00})});registry.applyEffects();}
function hostedOnDM()
{return false;}
function onPageLoad()
{IWRegisterNamedImage('comment overlay','../../Media/Photo-Overlay-Comment.png')
IWRegisterNamedImage('movie overlay','../../Media/Photo-Overlay-Movie.png')
loadMozillaCSS('Maui_-_July_2010_files/Maui_-_July_2010Moz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');adjustLineHeightIfTooBig('id3');adjustFontSizeIfTooBig('id3');NotificationCenter.addObserver(null,relayoutMediaGrid_id4,'RangeChanged','id4')
adjustLineHeightIfTooBig('id5');adjustFontSizeIfTooBig('id5');adjustLineHeightIfTooBig('id6');adjustFontSizeIfTooBig('id6');Widget.onload();fixupAllIEPNGBGs();fixAllIEPNGs('../../Media/transparent.gif');fixupIECSS3Opacity('id7');applyEffects()
initializeMediaStream_id4()}
function onPageUnload()
{Widget.onunload();}
