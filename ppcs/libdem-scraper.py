#!/usr/bin/env python

import sys
from bs4 import BeautifulSoup
import re
import requests
from urlparse import urljoin

from common import get_empty_json_directory, get_image_cache_directory, write_ppc_data, get_image

base_url = 'http://www.libdems.org.uk/'
all_page = 'general_election_candidates'

json_directory = get_empty_json_directory('libdem')
image_cache_directory = get_image_cache_directory()

r = requests.get(urljoin(base_url, all_page))
main_soup = BeautifulSoup(r.text)

def clean_contact_detail(key, value):
    if key == 'twitter_username':
        text = value.text.strip()
        text = re.sub(r'^.*twitter.com/', '', text)
        return re.sub(r'^@', '', text)
    elif key == 'address':
        newlines_for_tags = re.sub(
            r'\s*<\s*/?\s*\w+\s*/?\s*>\s*',
            "\n",
            unicode(value)
        )
        return newlines_for_tags.strip()
    else:
        return value.text.strip()

re_location = re.compile(r'window\.location\s*=\s*"(.*?)"')

def get_person(relative_url):
    full_url = urljoin(base_url, relative_url)
    print "full_url:", full_url
    result = {
        'full_url': full_url
    }
    r = requests.get(full_url)
    person_soup = BeautifulSoup(r.text)
    redirect_script_tag = person_soup.find('script', text=re_location)
    if redirect_script_tag:
        new_path = re_location.search(redirect_script_tag.text).group(1)
        print "Redirecting to:", new_path
        return get_person(new_path)
    contact_heading = person_soup.find(
        re.compile(r'^h\d+'),
        text=re.compile(r'^\s*Contact\s*$'),
    )
    if not contact_heading:
        print "Warning: no contact details found on", full_url
        return result
    table = contact_heading.find_next('table')
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        key_cell_text = cells[0].text.strip()
        if key_cell_text:
            key = {
                'Email': 'email',
                'Website': 'homepage',
                'Twitter': 'twitter_username',
                'Telephone': 'phone',
                'Phone': 'phone',
                'Facebook': 'facebook_url',
                'Address': 'address',
                'Blog': 'blog_url',
                'Campaign': 'campaign_url',
                'Party': 'party_url',
                'Websites': 'homepage',
                'Full bio': 'biography_url',
            }[key_cell_text.rstrip(':')]
            result[key] = clean_contact_detail(key, cells[1])
    image = person_soup.find('img', {'class': 'key'})
    if image is not None and image['src']:
        result['image_url'] = image['src']
        result['image_data'] = get_image(
            image['src'],
            image_cache_directory,
        )
    return result

if len(sys.argv) > 1:
  # Grab a specific person, for debugging
  print get_person(sys.argv[1])

else:
  # Grab all the candidates, the normal mode

  for region_span in main_soup.find_all('span', {'class': 'big-tiles-wrapper'}):
      region = region_span.find('h2').text
      print "region:", region
      region_list = region_span.find('ul')
      for li in region_list.find_all('li', recursive=False):
          print "======"
          link = li.find('a')
          relative_url = link['href']
          print "url:", relative_url
          h3 = li.find('h3')
          full_name = h3.find('a').text.strip()
          current_mp = False
          if full_name.endswith(' MP'):
              current_mp = True
              full_name = re.sub(' MP$', '', full_name)
          print "full_name:", full_name
          constituency = h3.findNext('p').text.strip()
          print "constituency:", constituency
          data = {
              'region': region,
              'name': full_name,
              'constituency': constituency,
          }
          if current_mp:
              data['current_mp'] = True
          data.update(get_person(relative_url))
          write_ppc_data(data, constituency, json_directory)
