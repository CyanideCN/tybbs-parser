import re
import datetime

import requests
from bs4 import BeautifulSoup

from log import logger
from container import Floor

#http://bbs.typhoon.org.cn/read.php?tid=78682&fid=70&page=e#a

TID = re.compile('tid=[0-9]*')
FID = re.compile('fid=[0-9]*')
BASE_URL = 'http://bbs.typhoon.org.cn/read.php?tid={}&fid={}'
INSERT_PIC = 1

def parse_text(text_list:list) -> list:
    out = list()
    for txt in text_list:
        if isinstance(txt, str):
            txt_strip = txt.strip()
            if txt_strip:
                out.append(txt_strip)
        else:
            if hasattr(txt, 'attrs'):
                att = txt.attrs
                if 'class' in att.keys():
                    if 'J_post_img' in att['class']:
                        return [INSERT_PIC]
            if hasattr(txt, 'contents'):
                out_a = parse_text(txt.contents)
                for o in out_a:
                    out.append(o)
    return out

def parse_img_url(editor_content:list) -> list:
    out = list()
    for ed in editor_content:
        trial = ed.find_all(attrs={'class':'J_post_img J_lazy'})
        if trial:
            out.append([i.attrs['data-original'] for i in trial])
        else:
            out.append(None)
    return out

def find_tid(url:str) -> int:
    return int(re.sub('tid=', '', re.findall(TID, url)[0]))

class Thread(object):
    def __init__(self, url:str, start_page:int=1):
        self.url = url
        self.tid = find_tid(url)
        self.fid = start_page

    def load_page(self, pagenum:int) -> list:
        '''Load a single page, return a list of floors when success'''
        logger.info('Open thread {}, page {}'.format(self.tid, pagenum))
        req = requests.get(BASE_URL.format(self.tid, pagenum))
        # post process
        soup = BeautifulSoup(req.content)
        title = soup.find_all('title')[0].next_element
        ff = soup.find_all(attrs={'class':'editor_content'})
        users = soup.find_all(attrs={'class':'J_user_card_show mr5'})
        post_time = soup.find_all(attrs={'class':'fl'})
        serial = soup.find_all(attrs={'class':'lou J_floor_copy'})

        user_string = [i.contents[0] for i in users]
        post_time_dt = [datetime.datetime.strptime(i.replace('发布于：', ''), '%Y-%m-%d %H:%M') for i in parse_text(post_time)]
        post_content = [parse_text(i.contents) for i in ff]
        floor_serial = parse_text(serial)[::2]
        img_url = parse_img_url(ff)

        ret = list()
        for num in range(len(floor_serial)):
            ret.append(Floor(floor_serial[num], user_string[num], post_time_dt[num], post_content[num],
                             {'tid':self.tid}, pic=img_url[num]))
        return ret