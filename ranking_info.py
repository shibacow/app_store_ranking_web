import os,sys
sys.path.append('../app_store_ranking')
from datetime import datetime,timedelta
from mog_op import MongoOp,ObjectId
import web
import re
import selector_info

class AppInfo(object):
    def __init__(self,aid,rank,title,summary,img,link,country_code,artist):
        self.aid=aid
        self.rank=rank
        self.title=title
        self.summary=summary
        self.img=img
        self.link=link
        self.country_code=country_code.lower()
        self.artist=artist

class RankingInfo(object):
    def __parseOrder(self,feed,offset,limit):
        if not 'entry' in feed:
            return
        entries=feed['entry']
        self.maxsize=max(len(entries),self.maxsize)
        if isinstance(entries,list):
            entries=entries[offset:offset+limit]
            for i,elm in enumerate(entries):
                aid=elm['id']['attributes']['im:id']
                aid=int(aid)
                #if i==1:
                #    web.debug(elm)
                artist=elm['im:artist']['label']
                #web.debug(artist)
                r=i+1
                title=elm['title']['label']
                summary=''
                if 'summary' in elm:
                    summary=elm['summary']
                link=''
                if isinstance(elm['link'],list):
                    for ls in elm['link']:
                        ls=ls['attributes']
                        if ls['type']==u'text/html':
                            link=ls['href']
                elif isinstance(elm['link'],dict):
                    ls=elm['link']['attributes']
                    link=ls['href']
                img=''
                if 'im:image' in elm:
                    img=elm['im:image'][1]
                    img=img['label']
                self.ranking_data.append(AppInfo(aid,r,title,summary,img,link,self.country_code,artist))
        else:
            pass
            #web.debug(type(entries))
            #web.debug(entries)
    def __init__(self,rr,offset,limit):
        self.offset=offset
        self.limit=limit
        self.maxsize=0
        self.country=selector_info.country_list.get(rr['country'],rr['country'])
        self.country_code=rr['country']
        feed=rr['feed']
        self.title=feed['title']['label']
        self.ranking_data=[]
        self.__parseOrder(feed,offset,limit)


class Ranking(object):
    def _get_meta_data(self,mp,fd,to,inputs):
        m=inputs['media']
        f=inputs['field']
        self.media=m
        self.field=f
        self.filtercountry=inputs.get('filtercountry',None)
        dk={"mediatype":m,"fieldtype":f,\
            "fetch_date":{"$lt":to,"$gte":fd}}
        return mp.find_all(mp.RANKING_META_DATA,dk)
    def _get_raw_data(self,mp,raw_id):
        dk={'_id':raw_id}
        raw=mp.is_exists(mp.RANKING_RAW_DATA,dk)
        return raw

    def _get_ranking(self,mp,inputs):
        maxsize=0
        fd=inputs['from']
        to=inputs['to']
        fd=datetime.strptime(fd,'%Y-%m-%d')
        to=datetime.strptime(to,'%Y-%m-%d')
        offset=0
        limit=30
        if 'offset' in inputs and inputs['offset'].isdigit():
            offset=int(inputs['offset'])
        if 'limit' in inputs and inputs['limit'].isdigit():
            limit=int(inputs['limit'])
        self.offset=offset
        self.limit=limit
        self.fd=fd
        self.to=to

        #to=to+timedelta(days=1)
        metas=self._get_meta_data(mp,fd,to,inputs)
        datas=[]
        clist=None
        cset=set()
        if self.filtercountry:
            if self.filtercountry=='G8':
                clist=selector_info.G8
            elif self.filtercountry=='G20':
                clist=selector_info.G20
            elif self.filtercountry=='TOP50':
                clist=selector_info.TOP50
        for r in metas:
            if clist and not r['country'] in clist:
                continue
            if r['country'] in cset:continue

            rr=self._get_raw_data(mp,r['ranking_raw_id'])
            if rr:
                r2=RankingInfo(rr,offset,limit)
                maxsize=max(r2.maxsize,maxsize)
                if r2.ranking_data:
                    datas.append(r2)
            cset.add(r['country'])
        minx=min(maxsize,offset+limit)
        ranknums=[i+1 for i in range(offset,minx)]
        return datas,ranknums,maxsize
    def generate_pagenate(self,maxsize,offset,limit):
        dd=maxsize/limit
        pg=[(i*limit,limit) for i in range(dd)]
        return pg
    def GET(self,*args,**keys):
        d={}
        inputs=web.input()
        mp=web.ctx.mongo
        datas,ranknums,maxsize=self._get_ranking(mp,inputs)
        d['ranknums']=ranknums
        d['maxsize']=maxsize
        d['media']=self.media
        d['field']=self.field
        d['limit']=self.limit
        d['offset']=self.offset
        d['start']=self.offset+1
        d['end']=self.offset+self.limit
        d['fd']=self.fd
        d['to']=self.to
        d['datas']=datas
        d['filtercountry']=self.filtercountry
        d['pg']=self.generate_pagenate(maxsize,self.offset,self.limit)
        return render.ranking(d)
    
