from multiprocessing.pool import ThreadPool
from requests import get
from json import loads
import os

def query(item, mc_framework, mc_version):
    link = f'https://api.modrinth.com/v2/search?query={item}&facets=[["categories:{mc_framework}"],["versions:{mc_version}"]]'
    req = get(link)
    cont = loads(req.content)

    try:
        return cont["hits"][0]["slug"]
    except:
        return False

def get_list(mc_framework, mc_version):
    """ Queries Modrinth for the mod's slugs """
    x=0
    array = []

    with open('modlist.txt', 'r') as file:
        searchlist = file.readlines()

    pool = ThreadPool(processes=len(searchlist))

    for item in searchlist:
        thread = pool.apply(query, (item, mc_framework, mc_version))
        array.append(thread)
        print(f"{x+1}: {item} => {thread}")
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
                thread = pool.apply(query, (input(), mc_framework, mc_version))
                array[int(inp)-1] = thread
                print(f'=> {thread}')
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

    list = get_list(mc_framework, mc_version)

    if not os.path.exists('./downloaded-mods'):
        os.mkdir('./downloaded-mods')

    os.chdir('./downloaded-mods')

    print("Please wait!")

    for item in list:
        pool.apply(download, (item, mc_version, mc_framework, ))

if __name__ == "__main__":
    main()