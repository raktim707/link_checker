from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from tldextract import extract
from openpyxl import load_workbook
import os.path

url = input('Enter the domain/url: ')

depth = input('set limit to link depth to follow (e.g: 1, 2 or 3): ')
try:
	depth = int(depth)
except:
	depth=5
external_follow = input('Do you want to follow external links (default is no)? y/n : ')
if external_follow in ['y', 'Y']:
	ext_depth=input('set limit to external link depth to follow (e.g: 0, 1, 2 or 3): ')
	ext_depth = int(ext_depth)
full_domain = urlparse(url).netloc
domain = extract(url, include_psl_private_domains=True).domain
print(domain)
file_exists = os.path.exists(domain+'.txt')

prev_total_links = None
prev_total_outbound = None
if file_exists == True:
	file1 = open(domain+'.txt', 'r')
	l = file1.readlines()
	for i in range(len(l)):
		if l[i] == '**** Total Inbound Links ****\n':
			prev_total_links = l[i+2]
		if l[i] == '**** Total Outbound Links ****\n':
			prev_total_outbound = l[i+2]
	file1.seek(0)
	myTxt = file1.read()
	my_intern_links = myTxt[:myTxt.find('**** Outbound Links')].splitlines()
	if my_intern_links != []:
		my_intern_links.remove(my_intern_links[0])
		my_intern_links.remove(my_intern_links[0])
		prev_intern_links=[]
		for item in my_intern_links:
			prev_intern_links.append(item.split('\t')[0])
	my_outbound_links = myTxt[myTxt.find('**** Outbound Links'):myTxt.find('**** Total Inbound Links')].splitlines()
	if my_outbound_links != []:
		my_outbound_links.remove(my_outbound_links[0])
		my_outbound_links.remove(my_outbound_links[0])
		prev_outbound_links=[]
		for item in my_outbound_links:
			prev_outbound_links.append(item.split('\t')[0])
			
	file1.close()
		
	

s = requests.Session()
global recurr_urls
global ext_recurr_urls

recurr_urls ={}
ext_recurr_urls = {}

def link_extractor(url, domain=domain, full_domain=full_domain):
    try:
    	page = s.get(url, timeout=3)
    except:
    	page=None
    if page is not None:
    	all_urls = []
    	outbound_urls = []
    	try:
    		soup = BeautifulSoup(page.content, 'html.parser')
    	except:
    		soup= None
    	if soup is not None:
    		for tag in soup.find_all('a'):
    			if tag.get('href') is not None:
    				if extract(tag.get('href'), include_psl_private_domains=True).domain == '':
    					url = full_domain + tag.get('href')
    				elif extract(tag.get('href'), include_psl_private_domains=True).domain != domain:
    					outbound_urls.append(tag.get('href'))
    				else:
    					url = tag.get('href')
    				if len(all_urls) < 300:
    					all_urls.append(url)
    		for tag in soup.find_all(['script', 'img', 'link']):
    			if (tag.has_attr('src')):
    				if tag.get('src') is not None:
    					if extract(tag.get('src'), include_psl_private_domains=True).domain == '':
    						url = full_domain + tag.get('src')
    					elif extract(tag.get('src'), include_psl_private_domains=True).domain != domain:
    						outbound_urls.append(tag.get('src'))
    					else:
    						url = tag.get('src')
    					all_urls.append(url)
    			elif (tag.has_attr('href')):
    				if tag.get('href') is not None:
    					if extract(tag.get('href'), include_psl_private_domains=True).domain == '':
    						url = full_domain + tag.get('href')
    					elif extract(tag.get('href'), include_psl_private_domains=True).domain != domain:
    						outbound_urls.append(tag.get('href'))
    					all_urls.append(url)
    		return [all_urls, outbound_urls]
    	else:
    		return [[],[]]
    else:
    	return [[],[]]


def scrape_all_links(all_url, depth=5, ext='n'):
    if depth != 0:
        print('Scraping Links....Please wait....')
        if ext != 'y':
            recurr_urls[depth] = []
        elif ext == 'y':
            ext_recurr_urls[depth]=[]
        if type(all_url) is list:
            for url in all_url:
                if url.startswith('www'):
                    url = 'http://' + url
                elif url.startswith('//'):
                	url = 'http:' + url
                if ext != 'y':
                	recurr_urls[depth].append(link_extractor(url)[0])
                elif ext == 'y':
                	ext_recurr_urls[depth].append(link_extractor(url)[1])
        elif type(all_url) is dict:
            for list_url in all_url[depth+1]:
                for item in list_url:
                	if item.startswith('www'):
                		item = 'http://' + item
                	elif item.startswith('//'):
                		item = 'http:' + item	
                	if ext != 'y':
                		recurr_urls[depth].append(link_extractor(item)[0])
                	elif ext == 'y':
                		ext_recurr_urls[depth].append(link_extractor(item)[1])
        depth = depth - 1
        if ext != 'y':
        	scrape_all_links(recurr_urls, depth)
        elif ext == 'y':
        	scrape_all_links(ext_recurr_urls, depth)
        print('Scraping Links....Please wait....')
    else:
    	if ext != 'y':
        	return recurr_urls
    	elif ext == 'y':
        	return ext_recurr_urls



urls = link_extractor(url)

all_urls=list(set(urls[0]))
if depth > 0:
	print('Following link depth')
	depth_urls = scrape_all_links(all_urls, depth=depth)
else:
	depth_urls=None


outbound_urls = list(set(urls[1]))

if external_follow in ['y', 'Y']:
	if int(ext_depth) > 0:
		scrape_all_links(outbound_urls, depth=ext_depth, ext='y')


