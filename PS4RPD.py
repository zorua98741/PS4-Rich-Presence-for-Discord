from ftplib import FTP                                  # used to establish connection between PC and PS4
from os import path                                     # used to test if external config file exists
from pypresence import Presence                         # used for sending data to Discord developer application
from pypresence import InvalidPipe                      # used for handling discord not found on system errors
from pypresence import InvalidID
from time import sleep                                  # used for delaying certain functions
from re import search                                   # used for regular expressions (finding substrings in data)
from time import time                                   # used for time elapsed functionality
from hashlib import sha1                                # used for getting tmdb hash
import hmac                                             # used for getting tmdb hash
from requests import get                                # used for taking tmdb url and getting gameName and image
from bs4 import BeautifulSoup                           # used for fixing formatting of tmdb output


class ExternalFile(object):                             # perform all external file operations (get, normalise, separate)
    def __init__(self):
        self.data = []                                  # holds all external config values
        self.section = []                               # holds where different sections in external file are

        self.s1configVariables = []                     # holds config variables (section 1)

        self.s2appIDVariables = []                      # holds Discord dev app ID variables (section 2)
        self.s2titleIDVariables = []                    # holds titleID variables (section 2)

        self.s3titleIDVariables = []                    # holds titleID variables (section 3)
        self.s3gameNameVariables = []                   # holds game names (section 3)
        self.s3imageVariables = []                      # holds game images (section 3)

    def getData(self):                                  # load external text file and get values for persistent variables
        try:
            file = open("PS4RPDconfig.txt", "r")        # open file read-only
            lines = file.readlines()                    # create list, each item is 1 line from external file
            file.close()
            for i in range(len(lines)):                 # loop for number of items in variable
                self.data.append(lines[i])              # make each line a new item in list
            del lines                                   # no longer needed
            self.normaliseData()                        # remove unneeded formatting from data

            prepWork.ip = self.s1configVariables[0]     # set ip here since s1configVariables could be not used in isPS4()
            prepWork.isPS4()                            # file has been successfully read, check if IP address belongs to PS4
        except FileNotFoundError:                       # external config file does not exist, most likely first run of program
            print("config file not found\n")
            prepWork.getIP()                            # call PrepWork classes getIP() function

    def normaliseData(self):
        self.section = []   # ! reset because getNewData() will call this, needs to be revisited
        for i in range(len(self.data)):
            self.data[i] = self.data[i].rstrip("\n")  # remove "\n" if present on every line
            try:
                self.data[i] = self.data[i].split(": ", 1)  # split into [0]: [1] (specify to split only once)
                self.data[i] = self.data[i][1]  # makes data[i] the value, instead of "info: value"
            except IndexError:
                self.data[i] = self.data[i][0]  # makes external config file more forgiving of format

        while True:             # has to be after removing "\n" for some reason, runs until "break is reached"
            try:
                self.data.remove('')  # removes empty lines
            except ValueError:
                break

        # for i in range(len(self.data)):       # DEBUGGING
            # print(self.data[i])
        # print("\n")                           # DEBUGGING

        for i in range(len(self.data)):         # create list holding where different sections of data begin
            if '=' in self.data[i]:
                self.section.append(i)

        self.variables()
        self.devApps()
        self.previouslyMapped()

    def variables(self):                                    # separate persistent variables from config file
        self.s1configVariables = []                                         # ! reset because getNewData() will call this, needs to be revisited
        for i in range(self.section[0], self.section[1]-1):     # uses section identifiers for flexibility
            self.s1configVariables.append(self.data[i+1])       # add value to list
        if int(self.s1configVariables[2]) < 15:                 # minimum value of 15 seconds for refresh time
            self.s1configVariables[2] = 15
        # print("variables: ", self.s1configVariables)      # DEBUGGING

    def devApps(self):                                      # separate titleID-appID from config file
        self.s2appIDVariables = []  # ! reset because getNewData() will call this, needs to be revisited
        self.s2titleIDVariables = []    # ! reset because getNewData() will call this, needs to be revisited
        for i in range(self.section[1], self.section[2]-1):
            if i % 2 == 1:
                self.s2appIDVariables.append(self.data[i+1])
            else:
                self.s2titleIDVariables.append(self.data[i+1])
        # print("devApps: ", self.s2appIDVariables, self.s2titleIDVariables)        # DEBUGGING

    def previouslyMapped(self):                             # separate previously mapped titleIDs from config file
        self.s3titleIDVariables = []    # ! reset because getNewData() will call this, needs to be revisited
        self.s3gameNameVariables = []   # ! reset because getNewData() will call this, needs to be revisited
        self.s3imageVariables = []      # ! reset because getNewData() will call this, needs to be revisited
        for i in range(self.section[2]+1, len(self.data)):
            line = i                                        # relevant line in data
            i = i - self.section[2]-1                       # since self.section[2] is variable, range will change and make modulus operations wrong, fix by bringing "i" back to 0
            if i % 3 == 0:
                self.s3titleIDVariables.append(self.data[line])
            if i % 3 == 1:
                self.s3gameNameVariables.append(self.data[line])
            if i % 3 == 2:
                self.s3imageVariables.append(self.data[line])
            # self.previouslyMappedVariables.append(self.data[i])
        # print("previouslyMapped: ", self.s3titleIDVariables, self.s3gameNameVariables, self.s3imageVariables)     # DEBUGGING

    def saveData(self):                                     # creates and adds default data to external file
        file = open("PS4RPDconfig.txt", "w+")
        file.write("==========Persistent Variables==========")
        file.write("\nIP: " + str(prepWork.ip))
        file.write("\nID: " + "858345055966461973")
        file.write("\nRefresh time(seconds): " + "120")
        file.write("\nReset time elapsed on game change: " + "True")
        file.write("\n")
        file.write("\n==========Developer Application-to-title IDs==========")
        file.write("\n")
        file.write("\n==========Previously Resolved Games==========")
        file.write("\n")
        file.close()
        self.getNewData()

    def updateIP(self):
        file = open("PS4RPDconfig.txt", "r")                # open file in "read-only" mode
        lines = file.readlines()                            # read in all lines from external file
        lines[1] = "IP: " + str(prepWork.ip) + "\n"         # update the "IP" variable with newly acquired
        file = open("PS4RPDconfig.txt", "w")                # open file in "write" mode
        file.writelines(lines)                              # write all lines back into external file
        file.close()                                        # close the file

    def addMappedGame(self):                                # adds titleID, game name, and image to end of external file
        file = open("PS4RPDconfig.txt", "a")                # open file in "append" mode
        file.write("\ntitleID: " + gatherDetails.titleID)
        file.write("\ngameName: " + gatherDetails.gameName)
        file.write("\nimage: " + gatherDetails.gameImage)
        file.write("\n")
        file.close()

    def getNewData(self):                                   # updates data[] and also the three section lists
        self.data = []      # reset list
        file = open("PS4RPDconfig.txt", "r")        # open file read-only
        lines = file.readlines()                    # create list, each item is 1 line from external file
        file.close()
        for i in range(len(lines)):                 # loop for number of items in variable
            self.data.append(lines[i])              # make each line a new item in list
        del lines                                   # no longer needed
        self.normaliseData()                        # remove unneeded formatting from data


