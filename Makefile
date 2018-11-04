
proxy.pac: proxy.pac.tail china_ip_list/china_ip_list.txt paper-domains.txt reserved.txt iplist2js.py
	python3 iplist2js.py |cat - proxy.pac.tail |sed -r 's/\bnull\b/0/g' >proxy.pac

test.js: proxy.pac test.tail
	cat proxy.pac test.tail >test.js

clean:
	rm -rf proxy.pac

all: proxy.pac
