from multiprocessing.pool import ThreadPool
from tkinter import filedialog as fd
from requests import get
from json import loads as loadjson
from tomllib import loads as loadtoml
import jellyfish
import zipfile
import os
import re

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
        return False
    elif jellyfish.levenshtein_distance(filename, modfilename) > len(modfilename) / 2:
        return True
    else:
        return False

def get_files():
    modnames = []
    modfilenames = []
    modversionsbase = []
    modversionsminor = []
    badmods = []
    modids = []
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

        print(x)

        try:
            try:
                # Get json file
                jarfile = zipfile.ZipFile(x, "r")
                jsonfile = loadjson(jarfile.read("fabric.mod.json"))
                
                # Set Values
                modframework = "fabric"
                modfilenames.append(x)
                modnames.append(jsonfile["name"])
                modids.append(jsonfile["id"])

                # Some mods don't have this for some reason
                try:
                    modversionsbase.append(cleanversion(jsonfile["depends"]["minecraft"].rsplit('.', 1)[0]))
                    modversionsminor.append(jsonfile["depends"]["minecraft"].rsplit('.', 1)[1])
                except:
                    continue
            except:
                # Get toml file and decode
                jarfile = zipfile.ZipFile(x, "r")
                tomlraw = jarfile.read("META-INF/mods.toml")
                tomlraw = tomlraw.decode()
                tomlfile = loadtoml(tomlraw)

                # Set Values
                modframework = "forge"
                modfilenames.append(x)
                modnames.append(tomlfile["mods"][0]["modId"])
                try:
                    modv = list(filter(lambda test_list: test_list['modId'] == 'minecraft', tomlfile["dependencies"][tomlfile["mods"][0]["modId"]]))
                    modversionsbase.append(modv[0]["versionRange"].strip('[)').split(',')[0].rsplit('.',1)[0])
                    modversionsminor.append(modv[0]["versionRange"].strip('[)').split(',')[0].rsplit('.', 1)[1])
                except:
                    continue
        except:
            badmods.append(x)
    
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
    print(len(modnames), "Mods found.")

    return modnames, modids, modfilenames, modversion, modframework, badmods

def cleanversion(modf):
    a = ""
    for string in modf:
        a += re.sub(re.compile(r'[~<=>]+'), '', string)
    return a

def get_list():
    """ Queries Modrinth for the mod's slugs """
    x = 0
    y = 0
    array = []
    not_found = []

    searchlist, modids, modfilenames, mc_version, mc_framework, badmods = get_files()
    pool = ThreadPool(processes=len(searchlist))

    for item in modids:
        thread, badmod = pool.apply(query, (item, mc_framework, mc_version))

        # Check if query returns empty
        if not thread:
            # If different mod found
            if badmod:
                dict = {
                    "name": searchlist[y],
                    "id": item,
                    "query": thread,
                    "reason": "Bad Mod",
                }
                not_found.append(dict)
                y += 1
                continue
            
            # If no mod was found
            else: 
                dict = {
                    "name": searchlist[y],
                    "id": item,
                    "reason": "No Mod Found"
                }
                not_found.append(dict)
                y += 1
                continue
        
        dict = {
            "slug": thread,
            "filename": modfilenames[len(array)+len(not_found)]
        }

        x += 1
        y += 1
        print(f'{x}: {item} => {thread}')
        array.append(dict)
    
    if not_found:
        print("\n")
        for item in not_found:
            match item['reason']:
                case "Bad Mod":
                    print("\033[91m"+ f"{item['name']} ({item['id']}) => Not found on Modrinth! (Wrong Mod Found, Found: {item['query']})" + "\033[0m")
                case "No Mod Found":
                    print("\033[91m"+ f"{item['name']} ({item['id']}) => Not found on Modrinth! (No mod found.)" + "\033[0m")

    if badmods:
        print("\n")
        for item in badmods:
            print("\033[91m"+ f"{item} has hit this program's limitations. Needs to be updated manually." + "\033[0m")

    if not_found or badmods:
        mods = []
        for item in not_found:
            mods.append(item["name"])
        mods += badmods

        with open('mods-to-manually-update.txt', 'w') as f:
            for line in mods:
                f.write(line)
                f.write('\n')
        
        os.startfile('mods-to-manually-update.txt')
        print("A text file labeled 'mods-to-manually-update.txt' has been created for your convenience. ;)")

    inp = ""

    if array:
        
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
    else:
        print("Empty mod list!")
        os.system('pause')
        exit()
    return array, mc_version, mc_framework

def download(tup, mc_version, mc_framework):
    """ Grabs the latest download """

    item = tup["slug"]
    modfilename = tup["filename"]

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
    path = fd.askdirectory(initialdir=os.getcwd())

    if not path:
        print("No folder selected!")
        os.system('pause')
        exit()

    os.chdir(path)
    os.mkdir('./updated-mods')
    os.chdir("./updated-mods")

    print("Please wait!")

    for item in list:
        pool.apply(download, (item, mc_version, mc_framework, ))

    print("Update Complete! Thanks for using this!")
    print("Bye! -K97i")
    os.system('pause')

if __name__ == "__main__":
    main()