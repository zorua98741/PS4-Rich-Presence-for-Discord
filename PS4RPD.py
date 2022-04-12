from ftplib import FTP
from pypresence import Presence
from pypresence import InvalidPipe
from pypresence import InvalidID
import time
import re
from bs4 import BeautifulSoup
import requests
import gc
import os


class PrepWork(object):                                 # does preparation needed for program to function
    def __init__(self):
        self.ip = None
        self.ftp = FTP()                                # create instance of FTP class
        self.client_id = "858345055966461973"           # default client id is my own
        self.sleep_time = 120                           # default sleep time is 2 minutes while in beta
        self.resetTimeOnGameChange = "True"             # default to reset timer whenever a new game is detected
        self.individualPs1Ps2Covers = "False"           # default to use the same image for all PS1 and PS2 games
        self.customPs4Covers = "False"                  # default to use orbispatches images for PS4 games
        self.customHomebrewCovers = "False"             # default to using "none" as image for all games detected as homebrew apps
        self.RPC = None
        self.data = []

    def getParams(self):                                # loads external config file and reads lines to get values
        try:
            file = open("PS4RPDconfig.txt", "r")        # open file, read-only
            lines = file.readlines()                    # create a list, each item is 1 line from external file
            file.close()                                # close the external file
            try:
                for i in range(len(lines)):             # number of lines in external file
                    self.data.append(lines[i])               # make each line a new item in list
                    self.data[i] = self.data[i].rstrip("\n")      # remove "\n" if present on every line
            except Exception as e:              # might never be reached now that code is more flexible?
                print("error with config file, please delete it: ", e)

            while True:                                 # runs until "break" is reached
                try:
                    self.data.remove('')                     # remove empty lines that seperate games in config file
                except ValueError:
                    break

            for i in range(len(self.data)):                  # number of items in list
                self.data[i] = self.data[i].split(": ")           # split into [0]: [1]
                self.data[i] = self.data[i][1]                    # remove text so value is only the important data
            try:
                self.ip = self.data[0]
                self.client_id = self.data[1]
                self.sleep_time = int(self.data[2])
                if self.sleep_time < 15:
                    self.sleep_time = 15                    # minimum value of 15 seconds (Discord limitation)
                self.resetTimeOnGameChange = self.data[3]
                self.individualPs1Ps2Covers = self.data[4]
                self.customPs4Covers = self.data[5]
                self.customHomebrewCovers = self.data[6]
            except IndexError as e:
                print("IndexError with config file: ", e)
                print("If all goes well config file is now reset/fixed, if not, delete it.")
                exit(1)

            self.isPS4()                                # call isPS4() function
        except FileNotFoundError:                       # if file does not exist, create it
            print("config file not found\n")
            self.getIP()                                # call getIP() function

    def getIP(self):                                    # allows user to input PS4 IP address
        self.ip = input("Please enter PS4's IP address: ")
        self.isPS4()                                    # call isPS4() function

    def isPS4(self):                                    # tests if input address is the PS4 or not
        try:
            self.ftp.connect(self.ip, 2121)              # connect to PS4's FTP server which is hosted on its IP address, port must be 2121
            self.ftp.login("", "")                      # no default username of password
            self.ftp.cwd("/mnt/sandbox")                # change current directory to where game ID can be found
            self.ftp.quit()                             # close ftp connection

            if os.path.isfile('./PS4RPDconfig.txt') is False: # test if external config file exists
                self.saveParams()                           # call saveParams() function
        except Exception as e:
            print("No FTP server found on ", self.ip, "Error: ", e, "\n")
            self.getIP()                                # call getIP() function

    def saveParams(self):                               # saves IP address and other persisting variables
        file = open("PS4RPDconfig.txt", "w+")           # w+ creates the file if it is missing
        file.write("IP: ")
        file.write(self.ip)                             # save the PS4's IP address to external file

        file.write("\nID: ")
        file.write(self.client_id)                      # save Discord developer application number to external file

        file.write("\nRefresh time(seconds): ")
        file.write(str(self.sleep_time))                # save time to wait between updates to external file

        file.write("\nReset time elapsed on game change: ")
        file.write(self.resetTimeOnGameChange)          # save boolean to external file

        file.write("\nIndividual PS1&PS2 covers: ")
        file.write(self.individualPs1Ps2Covers)

        file.write("\nCustom PS4 covers: ")
        file.write(self.customPs4Covers)

        file.write("\nCustom Homebrew covers: ")
        file.write(self.customHomebrewCovers)

        file.write("\n==================== : ====================\n")

        file.close()

    def findDiscord(self):                              # ensures discord is open
        self.RPC = Presence(self.client_id)             # create pypresence class
        try:
            self.RPC.connect()                          # attempts to connect to open discord client on computer
            print("findDiscord():         found")
        except InvalidPipe:
            print("findDiscord():         !not found!")
            time.sleep(15)                              # allow user time to open/restart/etc discord
            self.findDiscord()                          # call findDiscord() function

    def findPS4(self):                                  # handles if PS4 is turned off/lost connection
        try:
            self.ftp.connect(self.ip,2121)  # connect to PS4's FTP server which is hosted on its IP address, port must be 2121
            self.ftp.login("", "")  # no default username of password
            self.ftp.quit()  # close ftp connection
        except (ConnectionRefusedError, TimeoutError):  # connection refused if PS4 on but FTP server off, timeout if PS4 off
            print("!PS4 not found! \nwaiting 15 seconds and retrying")
            time.sleep(15)
            self.findPS4()