class PrepWork(object):
    def __init__(self):
        self.ip = None
        self.ftp = FTP()
        self.RPC = None

    def getIP(self):
        self.ip = input("Please enter the PS4's IP address: ")
        self.isPS4()

    def isPS4(self):
        try:
            self.ftp.connect(self.ip, 2121)             # connect to FTP server on given IP address
            self.ftp.login("", "")                      # login to FTP server
            self.ftp.cwd("/mnt/sandbox")                # change directory to one known to exist on PS4, but unlikely on other servers
            self.ftp.quit()                             # if the code reaches here then the IP given definitely belongs to a PS4, close connection

            if path.isfile('./PS4RPDconfig.txt') is False:  # if the file does NOT exist, then it must be made with newly acquired PS4 IP address
                externalFile.saveData()
            else:                                               # if it does exist, then only update the "IP" variable
                externalFile.updateIP()

        except Exception as e:
            print("No FTP server found on ", self.ip, "error: ", e)
            self.getIP()                                    # no FTP server on input IP address, ask user for another IP

    def findDiscord(self):
        self.RPC = Presence(externalFile.s1configVariables[1])  # create pypresence class
        try:
            self.RPC.connect()                                  # attempts to connect to open discord client on computer
            print("findDiscord():           found")
        except InvalidPipe:
            print("findDiscord():           !not found!")
            sleep(15)                                           # sleep program for 15 seconds
            self.findDiscord()                                  # call findDiscord() until it is found open

    def findPS4(self):
        try:
            self.ftp.connect(externalFile.s1configVariables[0], 2121)   # connect to PS4's FTP server, port must be 2121
            self.ftp.login("", "")                                      # no default username or password
            self.ftp.quit()                                             # close FTP session
        except (ConnectionRefusedError, TimeoutError):                  # ConnectionRefused when PS4 on, but FTP server off, Timeout when PS4 off
            print("findPS4():           !PS4 not found! Waiting 15 seconds and retrying")
            sleep(15)                                                   # sleep program for 15 seconds
            self.findPS4()                                              # call findPS4() until it is found with FTP server enabled


