from dataclasses import dataclass
import datetime
from typing import Optional, List, Union
import os
from os.path import exists, join
from io import BytesIO

import requests

from log import logger

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
        tid = self.floor_info['tid']
        img_list = list()
        target_dir = join(CACHE_DIR, str(tid))
        if not exists(target_dir):
            os.mkdir(target_dir)
        for idx, url in enumerate(self.pic):
            ext_name = url.split('.')[-1]
            target_fn = '_'.join([self.serial, str(idx)]) + ext_name # File format to be determined
            pic_fn = join(target_dir, target_fn)
            if exists(pic_fn):
                with open(pic_fn, 'rb') as buf:
                    img_list.append(buf)
                logger.debug('Picture found at {}'.format(pic_fn))
            else:
                logger.debug('Download picture ... {}'.format(url))
                req = requests.get(url)
                # Success check?
                img_list.append(BytesIO(req.content))
                f = open(pic_fn, 'wb')
                f.write(req.content)
                f.close()
        return img_list