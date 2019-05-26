import re
import datetime

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString

from container import Floor

headers = {'Referer': 'http://bbs.typhoon.org.cn/',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}

#http://bbs.typhoon.org.cn/read.php?tid=78682&fid=70&page=e#a

TID = re.compile('tid=[0-9]*')
FID = re.compile('fid=[0-9]*')
DATE = re.compile('发布于：[0-9]*-[0-9]*-[0-9]* [0-9]*:[0-9]*')
BASE_URL = 'http://bbs.typhoon.org.cn/read.php?tid={}&page={}'
INSERT_PIC = 1

def parse_text(text_list:list) -> list:
    out = list()
    for txt in text_list:
        if isinstance(txt, (str, NavigableString)):
            txt_strip = txt.strip()
            if txt_strip:
                out.append(txt_strip)
        else:
            if hasattr(txt, 'attrs'):
                att = txt.attrs
                if 'class' in att.keys():
                    if 'J_post_img' in att['class']:
                        return [INSERT_PIC]
                    if 'blockquote' in att['class']:
                        continue
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
        self.max_page = self._max_page()

    def load_page(self, pagenum:int) -> list:
        '''Load a single page, return a list of floors when success'''
        req = requests.get(BASE_URL.format(self.tid, pagenum), headers=headers)
        # post process
        soup = BeautifulSoup(req.content, 'html5lib')
        title_p = soup.find_all(attrs={'class':'floor_title cc'})
        if title_p:
            title = title_p[0].find('h1').contents[-1]
        else:
            title = None
        ff = soup.find_all(attrs={'class':'editor_content'})
        users = soup.find_all(attrs={'class':'J_user_card_show mr5'})
        post_time = soup.find_all(attrs={'class':'floor_top_tips cc'})
        serial = soup.find_all(attrs={'class':'lou J_floor_copy'})

        quote_list = list()
        for f in ff:
            quote_t = f.find_all('blockquote')
            if quote_t:
                if not hasattr(quote_t[0].next_element, 'contents'):
                    raw_quote = parse_text(quote_t[0].contents)
                    quote_list.append(('Quote', ''.join([i for i in raw_quote if isinstance(i, (str, NavigableString))])))
                else:
                    if not quote_t[0].next_element.contents:
                        raw_quote = parse_text(quote_t[0].contents)
                        quote_list.append(('Quote', ''.join([i for i in raw_quote if isinstance(i, (str, NavigableString))])))
                    else:
                        quote_list.append((quote_t[0].next_element.contents[0].contents[0],
                                           quote_t[0].next_element.contents[-1]))
            else:
                quote_list.append(None)

        user_string = [i.contents[0] for i in users]
        time_t = ' '.join(parse_text(post_time))
        time_find = re.findall(DATE, time_t)
        post_time_dt = [datetime.datetime.strptime(i.replace('发布于：', ''), '%Y-%m-%d %H:%M') for i in time_find]
        post_content = [parse_text(i.contents) for i in ff]
        floor_serial = parse_text(serial)[::2]
        img_url = parse_img_url(ff)

        ret = list()
        for num in range(len(floor_serial)):
            ret.append(Floor(floor_serial[num], user_string[num], post_time_dt[num], post_content[num],
                             {'tid':self.tid, 'title':title, 'quote':quote_list[num]}, pic=img_url[num]))
        return ret

    def _max_page(self):
        req = requests.get(BASE_URL.format(self.tid, 1), headers=headers)
        soup = BeautifulSoup(req.content, 'html5lib')
        page_t = parse_text(soup.find_all(attrs={'class':'pages'}))
        num = [int(i) for i in page_t if i.isalnum()]
        return max(num)

    def load_all(self):
        for pn in range(1, self.max_page + 1):
            yield self.load_page(pn)

    def load_range(self, start, end):
        for i in range(start, end):
            yield self.load_page(i)