class GatherDetails(object):                            # finds data for the rich presence
    def __init__(self):
        self.gameID = None                              # will hold game's CUSA ID
        self.gameName = None                            # will resolve CUSA ID into a game name
        self.gameImage = None                           # will be validated CUSA ID(?) for Discord developer application art asset
        self.ftp = FTP()                                # create a new instance of FTP class so PrepWorks' doesn't need to stay alive
        self.soup = None                                # HTML of orbispatches page
        self.gameType = None

        self.PS1PS2gameIDs = ["SLPS", "SCAJ", "SLKA", "SLPM", "SCPS", "CF00", "SCKA", "ALCH", "CPCS", "SLAJ", "KOEI",
                              "ARZE", "TCPS", "SCCS", "PAPX", "SRPM", "GUST", "WLFD", "ULKS", "VUGJ", "HAKU", "ROSE",
                              "CZP2", "ARP2", "PKP2", "SLPN", "NMP2", "MTP2", "SCPM",
                              "SLUS", "SCUS", "PBPX",
                              "SLES", "SCES", "SCED"]           # incomplete list of gameIDs for PS1 and PS2 games

    def getGameID(self):
        self.gameID = None                              # bandaid fix. Without this the script will crash when going from displaying a game to displaying the home menu
        self.gameType = None
        gameTypeFound = False

        data = []                                       # create list to hold folder names

        try:
            self.ftp.connect(setup.ip, 2121)         # connect to PS4's FTP server
            self.ftp.login()                                # no default username or password
            self.ftp.cwd("/mnt/sandbox")                    # change active directory to '/mnt/sandbox'
            self.ftp.dir(data.append)                       # produce directory listing, and add it to line by line to the list
            self.ftp.quit()                                 # close the FTP connection

            for i in range(len(data)):
                # print(data[i])                              # prints all directories in /mnt/sandbox with output formatted akin to 'ls -l'
    # this could and should probably use 1 regex search instead of 2
                if re.search('(?!NPXS)([a-zA-Z0-9]{4}[0-9]{5})', data[i]) is not None:       # check each item of data[] for a line that does not match "NPXS", but does match 4 characters, followed by 5 numbers (game ID)
                    self.gameID = re.search('(?!NPXS)([a-zA-Z0-9]{4}[0-9]{5})', data[i])     # when found, assign it to gameID

            if self.gameID is not None:
                self.gameID = self.gameID.group(0)          # remove <re.Match object; etc> junk
                if "CUSA" in self.gameID:
                    self.gameType = "PS4"
                    gameTypeFound = True
                else:
                    for i in range(len(self.PS1PS2gameIDs)):    # go through each item in list
                        if self.PS1PS2gameIDs[i] in self.gameID:    # check if the region ID is the game ID
                            self.gameType = "PS1/PS2"
                            gameTypeFound = True
                if gameTypeFound is not True:
                    self.gameType = "Homebrew"

            print("getGameID():          ", self.gameID)
        except (ConnectionRefusedError, TimeoutError):
            setup.findPS4()

    def getGameInfo(self):                              # uses beautifulSoup and orbispatches to convert game ID to game name
        if self.gameID is not None:
            headers = {"User-Agent": "Mozilla/5.0"}  # headers needed to get around error 403

            # resolve PS4 game name
            if self.gameType == "PS4":
                quote_page = "https://orbispatches.com/en/" + self.gameID       # orbispatches page where game name and image can be found
                try:
                    response = requests.get(quote_page, headers=headers)        # get html from page
                    self.soup = BeautifulSoup(response.text, "html.parser")     # parse html into beautiful soup

                    # get game name from orbispatches
                    self.gameName = str(self.soup.find(class_="game-title"))    # find game Name HTML
                    self.gameName = re.search('"game-title">(.*)</h2>', self.gameName).group(1)  # strip HTML down to just game name
                    print("getGameInfo():       ", self.gameName)

                    if setup.customPs4Covers == "True" or setup.customPs4Covers == "true":
                        self.gameImage = self.gameID
                        self.gameImage = self.gameImage.lower()
                    else:
                        # get game image from orbispatches
                        self.gameImage = str(self.soup.find(class_="game-icon"))    # find game image HTML
                        self.gameImage = re.search('url\((.*)\)', self.gameImage).group(1)  # strip HTML down to just image link
                    print("getGameInfo():       ", self.gameImage)

                except Exception as e:
                    print("getGameInfo():   !error!\n", e)
                    print("Is OrbisPatches down?")

            if self.gameType == "Homebrew":
                self.gameName = "Homebrew"                      # unfortunately haven't fond any way to resolve homebrew IDs
                if setup.customHomebrewCovers == "True" or setup.customHomebrewCovers == "true":
                    self.gameImage = self.gameID.lower()
                else:
                    self.gameImage = "none"
                print("getGameInfo() (name): ", self.gameName)
                print("getGameInfo() (image): ", self.gameImage)

            # resolve PS1 & PS2 game name (very likely terrible code)
            if self.gameType == "PS1/PS2":
                self.gameImage = "ps2ps1temp"       # assumption to use a shared game cover for PS2 and PS1 games
                # attempt to find corresponding PS1 or PS2 game title from game ID
                try:
                    # get game name from github ps1 games.md
                    quote_page = "https://raw.githubusercontent.com/zorua98741/PS4-Rich-Presence-for-Discord/main/PS1%20games.md"   # url to github page containing list of PS1 game id's and the corresponding game name
                    response = requests.get(quote_page, headers=headers)
                    self.soup = BeautifulSoup(response.text, "html.parser")
                    self.gameName = re.search(self.gameID + '.*', str(self.soup))
                    if self.gameName is not None:                               # can be done if its a PS2 game or does not appear in game ID text file
                        self.gameName = self.gameName.group(0)
                        self.gameName = self.gameName.split(';')                # formatting for text file is "GameID;GameName"
                        self.gameName = self.gameName[1]                        # [0] = GameID, [1] = GameName

                        if setup.individualPs1Ps2Covers == "True" or setup.individualPs1Ps2Covers == "true":
                            self.gameImage = self.gameID.lower()                            # don't have to validate game names if using the game ID
                    else:
                        # get game name from github ps2 games.md
                        quote_page = "https://raw.githubusercontent.com/zorua98741/PS4-Rich-Presence-for-Discord/main/PS2%20games.md"
                        response = requests.get(quote_page, headers=headers)
                        self.soup = BeautifulSoup(response.text, "html.parser")
                        self.gameName = re.search(self.gameID + '.*', str(self.soup))
                        if self.gameName is not None:
                            self.gameName = self.gameName.group(0)
                            self.gameName = self.gameName.split(';')
                            self.gameName = self.gameName[1]

                            if setup.individualPs1Ps2Covers == "True" or setup.individualPs1Ps2Covers == "true":
                                self.gameImage = self.gameID.lower()
                        else:                   # couldn't resolve gameID to a gameName
                            print("Unknown gameID: ", self.gameID)
                            self.gameName = "Unknown PS1/PS2 game"
                except Exception as e:
                    print("ERROR: ", e, "\n")
                    print("Very likely you are playing a game not in the external text file, or the external text file is unavailable")
                    self.gameName = "Unknown PS1/PS2 game"
                    self.gameImage = "ps2ps1temp"                       # probably unnecessary

                print("getGameInfo() (name): ", self.gameName)
                print("getGameInfo() (image):", self.gameImage)

        else:                                                               # no game is mounted or open, assume user is on XMB
            self.gameName = "PlayStation 4 Menu"
            self.gameImage = "none"


