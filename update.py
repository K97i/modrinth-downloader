import os
import zipfile
from json import loads as loadjson
from multiprocessing.pool import ThreadPool
from tkinter import filedialog as fd

from tomllib import loads as loadtoml

import common

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
        os._exit(-1)
    
    print(path, " <= path")
    os.chdir(path)

    if not os.listdir():
        print("Empty directory!")
        os.system('pause')
        os._exit(-1)

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
                    modversionsbase.append(common.cleanversion(jsonfile["depends"]["minecraft"].rsplit('.', 1)[0]))
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

def get_list():
    """ Queries Modrinth for the mod's slugs """
    x = 0
    y = 0
    array = []
    not_found = []

    searchlist, modids, modfilenames, mc_version, mc_framework, badmods = get_files()
    pool = ThreadPool(processes=len(searchlist))

    for item in modids:
        thread, badmod = pool.apply(common.query, (item, mc_framework, mc_version))

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
                    thread = pool.apply(common.query, (input(), mc_framework, mc_version))
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
        os._exit(-1)
    return array, mc_version, mc_framework

def main():

    pool = ThreadPool(processes=64)
    list, mc_version, mc_framework = get_list()

    print("Select mod folder please!")
    path = fd.askdirectory(initialdir=os.getcwd())

    if not path:
        print("No folder selected!")
        os.system('pause')
        os._exit(-1)

    os.chdir(path)
    os.mkdir('./updated-mods')
    os.chdir("./updated-mods")

    print("Please wait!")

    for item in list:
        pool.apply(common.download, (item, mc_version, mc_framework, "update"))

if __name__ == "__main__":
    main()