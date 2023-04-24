import os
import re
from json import loads as loadjson

import jellyfish
from requests import get


def query(item, mc_framework, mc_version):
    link = f'https://api.modrinth.com/v2/search?query={item}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
    req = get(link)
    cont = loadjson(req.content)

    # Check if recieved query is blank
    if not cont["hits"]:
        return False, None

    # Check if any query is not the query
    for slug in cont["hits"]:
        
        levcomp = 0.0
        current = ""
        tf, lev = checkbadmod(item, slug["slug"], mc_framework)
        
        if not tf:
            return slug["slug"], None
        
        if levcomp > lev:
            current = tf
            levcomp = lev
    
    return False, current

def checkbadmod(filename, modfilename, modframework):
    if filename.find(re.sub('\s+','',modfilename).lower()) != -1 and filename.find(modframework) != -1:
        return False, 0
    elif jellyfish.levenshtein_distance(filename, modfilename) > len(modfilename) / 2:
        return True, jellyfish.levenshtein_distance(filename, modfilename)
    else:
        return False, 0

def cleanversion(modf):
    a = ""
    for string in modf:
        a += re.sub(re.compile(r'[~<=>]+'), '', string)
    return a

def download(tup, mc_version, mc_framework, type):
    """ Grabs the latest download """
    
    modfilename = ""
    if type == "update":
        item = tup["slug"]
        modfilename = tup["filename"]

    elif type == "download":
        item = tup

    # Get Available Versions
    req = get(f"https://api.modrinth.com/v2/project/{item}/version")

    for mod_version in loadjson(req.content):
        if mc_version in mod_version["game_versions"] and mc_framework in mod_version["loaders"]:
            mod_download = mod_version
            break

    if not mod_download:
        print(f"Can't find appropriate version for {item}!")
        return
    
    filename = mod_download["files"][0]["filename"]

    # Check if filename matches
    if type == "update":
        if filename == modfilename:
            print(f'{item} is up-to-date! Yay!')
            return

    # Actually download it
    print(f'Downloading: {item}')
    mod_file = get(mod_download["files"][0]["url"]).content

    # Write to Disk
    if type == "update":
        open(f"{filename}", 'wb').write(mod_file)
        os.remove(modfilename)
        print(f"{item} has been updated! ({filename})")

    elif type == "download":
        open(f"{filename}", 'wb').write(mod_file)
        print(f"{filename} has been downloaded for {item}!")
