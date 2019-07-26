#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

#TODO: Make this an ant java task instead
import glob
import re
import hashlib
import sys
import os
import errno

def md5file(filePath):
	f = open(filePath, 'r')
	md5 = hashlib.md5()
	while True:
		data=f.read(md5.block_size)
		if(not data):
			break
		md5.update(data)
	f.close()
	return md5.hexdigest()

def fingerPathReplace(line, m, hash, file):
	ret = []
	ret.append(line[0:m.start(1)])
	ret.append(os.path.dirname(file)+"/")
	name = os.path.splitext(os.path.basename(file))
	ret.append(name[0])
	ret.append("__")
	ret.append(hash)
	ret.append(name[1])
	ret.append(line[m.end(1):])
	return ''.join(ret)

def mkdir_p(dir):
	if not os.path.exists(os.path.dirname(dir)):
		os.makedirs(os.path.dirname(dir))

def myGlob(path, ext):
	myfiles=[]
	for root, dirs, files in os.walk(path):
		for file in files:
			for e in ext:
				if(file.endswith(e)):
					myfiles.append(os.path.join(root, file))
	return myfiles
		
def genFingerMap():
	ourMap={}
	files = myGlob('./src', ['js', 'css'])
	files.extend(myGlob('./build', ['js', 'css']))
	for file in files:
		base = os.path.basename(file)
		if(base in ourMap):
			raise Exception('Duplicate file: %s' % base)
		ourMap[base]=md5file(file)
	return ourMap
		

files = myGlob('./src', ['html', 'tpl'])
fingerPatterns = [re.compile('href *?= *?"(.*?.css)"'), re.compile('src *?= *?"(.*?.js)"')]
fingerHashMaps = genFingerMap()
for file in files:
	f = open(file, 'r')
	newFilePath = './build/'+file
	mkdir_p(newFilePath)
	newf = open(newFilePath, 'w')
	for line in f:
		pFound = False
		for pattern in fingerPatterns:
			m = pattern.search(line)
			if m:
				fingerFileName = m.group(1)
				hash = fingerHashMaps[os.path.basename(fingerFileName)]
				newf.write(fingerPathReplace(line, m, hash, fingerFileName))
				pFound=True
				break
		if not pFound:
			newf.write(line)
	newf.close()
	f.close()
