import os
from os.path import dirname, join

def get_empty_json_directory(name):
    result = join(dirname(__file__), 'json', name)
    if not os.path.exists(result):
        os.makedirs(result)
    for filename in os.listdir(result):
        if not filename.endswith('.json'):
            os.remove(join(result, filename))
    return result
