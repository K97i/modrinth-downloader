import asyncio
import os
import threading
from tkinter import filedialog as fd

import aiohttp

import common


async def get_list(mc_framework, mc_version):
    """ Queries Modrinth for the mod's slugs """
    x = 0
    y = 0
    array = []
    not_found = []

    with open('modlist.txt', 'r') as file:
        searchlist = file.readlines()

    searchlist = [item.strip() for item in searchlist]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for item in searchlist:
            task = asyncio.ensure_future(common.query(item, mc_framework, mc_version, session, item))
            tasks.append(task)
        result = await asyncio.gather(*tasks)

    for item in result:
        if not item[0] and item[1] == None:
            dict = {
                    "name": item[3],
                    "id": item[2],
                    "reason": "No Mod Found"
                }
            not_found.append(dict)
        elif not item[0] and item[1]:
            dict = {
                    "name": item[3],
                    "id": item[2],
                    "query": item[1],
                    "reason": "Bad Mod",
                }
            not_found.append(dict)
        else:
            dict = {
                "name": item[3],
                "slug": item[0],
            }
            x += 1
            print(f'{x}: {item[3]} => {item[0]}')
            array.append(dict)
    
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
                        }
                        print(f'=> {result[0][0]}')

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
                except Exception:
                    print(f'Error! {Exception}')
                    continue 

    else:
        print("Empty mod list!")
        os.system('pause')
        os._exit(-1)

    return array

def main():

    if not os.path.isfile("modlist.txt"):
        open("modlist.txt", "w").write('Insert mods here!')
        print("Please enter the names of the mods you would like to download.")
        print("Re-run the program when you have done so. Press any key to exit.")
        os.startfile('modlist.txt')
        os.system('pause')
        os._exit(1)

    if os.stat("modlist.txt").st_size == 0:
        print("Please fill the text file! (Remember to save!)")
        os.system('pause')
        os._exit(1)

    print("What version? (1.19.2, 1.16.5, etc) ")
    mc_version = input()

    print("Modloader? (fabric, forge, quilt) ")
    mc_framework = input()

    list = asyncio.run(get_list(mc_framework, mc_version))

    print("Select mod folder please!")
    os.chdir(fd.askdirectory(initialdir=os.getcwd()))

    print("Please wait!")

    threads = []
    for item in list:
        x = threading.Thread(target=common.download, args=(item, mc_version, mc_framework, "download"))
        x.start()
        threads.append(x)

    for item in threads:
        item.join()

if __name__ == "__main__":
    main()