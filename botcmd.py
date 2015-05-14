import urllib
import re
import threading
import HTMLParser

concmd = ['/load_blacklist']

blacklist_lock = threading.Lock()
blacklist = None

html_unescape = HTMLParser.HTMLParser().unescape

def load_blacklist():
	global blacklist, blacklist_lock
	blacklist_lock.acquire()
	blacklist = []
	
	f = open("blacklist.txt", 'r')
	
	for line in f:
		while line != '' and  line[-1] == '\n':
			line = line[:-1]
		if line != '':
			blacklist.append(re.compile('^' + line + '$'))
	
	f.close()
	blacklist_lock.release()

def matchprotocol(string, protocol):
	return len(protocol) <= len(string) and string[:len(protocol)] == protocol

def getdomain(string):
	string = string[string.index('://') + len('://'):]
	return string[:string.index('/')]

def geturls(message):
	protocols = ['http://', 'https://']
	
	urls = []
	# TODO: add support for other separators
	for element in message.split():
		for protocol in protocols:
			if matchprotocol(element, protocol):
				urls.append(element)
				break
	
	return urls

def unhtmlize(string):
	string = string.replace('\n', ' ').replace('\t', ' ')
	while '  ' in string:
		string = string.replace('  ', ' ')
	return html_unescape(string.decode('utf-8')).encode('utf-8')

def gettitle(f):
	page = f.read()
	if '<title>' not in page:
		return None
	page = page[page.index('<title>') + len('<title>'):]
	if '</title>' not in page:
		title = page
	else:
		title = page[:page.index('</title>')]
	return unhtmlize(title)

def sanitize(string):
	for i in ['\n', '\r'] + [chr(i) for i in range(32)]:
		string = string.replace(i, '')
	return string

def parse((line, irc)):
	global blacklist, blacklist_lock
	zwsp = '\xe2\x80\x8b'
	
	line = line.replace('\x01', '').split(' ')
	nick = line[0].split('!')[0][1:]
	chan = line[2] if line[2][0]=='#' else nick
	
	if line[1] == 'PRIVMSG':
		message = ' '.join([line[3][1:]] + line[4:])
		
		if message[:len(zwsp)] == zwsp:
			return
		
		urls = geturls(message)
		for url in urls:
			blacklisted = False
			blacklist_lock.acquire()
			for i in blacklist:
				if i.match(url):
					blacklisted = True
					break
			blacklist_lock.release()
			if blacklisted:
				continue
			
			try:
				f = urllib.urlopen(url)
			except IOError:
				continue
			
			if f.info().gettype() == 'text/html':
				title = sanitize(gettitle(f))
				domain = sanitize(getdomain(url))
				irc.msg(chan, zwsp + '%s: %s' % (domain, title))
			f.close()

def execcmd(cmd):
	if cmd[0] == '/load_blacklist':
		load_blacklist()

load_blacklist()
