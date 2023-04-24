import os

import download
import update

print("What would you like to do? (download, update)")
inp = input()

while inp != "exit":
    if inp == "download":
        download.main()
        break

    if inp == "update":
        update.main()
        break

    print("What would you like to do? (download, update)")

print("Thanks for using this program! Press any key to exit.")
os.system('pause')
print("Bye! -K97i")
os._exit(1)
