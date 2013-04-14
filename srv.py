#!/usr/bin/python
# -*- coding:utf-8 -*-
import os,sys
currdir=os.path.dirname(__file__)
if not currdir in sys.path:
    sys.path.append(currdir)
    app_path=currdir+os.sep+'../app_store_ranking'
    sys.path.append(app_path)

from datetime import datetime,timedelta
from mog_op import MongoOp,ObjectId
import web
import re
import selector_info
import ranking_info

urls=(
    '/ranking_date.*',ranking_info.RankingDate,
    '/ranking.*',ranking_info.Ranking,
    '/interranking.*',ranking_info.InternationalRanking,
    '/publisherranking.*',ranking_info.PublisherRanking,
    '/.*','Index')

def homepath():
    return web.ctx.homepath
def web_trim(sstr):
    limit=20
    if len(sstr)>limit:
        sstr=sstr[:limit]+'...'
    return sstr

render=web.template.render(currdir+os.sep+'templates',globals={'homepath':homepath,'sorted':sorted,'web_trim:':web_trim})
ranking_info.render=render

def mongo_hook():
    web.ctx.mongo=MongoOp('localhost')
app=web.application(urls,globals())
app.add_processor(web.loadhook(mongo_hook))

class Index(object):
    def cache_chack(self):
        mp=web.ctx.mongo
        cdist=dict(key='front',expired_time={"$gte":datetime.now()})
        rr=mp.is_exists(mp.CACHE_DATA,cdist)
        if rr:
            web.debug("cache hits")
            return rr['body']
        else:
            web.debug("cache hits")
            tpp=self.get_group()
            extime=datetime.now()+timedelta(hours=3)
            cdist=dict(key='front',expired_time=extime,body=tpp)
            mp.save(mp.CACHE_DATA,cdist)
            return tpp
            
    def get_group(self):
        ttp={}
        mp=web.ctx.mongo
        dk={'key':{'country':True,'mediatype':True,'fieldtype':True},
            'condition':{},
            'reduce':'function(prev,obj){}',
            'initial':{'dates':[]}}
        rr=mp.group(mp.RANKING_META_DATA,dk)
        for r in rr:
            ttp.setdefault(r['mediatype'],{})
            ttp[r['mediatype']].setdefault(r['fieldtype'],[])
            ttp[r['mediatype']][r['fieldtype']].append(r['country'])
        return ttp
    def GET(self,*args,**keys):
        d={}
        d['ttp']=self.cache_chack()
        return render.index(d)

def main():
    app.run()
if __name__=='__main__':main()
application=app.wsgifunc()
