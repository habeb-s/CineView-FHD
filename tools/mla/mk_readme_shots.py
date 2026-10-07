from PIL import Image
S='previews_src/posters/%s/%s/%s.png'; O='repo/product/images/'
pick={'classic':'epg','details':'channelselection','cinema':'eventview','modern':'secondinfobar','minimal':'secondinfobar'}
def fit(p,w,h): return Image.open(p).convert('RGB').resize((w,h),Image.LANCZOS)
for m,s in pick.items(): fit(S%(m,'on',s),1280,720).save(O+'model-%s.jpg'%m,quality=88,optimize=True)
fit('shots/t102_final/W01.png',1280,720).save(O+'cineview-designs.jpg',quality=88,optimize=True)
a=fit(S%('classic','on','channelselection'),1280,720); b=fit(S%('classic','off','channelselection'),1280,720)
c=Image.new('RGB',(1280,1450),(12,16,28)); c.paste(a,(0,0)); c.paste(b,(0,730)); c.save(O+'posters-on-off.jpg',quality=86,optimize=True)
print('ok')
