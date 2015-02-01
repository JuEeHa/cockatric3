import urllib
import re
import threading

concmd = ['/load_replacetable', '/load_blacklist']

unhtml_replace_lock = threading.Lock()
unhtml_replace = None

blacklist_lock = threading.Lock()
blacklist = None

def load_replacetable():
	global unhtml_replace, unhtml_replace_lock
	
	unhtml_replace_lock.acquire()
	unhtml_replace = {}
	
	f = open("unhtml_replace.txt", 'r')
	
	for line in f:
		if line != '':
			replaced, replacer = line.split()
			unhtml_replace[replaced] = replacer
	
	f.close()
	unhtml_replace_lock.release()

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
	global unhtml_replace, unhtml_replace_lock
	unhtml_replace_lock.acquire()
	
	string = string.replace('\n', ' ').replace('\t', ' ')
	while '  ' in string:
		string = string.replace('  ', ' ')
	
	for i in unhtml_replace:
		if i in string:
			string = string.replace(i, unhtml_replace[i])
	
	unhtml_replace_lock.release()
	return string

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

def parse(args):
	global blacklist, blacklist_lock
	
	line, irc = args
	line = line.split(' ')
	nick = line[0].split('!')[0][1:]
	chan = line[2] if line[2][0]=='#' else nick
	
	if line[1] == 'PRIVMSG':
		message = ' '.join([line[3][1:]] + line[4:])
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
				title = gettitle(f)
				domain = getdomain(url)
				irc.msg(chan, '%s: %s' % (domain, title))
			f.close()

def execcmd(cmd):
	if cmd[0] == '/load_replacetable':
		load_replacetable()
	elif cmd[0] == '/load_blacklist':
		load_blacklist()

load_replacetable()
load_blacklist()
