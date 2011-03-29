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
#          Christian Kellner <kellner@biologie.uni-muenchen.de>

import os,stat,errno
import fuse
from fuse import Fuse
from urlparse import urlparse
import urllib
fuse.fuse_python_api = (0, 2)
import threading

watch_mutex = threading.Lock()
bookmarks = {}

def read_bookmarks():
	bm={}
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
		bm[name] = urllib.url2pathname(u.path)
	return bm

def update_bookmarks():
	global bookmarks
	watch_mutex.acquire ()
	bookmarks = read_bookmarks()
	watch_mutex.release ()

try:
	import pyinotify as inotify
	do_watch = True

	class INEventHandler(inotify.ProcessEvent):
		def process_IN_MOVED_TO(self, event):
			path = event.pathname
			fn = os.path.basename (path)
			if not fn == '.gtk-bookmarks':
				return
			update_bookmarks()

except ImportError, e:
	do_watch = False



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

		watch_mutex.acquire ()

		if path == '/':
			st.st_mode = stat.S_IFDIR | 0755
			st.st_nlink = 2
		elif bookmarks.has_key (rel_path):
			st.st_mode = stat.S_IFLNK | 0777
			st.st_nlink = 1
			st.st_uid = os.getuid()
			st.st_gid = os.getgid()
		else:
			st = -errno.ENOENT

		watch_mutex.release ()
		return st

	def readdir(self, path, offset):
		ret = ['.',
		'..',]

		watch_mutex.acquire ()
	
		bk = [value for value in read_bookmarks().keys()]
		ret += bk
		for r in ret:
			yield fuse.Direntry(r)
		watch_mutex.release ()


	def readlink (self, path):
		rel_path = path[1:]

		watch_mutex.acquire ()

		if not bookmarks.has_key (rel_path):
			watch_mutex.release ()
			return -errno.ENOENT

		linkpath = bookmarks[rel_path]
		watch_mutex.release ()

		return linkpath

def main():
	print 'Bookmark FS (c) 2011 G-Node\n'
	usage="""
	Expose GTK+ Bookmarks as filesystem

	""" + Fuse.fusage
	server = BookmarkFS(version="%prog " + fuse.__version__,
	usage=usage,
	dash_s_do='setsingle')

	server.parse(values=server, errex=1)

	if do_watch:
		wm = inotify.WatchManager() 
		mask = inotify.IN_MOVED_TO

		notifier = inotify.ThreadedNotifier(wm, INEventHandler())
		notifier.start()
		wdd = wm.add_watch(os.path.expanduser ('~'), mask)
	
	update_bookmarks()
	
	server.main()

	if do_watch:
		wm.rm_watch(wdd.values())
		notifier.stop()

if __name__=='__main__':
	main()
