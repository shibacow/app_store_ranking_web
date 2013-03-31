#!/usr/bin/python
# -*- coding:utf-8 -*-
import os,sys
currdir=os.path.dirname(__file__)
if not currdir in sys.path:
    sys.path.append(currdir)
    app_path=currdir+os.sep+'../app_store_ranking'
    sys.path.append(app_path)

from datetime import datetime
from mog_op import MongoOp,ObjectId
import web
import re
import selector_info
import ranking_info

urls=(
    '/ranking_date.*',ranking_info.RankingDate,
    '/ranking.*',ranking_info.Ranking,
    '/.*','Index')

def homepath():
    return web.ctx.homepath
render=web.template.render(currdir+os.sep+'templates',globals={'homepath':homepath})
ranking_info.render=render

def mongo_hook():
    web.ctx.mongo=MongoOp('localhost')
app=web.application(urls,globals())
app.add_processor(web.loadhook(mongo_hook))

class Index(object):
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
            ttp[r['mediatype']].setdefault(r['fieldtype'],set())
            ttp[r['mediatype']][r['fieldtype']].add(r['country'])
        return ttp
    def GET(self,*args,**keys):
        d={}
        d['ttp']=self.get_group()
        return render.index(d)

def main():
    app.run()
if __name__=='__main__':main()
application=app.wsgifunc()
