import os
import re
from json import loads as loadjson

import jellyfish
from requests import get
from tqdm import tqdm


async def query(item, mc_framework, mc_version, session, commonname):
    link = f'https://api.modrinth.com/v2/search?query={item}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
    
    async with session.get(link) as resp:
        cont = await resp.json()
        
        # Check if received query is blank
        if not cont["hits"]:
            return False, None, item, commonname

        levcomp = 999
        current = ""

        # Check if any query is not the query
        for slug in cont["hits"]:
            tf, lev = await checkbadmod(item, slug["slug"], mc_framework)
            if not tf:
                return slug["slug"], None, item, commonname

            if levcomp > lev:
                current = slug["slug"]
                levcomp = lev
            
        return False, current, item, commonname

async def checkbadmod(filename, modfilename, modframework):

    checkname = modfilename.find(re.sub('\s+','',filename).lower())
    checkloader = modfilename.find(modframework)
    checklevdist = jellyfish.levenshtein_distance(filename, modfilename)

    if checkname != -1 and checkloader != -1:
        return False, 0
    elif checklevdist > len(modfilename) / 2:
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

    name = tup["name"]
    item = tup["slug"]
    
    if type == "update":
        modfilename = tup["filename"]

    # Get Available Versions
    req = get(f"https://api.modrinth.com/v2/project/{item}/version")

    try:
        for mod_version in loadjson(req.content):
            if mc_version in mod_version["game_versions"] and mc_framework in mod_version["loaders"]:
                mod_download = mod_version
                break

        if not mod_download:
            print(f"Can't find appropriate version for {item}!")
            return
    except:
        with open("mods-that-broke.txt", 'w') as file:
            file.write(name)
            print(f"Error for {name}! Printed name of mod in textfile: mods-that-broke.txt")
            return
    
    filename = mod_download["files"][0]["filename"]

    # Check if filename matches
    if type == "update":
        if filename == modfilename:
            print(f'{item} is up-to-date! Yay!')
            return

    # Actually download it
    print(f'Downloading: {item}')
    resp = get(mod_download["files"][0]["url"], stream=True)
    total = int(resp.headers.get('content-length', 0))
    # Can also replace 'file' with a io.BytesIO object
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

    # Write to Disk
    if type == "update":
        os.remove(modfilename)
        print(f"{item} has been updated! ({filename})")

    elif type == "download":
        print(f"{filename} has been downloaded for {item}!")
