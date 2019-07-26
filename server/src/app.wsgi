import os
import sys
import logging
dir=os.path.dirname(__file__)
os.chdir(dir)
sys.path.append(dir)

timeLogger = logging.getLogger('timeLogger')
timeLoggerHandler = logging.FileHandler('../../logs/time.log')
timeLoggerHandler.setLevel(logging.INFO)
timeLogger.addHandler(timeLoggerHandler)


logging.basicConfig(filename='../../logs/bottle.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

import bottle
from beaker.middleware import SessionMiddleware
bottle.debug(True)
app = bottle.default_app()
session_opts = {
	'session.type': 'file',
	'session.cookie_expires': 300,
	'session.data_dir': './sessions',
	'session.auto': True
}
application=SessionMiddleware(app, session_opts)

import isadore_main
