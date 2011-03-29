#!/usr/bin/env python

# Copyright (c) 2011 INCF G-Node
#
# GNU General Public Licence (GPL)
# 
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Philipp Rautenberg <philipp.rautenberg@g-node.org>
#          	Christian Kellner <kellner@biologie.uni-muenchen.de>


import os,stat,errno
import fuse
from fuse import Fuse
from urlparse import urlparse
import urllib
fuse.fuse_python_api = (0, 2)


def read_bookmarks():
	bookmarks={}
	f = open (os.path.expanduser ('~/.gtk-bookmarks'))
	for line in f:
		pos = str.find (line, ' ')
		url = line[0:pos]
		u = urlparse(url)
		if not u.scheme == 'file':
			continue

		if pos == -1:
			name = os.path.basename (u.path)
		else:
			name = line[pos + 1: -1];
		bookmarks[name] = urllib.url2pathname(u.path)
	return bookmarks

bookmarks = read_bookmarks()

class MyStat(fuse.Stat):
	def __init__(self):
		self.st_mode=0
		self.st_ino=0
		self.st_dev=0
		self.st_nlink=0
		self.st_uid=0
		self.st_gid=0
		self.st_size=0
		self.st_atime=0
		self.st_mtime=0
		self.st_ctime=0

class BookmarkFS(Fuse):
	flags = 1
	def getattr(self, path):
		rel_path = path[1:]
		st = MyStat()
		if path == '/':
			st.st_mode = stat.S_IFDIR | 0755
			st.st_nlink = 2
		elif bookmarks.has_key (rel_path):
			st.st_mode = stat.S_IFLNK | 0777
			st.st_nlink = 1
			st.st_uid = os.getuid()
			st.st_gid = os.getgid()
		else:
			return -errno.ENOENT
		return st

	def readdir(self, path, offset):
		ret = ['.',
		'..',]
		
		bk = [value for value in read_bookmarks().keys()]
		ret += bk
		print ret
		for r in ret:
			yield fuse.Direntry(r)


	def readlink (self, path):
        	print '*** readlink', path
		rel_path = path[1:]
		if not bookmarks.has_key (rel_path):
			return -errno.ENOENT

		linkpath = bookmarks[rel_path]
		return linkpath

def main():
	print 'Bookmark FS (c) 2011 G-Node\n'
	print bookmarks
	usage="""
	Userspace hello example

	""" + Fuse.fusage
	server = BookmarkFS(version="%prog " + fuse.__version__,
	usage=usage,
	dash_s_do='setsingle')

	server.parse(values=server, errex=1)
	server.main()

if __name__=='__main__':
	main()