class GatherDetails(object):
    def __init__(self):
        self.ftp = FTP()
        self.titleID = None
        self.gameType = None
        self.PS1PS2gameIDs = ["SLPS", "SCAJ", "SLKA", "SLPM", "SCPS", "CF00", "SCKA", "ALCH", "CPCS", "SLAJ", "KOEI",
                              "ARZE", "TCPS", "SCCS", "PAPX", "SRPM", "GUST", "WLFD", "ULKS", "VUGJ", "HAKU", "ROSE",
                              "CZP2", "ARP2", "PKP2", "SLPN", "NMP2", "MTP2", "SCPM",
                              "SLUS", "SCUS", "PBPX",
                              "SLES", "SCES", "SCED"]           # incomplete list of gameIDs for PS1 and PS2 games
        self.tmdbKey = bytearray.fromhex('F5DE66D2680E255B2DF79E74F890EBF349262F618BCAE2A9ACCDEE5156CE8DF2CDF2D48C71173CDC2594465B87405D197CF1AED3B7E9671EEB56CA6753C2E6B0')
        self.gameName = None
        self.gameImage = None

        self.appChanged = False
        self.found = False

    def getTitleID(self):
        self.titleID = None             # ! bandaid fix ! fixes crash of going from game to main menu
        data = []                                                       # variable to hold folders in PS4 folder
        gameTypeFound = False
        try:
            self.ftp.connect(externalFile.s1configVariables[0], 2121)   # connect to PS4's FTP server, post must be 2121
            self.ftp.login()                                            # no default username or password
            self.ftp.cwd("/mnt/sandbox")                                # change active directory
            self.ftp.dir(data.append)                                   # get directory listing and add each item to to list with formatting similar to "ls -l"
            self.ftp.quit()                                             # close FTP connection

            for i in range(len(data)):
                if search('(?!NPXS)([a-zA-Z0-9]{4}[0-9]{5})', data[i]) is not None:   # annoying that regex has to be done twice
                    self.titleID = search('(?!NPXS)([a-zA-Z0-9]{4}[0-9]{5})', data[i])

            if self.titleID is not None:
                self.titleID = self.titleID.group(0)                    # remove <re.Match object> etc> junk
                if "CUSA" in self.titleID:                              # must be a PS4 game to be true
                    self.gameType = "PS4"
                    gameTypeFound = True
                else:
                    for i in range(len(self.PS1PS2gameIDs)):
                        if self.PS1PS2gameIDs[i] in self.titleID:       # must be a PS1/PS2 game
                            self.gameType = "PS1/PS2"
                            gameTypeFound = True
            if gameTypeFound is False:
                self.gameType = "Homebrew"

            print("getTitleID():        ", self.titleID)
        except (ConnectionRefusedError, TimeoutError):                  # ConnectionRefused for PS4 on FTP server off, Timeout for PS4 off
            prepWork.findPS4()                                          # call PrepWork's findPS4() function

    def checkMappedGames(self):
        found = False
        if not externalFile.s3titleIDVariables:
            print("checkMappedGames():         !list is empty!")
            self.getGameInfo()
            found = True            # not actually found, but stops from running getGameInfo() twice
        if self.titleID is not None:
            for i in range(len(externalFile.s3titleIDVariables)):
                if self.titleID == externalFile.s3titleIDVariables[i]:      # check if titleID is in external file
                    found = True
                    self.gameName = externalFile.s3gameNameVariables[i]
                    self.gameImage = externalFile.s3imageVariables[i]
        if found is not True:
            print("checkMappedGames():         !game is not mapped!")
            self.getGameInfo()
        else:
            print("checkMappedGames():          ", self.titleID, " : ", self.gameName, " : ", self.gameImage)

    def getGameInfo(self):
        if self.titleID is not None:
            if self.gameType == "PS4":
                modifiedTitleID = self.titleID + "_00"                                  # tmdb titleID's add "_00" to the end for whatever reason
                Hash = hmac.new(self.tmdbKey, bytes(modifiedTitleID, 'utf-8'), sha1)   # get hash of tmdb key using sha1 encryption
                Hash = Hash.hexdigest().upper()
                url = "http://tmdb.np.dl.playstation.net/tmdb2/" + modifiedTitleID + "_" + Hash + "/" + modifiedTitleID + ".json"     # url containing game name and image
                response = get(url, headers={"User-Agent": "Mozilla/5.0"})  # get HTML of website
                soup = BeautifulSoup(response.text, "html.parser")          # use bs4 to make data readable (fix odd formatting)

                try:
                    self.gameName = search('{"name\":\"(.*?)"', str(soup))  # get gameName from html
                    self.gameName = self.gameName.group(1)                  # remove regex junk

                    self.gameImage = search('{"icon":"(.*?)"', str(soup))   # get gameImage from html
                    self.gameImage = self.gameImage.group(1)                # remove regex junk
                    externalFile.addMappedGame()
                except AttributeError:                                      # not all PS4 games have a tmdb page for some reason
                    print("getGameInfo():           !no game found!")
                    self.gameName = "Unknown"
                    self.gameImage = "none"

            if self.gameType == "Homebrew" and self.titleID is not None:
                self.gameName = "Homebrew"                                                          # unfortunately no way found to resolve homebrew ID to a name
                self.gameImage = "none"
                externalFile.addMappedGame()

            if self.gameType == "PS1/PS2":
                self.gameImage = "ps2ps1temp"                           # PS1 and PS2 games use shared cover unless otherwise specified
                try:
                    quote_page = "https://raw.githubusercontent.com/zorua98741/PS4-Rich-Presence-for-Discord/main/PS1%20games.md"   # url to github page containing list of PS1 game id's and the corresponding game name
                    response = get(quote_page, headers={"User-Agent": "Mozilla/5.0"})                                               # get HTML of page
                    soup = BeautifulSoup(response.text, "html.parser")                                                              # make HTML formatted correctly
                    self.gameName = search(self.titleID + '.*', str(soup))                                                          # search for the open game's titleID in HTML document
                    if self.gameName is not None:                                                                                   # if its found remove formatting
                        self.gameName = self.gameName.group(0)
                        self.gameName = self.gameName.split(';')
                        self.gameName = self.gameName[1]                                                                # lower() used since Discord only accepts lowercase characters
                    else:                                                                                                           # if its not found perhaps open game is a PS2 game
                        quote_page = "https://raw.githubusercontent.com/zorua98741/PS4-Rich-Presence-for-Discord/main/PS2%20games.md"   # url to github page containing list of PS2 game id's and the corresponding game name
                        response = get(quote_page, headers={"User-Agent": "Mozilla/5.0"})
                        soup = BeautifulSoup(response.text, "html.parser")
                        self.gameName = search(self.titleID + '.*', str(soup))
                        if self.gameName is not None:
                            self.gameName = self.gameName.group(0)
                            self.gameName = self.gameName.split(';')
                            self.gameName = self.gameName[1]
                except Exception as e:                                                                                              # if not found then game may be missing from list, or the github page is unavailable
                    print("Error: ", e, "\n")
                    self.gameName = "Unknown PS1/PS2 game"
                externalFile.addMappedGame()
        else:
            self.gameName = "Playstation 4 Menu"
            self.gameImage = "none"

        print("getGameInfo():           ", self.gameName, " : ", self.gameImage)

    def changeDevApp(self):     # needs to be revised
        for i in range(len(externalFile.s2titleIDVariables)):
            if gatherDetails.titleID == externalFile.s2titleIDVariables[i]:
                print("Developer Application found, modifying presence")
                prepWork.RPC.close()
                prepWork.RPC = Presence(externalFile.s2appIDVariables[i])
                prepWork.RPC.connect()

                self.appChanged = True
                self.found = True
                break
            else:
                self.found = False
        if self.appChanged is True and self.found is False:
            self.appChanged = False
            self.found = True
            print("Changing to default Application ID in config file")
            prepWork.RPC.close()
            prepWork.RPC = Presence(externalFile.s1configVariables[1])
            prepWork.RPC.connect()


allowed = ["True", "true"]

externalFile = ExternalFile()
prepWork = PrepWork()
gatherDetails = GatherDetails()

externalFile.getData()                  # get data from external text file or create it, and verify it belongs to PS4
print("\n")
prepWork.findDiscord()                  # ensure discord is open

previousTitleID = ""
timer = time()                          # start timer for time elapsed functionality

while True:
    gatherDetails.getTitleID()          # get game's titleID from PS4 via FTP
    if gatherDetails.titleID != previousTitleID:    # used so webpage does not need to be contacted if the details will be the same
        previousTitleID = gatherDetails.titleID     # update previously opened game
        gatherDetails.checkMappedGames()
        externalFile.getNewData()
        gatherDetails.changeDevApp()
        if externalFile.s1configVariables[3] in allowed:
            timer = time()
    else:
        print("prevGetGameInfo():       ", gatherDetails.gameName, " : ", gatherDetails.gameImage)
    try:
        prepWork.RPC.update(details=gatherDetails.gameName, large_image=gatherDetails.gameImage, large_text=gatherDetails.titleID, start=timer)
    except(InvalidPipe, InvalidID):
        prepWork.findDiscord()
    print("\n")
    sleep(int(externalFile.s1configVariables[2]))
