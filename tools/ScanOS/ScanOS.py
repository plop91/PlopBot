import os
import platform

'''

'''
class OSLocation:
    osSlash = {
        "windows": "\\",
        "mac": "/",
        "linux": "/"
    }
    def __init__(self, path):
        self.os = OSLocation.getos()
        self.path = path
        self.contents = []
        try:
            self.contents = os.listdir(self.path)
        except Exception as e:
            print("could not list dir:"+str(e))
        self.folders = []
        if self.contents:
            self.pullFolders()

    def pullFolders(self):
        for s in self.contents:
            if os.path.isdir(self.path + self.osSlash[self.os] + s):
                self.folders.append(self.path + self.osSlash[self.os] + s)

    def __del__(self):
        del self.path

    def getPath(self):
        return self.path

    def getContents(self):
        return self.contents

    def getFolders(self):
        if len(self.folders) == 0:
            return
        return self.folders

    @staticmethod
    def getos():
        os = platform.platform()
        if "Windows" in os:
            os = "windows"
        elif "OSX" in os:
            os = "mac"
        elif "Linux" in os:
            os = "linux"
        return os

    @staticmethod
    def getosslash():
        return OSLocation.osSlash[OSLocation.getos()]
'''

'''
def getos():
    os = platform.platform()
    if "Windows" in os:
        os = "windows"
    elif "OSX" in os:
        os = "mac"
    elif "Linux" in os:
        os = "linux"
    return os
'''

'''
def getosslash():
    return OSLocation.osSlash[OSLocation.getos()]
'''

'''
def list(dir=os.getcwd()):
    scanndedDirectory = OSLocation(dir)
    print(scanndedDirectory.getPath())
    print(scanndedDirectory.getContents())
'''

'''
def listLong(dir=os.getcwd()):
    scannedDirectories = [OSLocation(dir)]
    startdir = scannedDirectories[0]
    toScan = startdir.getFolders()
    while toScan:
        temp = OSLocation(toScan.pop(0))
        tfolders = temp.getFolders()
        if tfolders is not None:
            for s in tfolders:
                toScan.append(s)
        scannedDirectories.append(temp)
    for s in scannedDirectories:
        print(s.getPath())
        print(s.getContents())
'''
Long list directories from dir
'''
def search(term,dir=os.getcwd()):
    scannedDirectories = [OSLocation(dir)]
    startdir = scannedDirectories[0]
    found = []
    for i in startdir.getContents():
        if term in i:
            found.append(i)
    toScan = startdir.getFolders()
    while toScan:
        temp = OSLocation(toScan.pop(0))
        for i in temp.getContents():
            if term in i:
                found.append(i)
        tfolders = temp.getFolders()
        if tfolders is not None:
            for s in tfolders:
                toScan.append(s)
        scannedDirectories.append(temp)
        found.sort()
    if len(found) <= 0:
        return None
    return found
'''
Menu for easily using ScanOs class
'''
def menu():
    if "mac" in getos():
        os.chdir("/Users/iansodersjerna")
    elif "windows" in getos():
        res = search("ian","C:\Users")
        print("res="+res[0])
        os.chdir("C:\Users\ian")
    while True:
        relitive = os.getcwd()+getosslash()
        print("Current working directory: " + relitive + """
    Enter 1 for long list
    Enter 2 for list
    Enter 3 to search
    Enter 4 to change directory
    Enter 5 to exit
    >>:"""),
        choice = raw_input("");
        if choice == "1":
            print("enter parameter\n>>:"),
            choice = raw_input("")
            if choice != "0":
                if choice:
                    if choice[0] == getosslash() or (choice[1] == ":" and choice[2] == "\\"):
                        listLong(choice)
                    else:
                        listLong(relitive + choice)
                else:
                    listLong(relitive)
        elif choice == "2":
            print("enter parameter\n>>:"),
            choice = raw_input("")
            if choice != "0":
                if choice:
                    if choice[0] == getosslash() or (choice[1] == ":" and choice[2] == "\\"):
                        list(choice)
                    else:
                        list(relitive + choice)
                else:
                    list(relitive)
        elif choice == "3":
            print("enter serch parameter\nEnter 0 to go back\n>>:"),
            choice = raw_input("")
            if choice != "0":
                print("enter directory to search in\nEnter 0 to go back\n>>:"),
                choice2 = raw_input("")
                if choice2 != "0":
                    if choice2:
                        if choice2[0] == OSLocation.getosslash():
                            print(search(choice, choice2))
                        else:
                            print(search(choice, relitive + choice2))
                    else:
                        print(search(choice,relitive))
        elif choice == "4":
            print("enter parameter\n>>:"),
            choice = raw_input("")
            if choice != "0":
                if choice:
                    if choice[0] == getosslash() or (choice[1] == ":" and choice[2] == "\\"):
                        os.chdir(choice)
                    else:
                        os.chdir(relitive + choice)
                else:
                    os.chdir(relitive)

        elif choice == "5":
            exit(0)