class ChangePresence(object):
    def __init__(self):
        self.gameIDs = []
        self.appIDs = []
        # self.test = []
        self.appChanged = False
        self.found = False

    def getData(self):                          # only needs to be called once
        for i in range(len(setup.data)-8):      # -8 to exclude config variables and divider (=== : ===)
            if i % 2 == 0:                      # even number items (including 0) are gameIDs
                self.gameIDs.append(setup.data[i+8])
            else:                               # odd number items are Discord developer application IDs
                self.appIDs.append(setup.data[i+8])
            # self.test.append(setup.data[i+8])
        # print(self.gameIDs)
        # print(self.appIDs)

    def testData(self):
        for i in range(len(self.gameIDs)):
            if details.gameID == self.gameIDs[i]:
                print("Developer Application found, modifying Presence")
                setup.RPC.close()
                setup.RPC = Presence(self.appIDs[i])
                setup.RPC.connect()

                self.appChanged = True
                self.found = True
                break
            else:
                self.found = False
        if self.appChanged is True and self.found is False:
            self.appChanged = False
            self.found = False
            print("Changing to Application ID in config")
            setup.RPC.close()
            setup.RPC = Presence(setup.client_id)
            setup.RPC.connect()


class ManipulateGameData(object):
    def __init__(self):
        self.x = 0

    def loadData(self):
        pass

    def saveData(self):
        pass




