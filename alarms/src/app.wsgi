import os
import sys

dir=os.path.dirname(__file__)
os.chdir(dir)
sys.path.append(dir)

from main import app as application
import logging

file_handler = logging.FileHandler('../../logs/flask.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
application.logger.addHandler(file_handler)

phone_logger = logging.getLogger('isadore_alarms.phone_logger')
pfile_handler = logging.FileHandler('../../logs/phone.log')
pfile_handler.setLevel(logging.INFO)
phone_logger.setLevel(logging.INFO)
pfile_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
phone_logger.addHandler(pfile_handler)

