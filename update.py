import asyncio
import os
import threading
import zipfile
from json import loads as loadjson
from tkinter import filedialog as fd

import aiohttp
from tomllib import loads as loadtoml

import common


def get_files():
    modnames = []
    modfilenames = []
    modversionsbase = []
    modversionsminor = []
    modframeworks = []
    badmods = []
    modids = []
    modversionbase = ""
    modversionminor = ""
    modframework = ""

    print("Select mod folder please!")
    path = fd.askdirectory(initialdir=os.getcwd())

    if not path:
        print("No folder selected!")
        os.system('pause')
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
                modframeworks.append("fabric")
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
                modframeworks.append("forge")
                modfilenames.append(x)
                modnames.append(tomlfile["mods"][0]["modId"])
                modids.append(tomlfile["mods"][0]["modId"])
                try:
                    modv = list(filter(lambda test_list: test_list['modId'] == 'minecraft', tomlfile["dependencies"][tomlfile["mods"][0]["modId"]]))
                    modversionsbase.append(modv[0]["versionRange"].strip('[)').split(',')[0].rsplit('.',1)[0])
                    modversionsminor.append(modv[0]["versionRange"].strip('[)').split(',')[0].rsplit('.', 1)[1])
                except:
                    continue
        except:
            badmods.append(x)
    
    for i in modframeworks:
        curr_frequency = modframeworks.count(i)
        counter = 0
        if (curr_frequency> counter):
            counter = curr_frequency
            modframework = i

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

    print("Guessed Minecraft Version:", modversion)
    print("Guessed Minecraft Mod Loader:", modframework)
    print(len(modnames), "Mods found.")

    return modnames, modids, modfilenames, modversion, modframework, badmods

async def get_list():
    """ Queries Modrinth for the mod's slugs """
    x = 0
    y = 0
    array = []
    not_found = []
    badmods = []
    result = []

    searchlist, modids, modfilenames, mc_version, mc_framework, badmods = get_files()

    async with aiohttp.ClientSession() as session:
        tasks = []
        for item in modids:
            task = asyncio.ensure_future(common.query(item, mc_framework, mc_version, session, searchlist[modids.index(item)]))
            tasks.append(task)
        result = await asyncio.gather(*tasks)

    for item in result:
        if not item[0] and item[1] == None:
            dict = {
                    "name": searchlist[modids.index(item[2])],
                    "id": item[2],
                    "reason": "No Mod Found"
                }
            print()
            not_found.append(dict)
            continue
        elif not item[0] and item[1]:
            dict = {
                    "name": searchlist[modids.index(item[2])],
                    "id": item[2],
                    "query": item[1],
                    "reason": "Bad Mod",
                }
            not_found.append(dict)
            continue
        dict = {
            "name": item[3],
            "slug": item[0],
            "filename": modfilenames[len(array)+len(not_found)]
        }
        x += 1
        print(f'{x}: {item[3]} => {item[0]}')
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

            if inp.isdigit():
                print("What would you like to do? (remove, change)")
                ch = input()
                
                try:
                    if ch == "remove":
                        array.pop(int(inp)-1)
                        searchlist.pop(int(inp)-1)
                        print("Item Removed.")

                    if ch == "change":
                        print(f'What would you like to change {array[int(inp)-1]["slug"]} to? ')
                        search = input()
                        async with aiohttp.ClientSession() as session:
                            tasks = []
                            task = asyncio.ensure_future(common.query(search, mc_framework, mc_version, session, search))
                            tasks.append(task)
                            result = await asyncio.gather(*tasks)
                        if not result[0][0]:
                            print("Error!")
                            if result[0][1]:
                                print(f'Closest mod found is {result[1]}')
                            else:
                                print("No mod found.")
                            continue

                        searchlist[int(inp)-1] = search
                        array[int(inp)-1] = {
                            "name": result[0][3],
                            "slug": result[0][0],
                            "filename": array[int(inp)-1]["filename"]
                        }
                        print(f'=> {result[0][0]}')

                    x = 0
                    for item in array:
                        print(f'{x+1}: {item["name"]} => {item["slug"]}')
                        x += 1

                    if not_found:
                        print("\n")
                        for item in not_found:
                            match item['reason']:
                                case "Bad Mod":
                                    print("\033[91m"+ f"{item['name']} => Not found on Modrinth! (Wrong Mod Found, Found: {item['query']})" + "\033[0m")
                                case "No Mod Found":
                                    print("\033[91m"+ f"{item['name']} => Not found on Modrinth! (No mod found.)" + "\033[0m")
                        
                    continue
                except Exception as e:
                    print(f'Error! {e}')
                    continue
    else:
        print("Empty mod list!")
        os.system('pause')
        os._exit(-1)
    return array, mc_version, mc_framework

def main():

    list, mc_version, mc_framework = asyncio.run(get_list())

    print("Please wait!")

    threads = []
    for item in list:
        x = threading.Thread(target=common.download, args=(item, mc_version, mc_framework, "update"))
        x.start()
        threads.append(x)

    for item in threads:
        item.join()

    if os.path.exists("mods-that-broke.txt"):
        os.startfile('mods-that-broke.txt')

if __name__ == "__main__":
    main()