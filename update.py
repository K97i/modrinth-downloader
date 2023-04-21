from multiprocessing.pool import ThreadPool
from tkinter import filedialog as fd
from requests import get
from json import loads
import tkinter as tk
import jellyfish
import zipfile
import os
import re

root = tk.Tk()
root.withdraw()

def query(item, mc_framework, mc_version):
    link = f'https://api.modrinth.com/v2/search?query={item}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
    req = get(link)
    cont = loads(req.content)

    try:
        return cont["hits"][0]["slug"]
    except:
        return False

def get_files():
    modnames = []
    modfilenames = []
    modversionsbase = []
    modversionsminor = []
    modversionbase = ""
    modversionminor = ""

    path = fd.askdirectory()
    if not path:
        exit()
    
    print(path, " <= path")
    os.chdir(path)

    for x in os.listdir():
        filename, file_ext = os.path.splitext(x)
        
        if file_ext != ".jar":
            continue

        try:
            jarfile = zipfile.ZipFile(x, "r")
            jsonfile = loads(jarfile.read("fabric.mod.json"))
            modfilenames.append(x)
            modnames.append(jsonfile["name"])
            modversionsbase.append(cleanversion(jsonfile["depends"]["minecraft"].rsplit('.', 1)[0]))
            modversionsminor.append(jsonfile["depends"]["minecraft"].split('.')[2])
        except:
            continue
    
    for i in modversionsbase:
        curr_frequency = modversionsbase.count(i)
        counter = 0
        if (curr_frequency> counter):
            counter = curr_frequency
            modversionbase = i

    for i in modversionsminor:
        curr_frequency = modversionsminor.count(i)
        counter = 0
        
        try:
            int(i)
        except:
            continue

        if (curr_frequency> counter):
            counter = curr_frequency
            modversionminor = i

    modversion = modversionbase + "." + modversionminor
    print("Guessed Minecraft Version: ", modversion)

    return modnames, modfilenames, modversion

def cleanversion(modf):
    a = ""
    for string in modf:
        a += re.sub(re.compile(r'[~<=>]+'), '', string)
    return a

def get_list():
    """ Queries Modrinth for the mod's slugs """
    x=0
    array = []
    not_found = []

    searchlist, modfilenames, mc_version = get_files()
    pool = ThreadPool(processes=len(searchlist))

    print("Mod Loader? (fabric, forge)")
    mc_framework = input()

    for item in searchlist:
        thread = pool.apply(query, (item, mc_framework, mc_version))

        if not thread:
            not_found.append(item)
            continue

        # Check if mod is actually the same mod
        if checkbadmod(item, thread):
            not_found.append(item)
            continue
        
        dict = {
            "slug": thread,
            "filename": modfilenames[len(array)+len(not_found)]
        }

        x+=1
        print(f'{x}: {item} => {thread}')
        array.append(dict)
    
    if not_found:
        print("\n")
        for item in not_found:
            print("\033[91m"+ f"{item} => Not found on Modrinth!" + "\033[0m")

    inp = ""

    while inp != "done":

        print("Would you like to change any of the items?")
        print("Enter the number you would like to change")
        print("OR enter 'done' if you are okay with the list")
        print("OR enter 'cancel' to cancel the download.")
        inp = input()

        if inp == "cancel":
            print("Download cancelled!")
            os._exit(1)

        try:
            int(inp)
            try:
                print(f'What would you like to change {array[int(inp)-1]} to? ')
                thread = pool.apply(query, (input(), mc_framework, mc_version))
                array[int(inp)-1] = thread
                print(f'=> {thread}')
                continue
            except Exception:
                print(f'Error! {Exception}')
                continue
        except:
            continue
    return array, mc_version, mc_framework

def checkbadmod(filename, modfilename):
    count = jellyfish.levenshtein_distance(filename, modfilename)
    if count > len(modfilename) / 2:
        return True
    else:
        return False

def download(tup, mc_version, mc_framework):
    """ Grabs the latest download """

    item = tup["slug"]
    modfilename = tup["filename"]

    # Get Available Versions
    req = get(f"https://api.modrinth.com/v2/project/{item}/version")

    for mod_version in loads(req.content):
        if mc_version in mod_version["game_versions"] and mc_framework in mod_version["loaders"]:
            mod_download = mod_version
            break

    if not mod_download:
        print(f"Can't find appropriate version for {item}!")
        return
    
    filename = mod_download["files"][0]["filename"]

    # Check if filename matches
    if filename == modfilename:
        print(f'{item} is up-to-date! Yay!')
        return

    # Actually download it
    print(f'Downloading: {item}')
    mod_file = get(mod_download["files"][0]["url"]).content

    # Write to Disk
    open(f"{filename}", 'wb').write(mod_file)
    os.remove(modfilename)
    print(f"{item} has been updated! ({filename})")

def main():
    pool = ThreadPool(processes=64)
    list, mc_version, mc_framework = get_list()

    print("Select mod folder please!")
    os.chdir(fd.askdirectory(initialdir=os.getcwd()))

    print("Please wait!")

    for item in list:
        pool.apply(download, (item, mc_version, mc_framework, ))

if __name__ == "__main__":
    main()