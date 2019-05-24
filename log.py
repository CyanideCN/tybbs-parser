import logging
import datetime

logger = logging.getLogger('tybbs-parser')
handler = logging.FileHandler('logs/{}.log'.format(datetime.datetime.now().strftime('%Y%m%d')))
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)