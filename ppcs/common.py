import json
import os
from os.path import dirname, join
import re

def get_empty_json_directory(name):
    result = join(dirname(__file__), 'json', name)
    if not os.path.exists(result):
        os.makedirs(result)
    for filename in os.listdir(result):
        if not filename.endswith('.json'):
            os.remove(join(result, filename))
    return result

def write_ppc_json(data, constituency, json_directory):
    file_leafname = re.sub(r'\W+', '-', constituency.lower()) + '.json'
    with open(join(json_directory, file_leafname), 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
