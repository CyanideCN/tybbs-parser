from dataclasses import dataclass
import datetime
from typing import Optional, List, Union
import os
from os.path import exists, join
from io import BytesIO

import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')

@dataclass
class _Floor(object):
    serial: str
    user: str
    time: datetime.datetime
    content: list
    floor_info: dict
    pic: Optional[List[str]]

class Floor(_Floor):
    def __init__(self, serial:str, user:str, time:datetime.datetime, content:list,
                 floor_info:dict, pic:Optional[List[str]]=None):
        super().__init__(serial, user, time, content, floor_info, pic)

    def download_pic(self) -> list:
        if not self.pic:
            return
        self.pic = [i for i in self.pic if i]
        if not self.pic:
            return
        tid = self.floor_info['tid']
        img_list = list()
        target_dir = join(CACHE_DIR, str(tid))
        if not exists(target_dir):
            os.mkdir(target_dir)
        for idx, url in enumerate(self.pic):
            ext_name = url.split('.')[-1]
            target_fn = '_'.join([self.serial, str(idx)]) + '.' + ext_name
            pic_fn = join(target_dir, target_fn)
            if exists(pic_fn):
                f = open(pic_fn, 'rb')
                img_list.append(f)
            else:
                try:
                    req = requests.get(url)
                except Exception:
                    print('Download {} failed'.format(url))
                    img_list.append(BytesIO())
                    continue
                # Success check?
                img_list.append(BytesIO(req.content))
                try:
                    f = open(pic_fn, 'wb')
                except Exception:
                    print('Create file {} failed'.format(pic_fn))
                    img_list.append(BytesIO())
                    continue
                f.write(req.content)
                f.close()
        return img_list