file1 = open(domain+'.txt', 'w')
row=2
response_codes=[]
all_broken_links = []
file1.writelines('**** Internal Links ****\n\n')

'''for i in range(row, len(all_urls)+row):
    if all_urls[i-row].startswith('www'):
    	url = 'http://' + all_urls[i-row]
    else:
    	url = all_urls[i-row]
    try:
    	page=s.get(url, timeout=3)
    	status_code = page.status_code
    	response_codes.append(str(page.status_code))
    	if status_code == 404:
    		all_broken_links.append(url)
    except:
    	all_broken_links.append(url)
    	status_code = 404
    	response_codes.append(str(404))
    file1.writelines([url+'\t', str(status_code)+'\n'])
    print('internal_url:%s \t %s '%(url, str(status_code)))'''


count=0

all_ele = []
if recurr_urls != {}:
	for key in recurr_urls:
		for item in recurr_urls[key]:
			for i in item:
				all_ele.append(i)

	all_ele = list(set(all_ele))
for item in all_urls:
	all_ele.append(item)
all_ele = list(set(all_ele))
count=len(all_ele)
start_row = len(all_urls)+row

if count != 0:
	for i in range(start_row, count+start_row):
		if all_ele[i-start_row].startswith('www'):
			url = 'http://'+all_ele[i-start_row]
		else:
			url = all_ele[i-start_row]
		try:
			page=s.get(url, timeout=2)
			status_code = page.status_code
			if status_code == 404:
				all_broken_links.append(url)
			response_codes.append(str(page.status_code))
		except:
			status_code = 404
			all_broken_links.append(url)
			response_codes.append(str(404))
		file1.writelines([all_ele[i-start_row]+'\t', str(status_code)+'\n'])
		print('internal_url:%s \t %s '%(url, str(status_code)))


total_links = count


file1.writelines('**** Outbound Links ****\n\n')
'''for i in range(2, total_outbound_links + 2):
	if outbound_urls[i-2].startswith('www'):
		url = 'http://' + outbound_urls[i-2]
	else:
		url = outbound_urls[i-2]
	try:
		page=s.get(url, timeout=3)
		status_code = page.status_code
		if status_code == 404:
			all_broken_links.append(url)
		response_codes.append(str(page.status_code))
	except:
		all_broken_links.append(url)
		status_code = 404
		response_codes.append(str(404))
	file1.writelines([url+'\t', str(status_code)+'\n'])
	print('external_url: %s \t %s'%(url, str(status_code)))'''


ext_ele = []
if ext_recurr_urls !={}:
	for key in ext_recurr_urls:
		for item in ext_recurr_urls[key]:
			for i in item:
				ext_ele.append(i)

for item in outbound_urls:
	ext_ele.append(item)
ext_ele = list(set(ext_ele))
total_outbound_links = len(ext_ele)

if len(ext_ele) > 0:
	new_start = total_outbound_links + 2
	for i in range(new_start, len(ext_ele)+new_start):
		if ext_ele[i-new_start].startswith('www'):
			url= 'http://' + ext_ele[i-new_start]
		elif ext_ele[i-new_start].startswith('//'):
			url = 'http:'+ ext_ele[i-new_start]
		else:
			url = ext_ele[i-new_start]
		try:
			page = s.get(url, timeout=2)
			status_code = page.status_code
			if status_code == 404:
				all_broken_links.append(url)
			response_codes.append(str(page.status_code))
		except:
			status_code = 404
			all_broken_links.append(url)
			response_codes.append(str(404))
		file1.writelines([ext_ele[i-new_start]+'\t', str(status_code)+'\n'])
		print('external_url: %s \t %s'%(url, str(status_code)))


file1.writelines('\n**** Total Inbound Links ****\n\n')
file1.writelines(str(total_links))
print('Total Internal Links: ', total_links)

file1.writelines('\n**** Total Outbound Links ****\n\n')
file1.writelines (str(total_outbound_links))
print('Total external Links: ', total_outbound_links)

file1.writelines('\n**** All Broken Links ****\n\n')
for url in all_broken_links:
	file1.writelines(url+'\n')

codes=list(set(response_codes))
total_codes=[]
file1.writelines('\n**** Count of Response Codes ****\n\n')
file1.writelines('Response Code | Count\n\n')
for i in range(len(codes)):
	file1.writelines([codes[i]+'\t |', str(response_codes.count(codes[i]))+'\n'])
	print('Response Code: %s, Count: %s'%(codes[i],  response_codes.count(codes[i])))

if file_exists == True:
	if my_intern_links != []:
		new_intern = set(all_ele) - set(prev_intern_links)
		if len(new_intern) !=0:
			file1.writelines('\nAdded internal links (+)\n\n')
			for url in new_intern:
				file1.writelines(url+'\n')
		removed_intern = set(prev_intern_links) - set(all_ele)
		if len(removed_intern) !=0:
			file1.writelines('\nRemoved internal Links (-)\n\n')
			for url in removed_intern:
				file1.writelines(url + '\n')
	if my_outbound_links != []  and len(ext_ele) !=0:
		new_extern = set(ext_ele) - set(prev_outbound_links)
		removed_extern = set(prev_outbound_links) - set(ext_ele)
		
		if len(new_extern) != 0:
			file1.writelines('\nAdded External Links (+)\n\n')
			for url in new_extern:
				file1.writelines(url + '\n')
		
		if len(removed_extern) != 0:
			file1.writelines('\nRemoved External Links (-)\n\n')
			for url in removed_extern:
				file1.writelines(url+'\n')
	print("Previous total internal links: ", prev_total_links)
	print("previous total outbound links: ", prev_total_outbound)
file1.close()
