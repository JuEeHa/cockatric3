import urllib

concmd = []

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
	# TODO: implement unhtmlize
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
	line, irc = args
	line = line.split(' ')
	nick = line[0].split('!')[0][1:]
	chan = line[2] if line[2][0]=='#' else nick
	
	if line[1] == 'PRIVMSG':
		message = ' '.join([line[3][1:]] + line[4:])
		urls = geturls(message)
		for url in urls:
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
	return