setup = PrepWork()                                      # create instance of PrepWork class
setup.getParams()                                       # runs through getParams() > getIP() > isPS4()
setup.findDiscord()                                     # ensures discord is open on computer

details = GatherDetails()                               # create instance of GatherDetails class
pres = ChangePresence()
pres.getData()
timer = time.time()
previousGameTitle = ""                                  # initialise variable used so getGameInfo doesn't have to be called every cycle


while True:
    details.getGameID()                                 # find currently open game
    if details.gameID != previousGameTitle:
        previousGameTitle = details.gameID
        details.getGameInfo()                           # convert gameID to game name & image
        pres.testData()
        if setup.resetTimeOnGameChange == "True" or setup.resetTimeOnGameChange == "true":
            timer = time.time()                         # reset time elapsed when a new game is open
    else:
        print("prev getGameInfo():   ", details.gameName, " : ", details.gameImage)
    try:
        setup.RPC.update(details=details.gameName, large_image=details.gameImage, large_text=details.gameID, start=timer)       # set presence data
    except(InvalidPipe, InvalidID):
        setup.findDiscord()
    print("\n")
    gc.collect()
    time.sleep(setup.sleep_time)

# NOTES:
# When attempting to connect to a different FTP server (specifically PS3) get Errno 11001, program is able to recover
# when orbispatches is down program doesn't crash, but no game name or image is shown

# PSP support won't be added unless requested due to considerably bad compatibility and thus low chance of usage
# PS2 and PS1 support is dependent on user naming the game the correct game ID (e.g. SLUS21083 for LEGO Star Wars)

# Instead of having second config for external files, have a dividing line, or heading in PS4RPDconfig.txt and test each line
# of string for the dividing line, when found, every line after it is for resolved game names.
