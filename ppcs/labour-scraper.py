#!/usr/bin/env python

from bs4 import BeautifulSoup
import re
import requests
import time

from common import get_empty_json_directory, get_image_cache_directory, write_ppc_data, get_image

base_url = 'http://www.labour.org.uk/people/filter/c/candidate'

json_directory = get_empty_json_directory('labour')
image_cache_directory = get_image_cache_directory()

r = requests.get(base_url)
soup = BeautifulSoup(r.text)

main_content_div = soup.find('div', id='main-content')

key_mapping = {
    'twitter': 'twitter_username',
    'telephone': 'phone',
    'facebook': 'facebook_url',
    'web': 'homepage',
    'address': 'address',
    'email': 'email',
}

def get_person(full_name, constituency, person_url):
    result = {}
    print "Processing", person_url
    address_div = None
    tries = 0
    # These pages sometimes get 503 Connection timed out from Varnish,
    # so retry in that case:
    while address_div is None and tries < 5:
        r = requests.get(person_url)
        tries += 1
        person_soup = BeautifulSoup(r.text)
        address_div = person_soup.find('address', {'class': 'person-address'})
        if address_div is None:
            print "  Retrying after 5 seconds"
            time.sleep(5)
    # If the address_div still isn't found, print out the page for debugging:
    if address_div is None:
        print person_soup.prettify()
        raise Exception, "Couldn't find the <address class=\"person-address\"> element"
    for address_link in address_div.find_all('a', {'class': 'person-address-link'}):
        classes = [c for c in address_link['class'] if c != 'person-address-link']
        if len(classes) != 1:
            raise Exception, "Found unexpected number of classes remaining:", classes
        info_key = key_mapping[classes[0]]
        info_value = address_link.text.strip()
        info_url = address_link['href']
        if info_key == 'twitter_username':
            m = re.search(r'twitter.com/(\S+)', info_url)
            result[info_key] = m.group(1)
        elif info_key == 'phone':
            result[info_key] = info_value
        elif info_key == 'facebook_url':
            result[info_key] = info_url
        elif info_key == 'email':
            m = re.search(r'mailto:(.*)', info_url)
            result[info_key] = m.group(1)
        elif info_key == 'homepage':
            result[info_key] = info_url
        elif info_key == 'address':
            result[info_key] = info_value
    return result

for figure in main_content_div.find_all('figure'):
    image = figure.find('img')
    full_url = figure.parent['href']
    name = figure.find('div', {'class': 'person-name'}).text.strip()
    title_text = figure.find('div', {'class': 'person-title'}).text.strip()
    constituency = re.sub(r'Candidate\s+for\s+(.*?)\s*$', '\\1', title_text)
    result = {
        'name': name,
        'constituency': constituency,
        'full_url': full_url,
        'image_headshot_url': image['src'],
        'image_data': get_image(image['src'], image_cache_directory),
    }
    # Now get the person page:
    result.update(get_person(
        name,
        constituency,
        full_url,
    ))
    write_ppc_data(result, constituency, json_directory)
