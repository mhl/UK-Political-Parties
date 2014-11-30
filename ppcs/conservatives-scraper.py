#!/usr/bin/env python

from bs4 import BeautifulSoup
import re
import requests
from urlparse import urljoin

from common import get_empty_json_directory, write_ppc_json

base_url = 'https://www.conservatives.com/'
all_page = '/OurTeam/Prospective_Parliamentary_Candidates.aspx'

def get_contact_detail(label, detail):
    m_label = re.search(r'^(\w+):', label.text)
    if not m:
        raise Exception, "Failed to match the label" + label.text
    label_abbrev = m_label.group(1)
    return {
        {'t': 'phone',
         'e': 'email',
         'w': 'homepage'}[label_abbrev]:
        detail.text.strip()
    }

def get_person(person_path, person_slug, constituency):
    r = requests.get(urljoin(base_url, person_path))
    person_soup = BeautifulSoup(r.text)
    contact_div = person_soup.find('div', {'class': 'contact-container'})
    full_name = person_soup.find('h1').text.strip()
    data = {
        'slug': person_slug,
        'path': person_path,
        'full_url': urljoin(base_url, person_path),
        'name': full_name,
        'constituency': constituency,
    }
    address_div = contact_div.find(True, {'class': 'contact-detail-address'})
    if address_div:
        data['address'] = list(address_div.children)[2]
    inner_contact_div = contact_div.find('div', {'class':'contact-container-inner'})
    for div in inner_contact_div.find_all('div', recursive=False):
        if div.has_attr('class'):
            div_class = div['class']
        else:
            div_class = None
        # print "div_class is:", div_class
        if div_class == ['contact-social-media']:
            link = div.find('a')
            if link:
                tw_m = re.search(r'twitter.com/(\w+)$', link['href'])
                fb_m = re.search(r'(http.*facebook.com.*)$', link['href'])
                if tw_m:
                    data['twitter_username'] = tw_m.group(1)
                if fb_m:
                    data['facebook_url'] = fb_m.group(1)
        elif div.find('pre', {'class': 'contact-detail-address'}):
            # We've already dealt with the address div, so skip it
            pass
        elif div_class is None:
            label = div.find('span', {'class': 'contact-label'})
            detail = div.find('span', {'class': 'contact-detail'})
            if label and detail:
                data.update(get_contact_detail(label, detail))
        else:
            raise Exception, "Unknown div {0}".format(div)
    return data

r = requests.get(urljoin(base_url, all_page))
main_soup = BeautifulSoup(r.text)

json_directory = get_empty_json_directory('conservatives')

table = main_soup.find('table')

for row in table.find_all('tr'):
    person_link = row.find('a')
    if not person_link:
        continue
    person_url = person_link['href']
    print "person_url:", person_url
    m = re.search(r'/([^/]+)\.aspx$', person_url)
    if not m:
        raise Exception, "Couldn't parse {0}".format(person_url)
    person_slug = m.group(1)
    cells = row.find_all('td')
    constituency = cells[1].text.strip()
    if not constituency:
        continue
    data = get_person(
        person_url,
        person_slug,
        constituency,
    )
    write_ppc_json(data, constituency, json_directory)
