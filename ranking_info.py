import os,sys
sys.path.append('../app_store_ranking')
from datetime import datetime,timedelta
from mog_op import MongoOp,ObjectId
import web
import re
import selector_info

class RankingInfo(object):
    def __parseOrder(self,feed):
        if not 'entry' in feed:
            return
        entries=feed['entry']
        limit=30
        if isinstance(entries,list):
            if len(entries)>limit:
                entries=entries[:limit]
            for i,elm in enumerate(entries):
                r=i+1
            #web.debug(elm)
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
                self.ranking_data.append(dict(rank=r,title=title,summary=summary,img=img,link=link))
        else:
            pass
            #web.debug(type(entries))
            #web.debug(entries)
    def __init__(self,rr):
        self.country=selector_info.country_list.get(rr['country'],rr['country'])
        feed=rr['feed']
        self.title=feed['title']['label']
        self.ranking_data=[]
        self.__parseOrder(feed)


class Ranking(object):
    def __get_meta_data(self,mp,fd,to,inputs):
        m=inputs['media']
        f=inputs['field']
        self.media=m
        self.field=f
        self.filtercountry=inputs.get('filtercountry',None)
        dk={"mediatype":m,"fieldtype":f,\
            "fetch_date":{"$lt":to,"$gte":fd}}
        return mp.find_all(mp.RANKING_META_DATA,dk)
    def __get_raw_data(self,mp,raw_id):
        dk={'_id':raw_id}
        raw=mp.is_exists(mp.RANKING_RAW_DATA,dk)
        return raw

    def __get_ranking(self,mp,inputs):
        fd=inputs['from']
        to=inputs['to']
        fd=datetime.strptime(fd,'%Y-%m-%d')
        to=datetime.strptime(to,'%Y-%m-%d')
        #to=to+timedelta(days=1)
        metas=self.__get_meta_data(mp,fd,to,inputs)
        datas=[]
        clist=None
        cset=set()
        if self.filtercountry:
            if self.filtercountry=='G8':
                clist=selector_info.G8
            elif self.filtercountry=='G20':
                clist=selector_info.G20
        for r in metas:
            if clist and not r['country'] in clist:
                continue
            if r['country'] in cset:continue

            rr=self.__get_raw_data(mp,r['ranking_raw_id'])
            if rr:
                r2=RankingInfo(rr)
                if r2.ranking_data:
                    datas.append(r2)
            cset.add(r['country'])
        return datas
    def GET(self,*args,**keys):
        d={}
        inputs=web.input()
        mp=web.ctx.mongo
        datas=self.__get_ranking(mp,inputs)
        d['media']=self.media
        d['field']=self.field
        d['datas']=datas
        return render.ranking(d)
    
class RankingDate(object):
    def __get_meta_data(self,mp,fd,to,inputs):
        m=inputs['media']
        f=inputs['field']
        dk={"mediatype":m,"fieldtype":f,\
            "fetch_date":{"$lt":to,"$gte":fd}}
        return mp.find_all(mp.RANKING_META_DATA,dk)

    def __get_ranking(self,mp,inputs):
        fd=inputs['from']
        to=inputs['to']
        fd=datetime.strptime(fd,'%Y-%m-%d')
        to=datetime.strptime(to,'%Y-%m-%d')
        to=to+timedelta(days=1)
        metas=self.__get_meta_data(mp,fd,to,inputs)
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
    