class InternationalRanking(Ranking):
    def corss_collect(self,data,limit=30):
        ainfodict={}
        adict={}
        for c in data:
            for a in c.ranking_data:
                aid=a.aid
                ainfodict[aid]=a
                adict.setdefault(aid,set())
                adict[aid].add(c.country_code)
        kk=sorted(adict.items(),key=lambda x:len(x[1]),reverse=True)
        numdict={}
        for a,b in kk:
            sz=len(b)
            if sz>limit:
                numdict.setdefault(sz,[])
                numdict[sz].append(ainfodict[a])
        return sorted(numdict.items(),reverse=True)
            
    def _get_ranking(self,mp,inputs):
        maxsize=0
        fd=inputs['from']
        to=inputs['to']
        fd=datetime.strptime(fd,'%Y-%m-%d')
        to=datetime.strptime(to,'%Y-%m-%d')
        offset=0
        limit=30
        if 'offset' in inputs and inputs['offset'].isdigit():
            offset=int(inputs['offset'])
        if 'limit' in inputs and inputs['limit'].isdigit():
            limit=int(inputs['limit'])
        self.offset=offset
        self.limit=limit
        self.fd=fd
        self.to=to

        #to=to+timedelta(days=1)
        metas=self._get_meta_data(mp,fd,to,inputs)
        datas=[]
        clist=None
        cset=set()
        if self.filtercountry:
            if self.filtercountry=='G8':
                clist=selector_info.G8
            elif self.filtercountry=='G20':
                clist=selector_info.G20
            elif self.filtercountry=='TOP50':
                clist=selector_info.TOP50
        for r in metas:
            if clist and not r['country'] in clist:
                continue
            if r['country'] in cset:continue

            rr=self._get_raw_data(mp,r['ranking_raw_id'])
            if rr:
                r2=RankingInfo(rr,0,300)
                maxsize=max(r2.maxsize,maxsize)
                if r2.ranking_data:
                    datas.append(r2)
            cset.add(r['country'])
        minx=min(maxsize,offset+limit)
        ranknums=[i+1 for i in range(offset,minx)]
        return datas,ranknums,maxsize


    def GET(self,*args,**keys):
        d={}
        inputs=web.input()
        mp=web.ctx.mongo
        datas,ranknums,maxsize=self._get_ranking(mp,inputs)
        sorted_data=self.corss_collect(datas,5)

        d['sorted_data']=sorted_data
        d['ranknums']=ranknums
        d['maxsize']=maxsize
        d['media']=self.media
        d['field']=self.field
        d['limit']=self.limit
        d['offset']=self.offset
        d['start']=self.offset+1
        d['end']=self.offset+self.limit
        d['fd']=self.fd
        d['to']=self.to
        d['datas']=datas
        d['filtercountry']=self.filtercountry
        d['pg']=self.generate_pagenate(maxsize,self.offset,self.limit)
        return render.inter_ranking(d)
