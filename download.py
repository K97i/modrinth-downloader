from multiprocessing.pool import ThreadPool
from tkinter import filedialog as fd
from requests import get
from json import loads
import jellyfish
import re
import os

def query(item, mc_framework, mc_version):
    link = f'https://api.modrinth.com/v2/search?query={item}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
    req = get(link)
    cont = loads(req.content)

    # Check if recieved query is blank
    if not cont["hits"]:
        return False, None

    # Check if any query is not the query
    for slug in cont["hits"]:
        
        levcomp = 0.0
        current = ""
        tf = checkbadmod(item, slug["slug"], mc_framework)
        lev = 0
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

def get_list(mc_framework, mc_version):
    """ Queries Modrinth for the mod's slugs """
    x = 0
    y = 0
    array = []
    not_found = []

    with open('modlist.txt', 'r') as file:
        searchlist = file.readlines()

    searchlist = [item.strip() for item in searchlist]

    pool = ThreadPool(processes=len(searchlist))

    for item in searchlist:
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

        array.append(thread)
        print(f"{x+1}: {item} => {thread}")
        x += 1
        y += 1
    
    inp = ""

    if not_found:
            print("\n")
            for item in not_found:
                searchlist.remove(item['name'])
                match item['reason']:
                    case "Bad Mod":
                        print("\033[91m"+ f"{item['name']} => Not found on Modrinth! (Wrong Mod Found, Found: {item['query']})" + "\033[0m")
                    case "No Mod Found":
                        print("\033[91m"+ f"{item['name']} => Not found on Modrinth! (No mod found.)" + "\033[0m")

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

            print("What would you like to do? (remove, change)")
            ch = input()
            
            try:
                if ch == "remove":
                    array.pop(int(inp)-1)
                    searchlist.pop(int(inp)-1)
                    print("Item Removed.")

                if ch == "change":
                    print(f'What would you like to change {array[int(inp)-1]} to? ')
                    search = input()
                    thread = pool.apply(query, (search, mc_framework, mc_version))
                    if not thread[0]:
                        print("Error!")
                        if thread[1]:
                            print(f'Closest mod found is {thread[1]}')
                        else:
                            print("No mod found.")
                        continue

                    searchlist[int(inp)-1] = search
                    array[int(inp)-1] = thread[0]
                    print(f'=> {thread[0]}')

                x = 0
                for item in array:
                    print(f'{x+1}: {searchlist[x]} => {array[x]}')
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
            except:
                print("Error!")
                continue
        except:
            continue    

    return array

def download(item, mc_framework, mc_version):
    """ Grabs the latest download """

    mod_download = ""

    # Get Available Versions
    req = get(f"https://api.modrinth.com/v2/project/{item}/version")

    for mod_version in loads(req.content):
        if mc_version in mod_version["game_versions"] and mc_framework in mod_version["loaders"]:
            mod_download = mod_version
            break

    if not mod_download:
        print(f"Can't find appropriate version for {item}!")
        return

    # Actually download it
    mod_file = get(mod_download["files"][0]["url"]).content
    filename = mod_download["files"][0]["filename"]

    # Write to Disk
    open(f"{filename}", 'wb').write(mod_file)
    print(f"{filename} has been downloaded for {item}!")

def main():
    pool = ThreadPool(processes=64)

    if not os.path.isfile("modlist.txt"):
        open("modlist.txt", "wb").write(b'Insert mods here!')
        print("Please enter the names of the mods you would like to download.")
        print("Re-run the program when you have done so. Press any key to exit.")
        os.system('pause')
        os._exit(1)

    print("What version? (1.19.2, 1.16.5, etc) ")
    mc_version = input()

    print("Modloader? (fabric, forge, quilt) ")
    mc_framework = input()

    list = get_list(mc_framework, mc_version)

    print("Select mod folder please!")
    os.chdir(fd.askdirectory(initialdir=os.getcwd()))

    print("Please wait!")

    for item in list:
        pool.apply(download, (item, mc_framework, mc_version, ))

if __name__ == "__main__":
    main()