import multiprocessing
import requests
import json
import os

def compile_list():
    """ Queries Modrinth for the mod's slugs """
    x=0
    array = []

    print(mc_framework, mc_version)

    with open('modlist.txt', 'r') as file:
        searchlist = file.readlines()

    for item in searchlist:

        link = f'https://api.modrinth.com/v2/search?query={item}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
        req = requests.get(link)
        cont = json.loads(req.content)

        array.append(cont["hits"][0]["slug"])
        print(f"{x+1}: {item} => {array[x]}")
        x+=1

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
                link = f'https://api.modrinth.com/v2/search?query={input()}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
                req = requests.get(link)
                cont = json.loads(req.content)
                array[int(inp)-1] = cont["hits"][0]["slug"]
                print(f'=> {cont["hits"][0]["slug"]}')
                continue
            except:
                print("Error!")
                continue
        except:
            continue
    return array

def download(item, mc_framework, mc_version):
    """ Grabs the latest download """

    # Get Available Versions
    req = requests.get(f"https://api.modrinth.com/v2/project/{item}/version")

    for mod_version in json.loads(req.content):
        if mc_version in mod_version["game_versions"] and mc_framework in mod_version["loaders"]:
            mod_download = mod_version
            break

    if not mod_download:
        print(f"Can't find appropriate version for {item}!")
        return

    # Actually download it
    mod_file = requests.get(mod_download["files"][0]["url"]).content
    filename = mod_download["files"][0]["filename"]

    # Write to Disk
    open(f"{filename}", 'wb').write(mod_file)
    print(f"{filename} has been downloaded for {item}!")

if __name__ == "__main__":
    print("What version? (1.19.2, 1.16.5, etc) ")
    mc_version = input()

    print("Modloader? (fabric, forge, quilt) ")
    mc_framework = input()

    if not os.path.isfile("modlist.txt"):
        open("modlist.txt", "wb").write()
        print("Please enter the names of the mods you would like to download.")
        print("Re-run the program when you have done so. Press Enter key to exit.")
        input()
        os._exit(1)

    list = compile_list()

    if not os.path.exists('./downloaded-mods'):
        os.mkdir('./downloaded-mods')

    os.chdir('./downloaded-mods')

    print("Please wait!")

    threads = []

    for item in list:
        thread = multiprocessing.Process(target=download, args=(item, mc_framework, mc_version,))
        threads.append(threads)
        thread.start()