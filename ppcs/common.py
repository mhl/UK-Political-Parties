from glob import glob
import hashlib
import json
import os
from os.path import dirname, join, exists
import re
import shutil
from tempfile import NamedTemporaryFile

from PIL import Image
import requests

from faces import face_crop

def get_empty_json_directory(name):
    result = join(dirname(__file__), 'json', name)
    if not os.path.exists(result):
        os.makedirs(result)
    for filename in os.listdir(result):
        full_path = join(result, filename)
        if os.path.isdir(full_path):
            continue
        if not (filename.endswith('.json') or filename.endswith('-cropped.png')):
            os.remove(full_path)
    return result

def get_image_cache_directory():
    result = join(dirname(__file__), 'image-cache')
    if not exists(result):
        os.makedirs(result)
    return result

def write_ppc_data(data, constituency, json_directory):
    basename = re.sub(r'\W+', '-', constituency.lower())
    json_leafname = basename + '.json'
    image_cropped_filename = join(json_directory, basename + '-cropped.png')
    image_original_without_extension = join(json_directory, basename + '-original')
    image_data = data.get('image_data', {})
    if not glob(image_original_without_extension + '*'):
        if 'original_filename' in image_data:
            with Image.open(image_data['original_filename']) as im:
                image_format = im.format.lower()
            shutil.copyfile(
                image_data['original_filename'],
                image_original_without_extension + '.' + image_format,
            ),
    if not exists(image_cropped_filename):
        if 'cropped_filename' in image_data:
            shutil.copyfile(
                image_data['cropped_filename'],
                image_cropped_filename,
            )
        elif 'original_filename' in image_data:
            shutil.copyfile(
                image_data['original_filename'],
                image_cropped_filename,
            )
    reduced_data = data.copy()
    reduced_data.pop('image_data', None)
    with open(join(json_directory, json_leafname), 'w') as f:
        json.dump(reduced_data, f, indent=4, sort_keys=True)

def get_image_cached(url, cache_directory):
    md5sum = hashlib.md5(url).hexdigest()
    filename = join(cache_directory, md5sum)
    if not os.path.exists(filename):
        print "getting image URL", url
        r = requests.get(url, stream=True)
        ntf = NamedTemporaryFile(
            delete=False,
            prefix=join(cache_directory, 'tmp'),
        )
        with open(ntf.name, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        os.rename(ntf.name, filename)
    return filename, md5sum

def get_image(url, cache_directory, already_cropped=False):
    original_filename, original_md5sum = get_image_cached(
        url,
        cache_directory,
    )
    result = {
        'original_url': url,
        'original_filename': original_filename,
    }
    if already_cropped:
        result['cropped_filename'] = original_filename
    else:
        cache_directory_cropped = join(cache_directory, 'cropped')
        if not exists(cache_directory_cropped):
            os.makedirs(cache_directory_cropped)
        im = Image.open(original_filename)
        cropped = face_crop(im, 200, face=True)
        ntf = NamedTemporaryFile(
            delete=False,
            prefix=join(cache_directory_cropped, 'tmp'),
            suffix='.png'
        )
        cropped.save(ntf.name, 'PNG')
        with open(ntf.name, 'rb') as f:
            cropped_md5sum = hashlib.md5(f.read()).hexdigest()
        cropped_filename = join(
            cache_directory_cropped,
            cropped_md5sum + '.png',
        )
        os.rename(ntf.name, cropped_filename)
        result['cropped_filename'] = cropped_filename
    return result