class PAppInfo(object):
    def __init__(self,artist):
        self.artist=artist
        self.apdict={}
        self.appdict={}
    def add(self,ainfo,c):
        self.appdict.setdefault(ainfo.aid,ainfo)
        self.apdict.setdefault(ainfo.aid,set())
        self.apdict[ainfo.aid].add(c.country_code)
    def appinfo(self):
        alist=[]
        for a in self.appdict.values():
            aid=a.aid
            csz=len(self.apdict[aid])
            a.csize=csz
            alist.append(a)
        return sorted(alist,key=lambda x:x.csize,reverse=True)
    def cname(self,c):
        return selector_info.country_list.get(c.upper(),c)
    def gen_clist(self):
        cdict={}
        for a in self.apdict:
            cl=self.apdict[a]
            for c in cl:
                cdict.setdefault(c.lower(),0)
                cdict[c.lower()]+=1
        return sorted(cdict.items(),key=lambda x:x[1],reverse=True)

    def size(self):
        cset=set()
        for a in self.apdict:
            cl=self.apdict[a]
            for c in cl:
                cset.add(c)
        return len(cset)
    def web_trim(self,sstr,limit):
        if len(sstr)>limit:
            sstr=sstr[:limit]+'...'
        return sstr


class PublisherRanking(InternationalRanking):
    def publisher_collect(self,data,limit=30):
        padict={}
        for c in data:
            for a in c.ranking_data:
                padict.setdefault(a.artist,PAppInfo(a.artist))
                padict[a.artist].add(a,c)
        kk=sorted(padict.items(),key=lambda x:x[1].size(),reverse=True)
        numdict={}
        for a,b in kk:
            sz=b.size()
            if sz>limit:
                numdict.setdefault(sz,[])
                numdict[sz].append(b)
        return sorted(numdict.items(),reverse=True)

    def GET(self,*args,**keys):
        d={}
        inputs=web.input()
        mp=web.ctx.mongo
        datas,ranknums,maxsize=self._get_ranking(mp,inputs)
        #sorted_data=self.corss_collect(datas,5)
        sorted_data=self.publisher_collect(datas,2)

        d['sorted_data']=sorted_data
        d['ranknums']=ranknums
        d['maxsize']=maxsize
        d['media']=self.media
        d['field']=self.field
        d['limit']=self.limit
        d['offset']=self.offset
        d['start']=self.offset+1
        d['end']=self.offset+self.limit
        d['fd']=self.fd
        d['to']=self.to
        d['datas']=datas
        d['filtercountry']=self.filtercountry
        d['pg']=self.generate_pagenate(maxsize,self.offset,self.limit)
        return render.publisher_ranking(d)


class RankingDate(object):
    def __get_meta_data(self,mp,inputs):
        m=inputs['media']
        f=inputs['field']
        dk={"mediatype":m,"fieldtype":f}
        return mp.find_all(mp.RANKING_META_DATA,dk)

    def __get_ranking(self,mp,inputs):
        metas=self.__get_meta_data(mp,inputs)
        dds={}
        for m in metas:
            dt=m['fetch_date'].strftime("%Y-%m-%d")
            dds.setdefault(dt,0)
            dds[dt]+=1
        tdl=timedelta(days=1)
        date_info={}
        date_info['media']=inputs['media']
        date_info['field']=inputs['field']
        ddsa=[]
        for d in sorted(dds.keys()):
            p=datetime.strptime(d,'%Y-%m-%d')
            n=p+tdl
            ddsa.append((p,n))
        date_info['dates']=ddsa
        return date_info

    def GET(self,*args,**keys):
        d={}
        inputs=web.input()
        mp=web.ctx.mongo
        datas=self.__get_ranking(mp,inputs)
        d['data']=datas
        return render.date(d)
    
