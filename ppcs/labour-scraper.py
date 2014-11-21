#!/usr/bin/env python

from bs4 import BeautifulSoup
import re
import requests
from urlparse import urljoin

from common import get_empty_json_directory, write_ppc_json

base_url = 'http://www2.labour.org.uk'
all_page = '/candidates'

r = requests.get(urljoin(base_url, all_page))
main_soup = BeautifulSoup(r.text)

json_directory = get_empty_json_directory('labour')

table = main_soup.find('table')

matchers = {
    'email': re.compile(r'(?ms)Email:.*?<a.*?href="mailto:(.*?)"'),
    'twitter_username': re.compile(r'(?ms)Twitter:.*?<a.*?href=".*?twitter.com/(.*?)"'),
    'phone': re.compile(r'(?ms)Tel:.*?([\d\s\(\)]+)'),
    'facebook_url': re.compile(r'(?ms)Facebook:.*?<a.*?href="(.*?)"'),
}

def get_person(full_name, constituency, relative_url):
    full_url = urljoin(base_url, relative_url)
    full_url = re.sub(r'\?.*', '', full_url)
    print "got URL:", full_url
    data = {
        'path': relative_url,
        'full_url': full_url,
    }
    r = requests.get(full_url)
    if r.status_code != 200:
        print "Warning: bad HTTP status returned for", full_url
        return data
    page_text = r.text
    person_soup = BeautifulSoup(page_text)
    title = person_soup.find('h2')
    if not title:
        print "Warning: couldn't find a title in", full_url
        _, full_name = [x.strip() for x in title.text.split(',')]
        # Remove any NO-BREAK-SPACE from the name:
        data['name'] = re.sub(r'\xA0', ' ', full_name)
    # Unfortunately, these pages are malformed enough that when parsed
    # by BeautifulSoup, the <p/>s that contain some of the contact
    # details disappear. So (sigh) just extract them with regular expressions.
    page_text = page_text.replace("\r", '').replace("\n", '')
    for key, regex in matchers.items():
        m = regex.search(page_text)
        if m:
            data[key] = m.group(1).strip()
    return data

for row in table.find_all('tr'):
    cells = row.find_all('td')
    constituency, region, candidate = [
        c.text.strip() for c in cells
    ]
    if not candidate:
        continue
    if constituency == 'Constituency':
        # Then this is a header line, just skip it
        continue
    candidate_link = cells[2].find('a')
    data = {
        'name': candidate,
        'region': region,
        'constituency': constituency,
    }
    if candidate_link:
        data.update(get_person(
            candidate_link,
            constituency,
            candidate_link['href']
        ))
    write_ppc_json(data, constituency, json_directory)
