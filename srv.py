#!/usr/bin/python
# -*- coding:utf-8 -*-
import os,sys
sys.path.append('../app_store_ranking')
from datetime import datetime
from mog_op import MongoOp,ObjectId
import web
import re
import selector_info
urls=(
    '/ranking.*','Ranking',
    '/.*','Index')

render=web.template.render('templates')

def mongo_hook():
    web.ctx.mongo=MongoOp('localhost')
app=web.application(urls,globals())
app.add_processor(web.loadhook(mongo_hook))

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
            web.debug(type(entries))
            web.debug(entries)
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
        metas=self.__get_meta_data(mp,fd,to,inputs)
        datas=[]
        for r in metas:
            rr=self.__get_raw_data(mp,r['ranking_raw_id'])
            r=RankingInfo(rr)
            if r.ranking_data:
                datas.append(r)
        return datas
    def GET(self,*args,**keys):
        d={}
        inputs=web.input()
        mp=web.ctx.mongo
        datas=self.__get_ranking(mp,inputs)
        d['datas']=datas
        return render.ranking(d)
    
class Index(object):
    def get_group_date(self,fd,to):
        ttp={}
        mp=web.ctx.mongo
        dk={'key':{'country':True,'mediatype':True,'fieldtype':True},
            'condition':{'fetch_date':{'$lt':to,'$gte':fd}},
            'reduce':'function(prev,obj){}',
            'initial':{'dates':0}}
        rr=mp.group(mp.RANKING_META_DATA,dk)
        for r in rr:
            ttp.setdefault(r['mediatype'],{})
            ttp[r['mediatype']].setdefault(r['fieldtype'],set())
            ttp[r['mediatype']][r['fieldtype']].add(r['country'])
        return ttp
    def GET(self,*args,**keys):
        d={}
        fd=datetime(2013,1,13)
        to=datetime(2013,2,19)
        d['fd']=fd
        d['to']=to
        d['ttp']=self.get_group_date(fd,to)
        return render.index(d)

def main():
    app.run()
if __name__=='__main__':main()
