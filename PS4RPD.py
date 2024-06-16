from pathlib import Path  # getting location of config file
import json  # get and set values for external config file
from socket import socket, AF_INET, SOCK_DGRAM  # get host's IP address
import re  # various string manipulation via regex
import networkscan  # get list of devices on user's network
from ftplib import FTP  # connection between PC and device
from pypresence import Presence  # sends presence data to Discord client
from pypresence.exceptions import DiscordNotFound  # handles when Discord cannot be found as process
from pypresence.exceptions import PipeClosed   # handles when Discord was previously connected to but is no longer found
from time import sleep, time  # adds delay to program. Plus "time elapsed" functionality for presence
import hmac     # generate link for tmdb
from hashlib import sha1    # generate link for tmdb
import requests     # get data from website

default_config = {
    "var": {
        "ip": "",  # IPv4 address belonging to device
        "client_id": 858345055966461973,  # Discord developer application ID
        "wait_time": 120,           # how long to wait before grabbing new data
        "retro_covers": True,       # will try to show separate covers if set to True
        "hibernate": False,         # whether IP prompt is shown when fail to connect to ps4, or to wait (previously "ip_prompt")
        "hibernate_time": 600,      # how long to wait before attempting to reconnect
        "presence_on_home": True,   # will disconnect from Discord if set to False
        "use_devapps": False,       # whether script will try and change dev app based on titleID
        "show_timer": False         # whether to show time elapsed. Currently not useful if "hibernate" is used.
    },
    "devapps": [
        {"devid": "", "titleid": ""}
    ],
    "mapped": [

    ]
}
title_id_dict = {
    "PS4": "CUSA",
    "PS1/2": ["SLES", "SCES", "SCED", "SLUS", "SCUS", "SLPS", "SCAJ", "SLKA", "SLPM", "SCPS", "CF00", "SCKA", "ALCH",
              "CPCS", "SLAJ", "KOEI", "ARZE", "TCPS", "SCCS", "PAPX", "SRPM", "GUST", "WLFD", "ULKS", "VUGJ", "HAKU",
              "ROSE", "CZP2", "ARP2", "PKP2", "SLPN", "NMP2", "MTP2", "SCPM", "PBPX"],
}
tmdb_key = bytearray.fromhex('F5DE66D2680E255B2DF79E74F890EBF349262F618BCAE2A9ACCDEE5156CE8DF2CDF2D48C71173CDC2594465B87405D197CF1AED3B7E9671EEB56CA6753C2E6B0')
config_path = Path("ps4rpdConfig.txt")


class PrepWork:
    def __init__(self):
        self.config = default_config  # default config will be used if config file is not found
        self.RPC = None

    def read_config(self):
        if config_path.is_file():  # file exists
            with config_path.open(mode="r") as f:
                try:
                    self.config = json.load(f)  # load config from external file
                except json.decoder.JSONDecodeError as e:
                    print(f"read_config():   error with JSON (config file): {e}")
                f.close()
            if self.test_for_ps4(self.config["var"]["ip"]) is False:
                # check that IP still belongs to PS4 and that it is online.
                if self.config["var"]["hibernate"] is False:
                    self.prompt_user()
                else:
                    while self.test_for_ps4(self.config["var"]["ip"]) is False:
                        print(f"read_config():   ps4 not found, hibernating {self.config['var']['hibernate_time']} seconds")
                        sleep(self.config["var"]["hibernate_time"])
        else:  # file does not exist
            self.prompt_user()  # ask user how to get the devices IP address

    def prompt_user(self):
        print("Get PS4's IP address Automatically or Manually?")
        choice = "placeholder"
        accepted = ["a", "m"]
        while choice[0].lower() not in accepted:  # loop until first character of user input is either "a" or "m"
            choice = input("Please enter either 'a' or 'm': ")
        if choice[0].lower() == "a":  # use networkscan to try and find device automatically
            self.scan_network()
        elif choice[0].lower() == "m":  # allow user to manually enter device IP address
            self.get_ip_from_user()
        else:  # this should never be reached
            exit("Unexpected input")

    def scan_network(self):
        try:
            temp_sock = socket(AF_INET, SOCK_DGRAM)
            temp_sock.connect(("8.8.8.8", 80))
            host_ip = temp_sock.getsockname()[0]  # host IP address
            temp_sock.close()
        except Exception as e:
            print(f"Error while getting host network. '{e}'")
            self.get_ip_from_user()
        else:
            host_ip = re.search("^(.*)\.", host_ip).group(
                0) + "0/24"  # replace 4th octet and add short-form subnet mask
            print(f"Expected network is '{host_ip}'.")

            scan = networkscan.Networkscan(host_ip)
            scan.run()
            print(f"Completed network scan: {scan.list_of_hosts_found}")
            # ps4_ip = [i for i in scan.list_of_hosts_found if test_for_ps4(i) is True] # list comprehension alternative
            ps4_ip = None
            for i in range(len(scan.list_of_hosts_found)):  # iterate through list of IP addresses
                if self.test_for_ps4(scan.list_of_hosts_found[i]):
                    ps4_ip = scan.list_of_hosts_found[i]
                    break  # break out of loop since the device has been found
            if ps4_ip is None:  # no device on network belongs to device
                print("No device on network was found to belong to a Jailbroken PS4 running an FTP server.")
                self.prompt_user()
            else:
                self.save_config(ps4_ip)

    def get_ip_from_user(self):
        ip = input("Please enter the PS4's IP address: ")
        while self.test_for_ps4(ip) is False:
            ip = input("Please enter the PS4's IP address: ")
        self.save_config(ip)

    def test_for_ps4(self, ip):
        ftp = FTP()
        ftp.set_pasv(False)
        try:
            ftp.connect(ip, 2121)  # device uses port 2121
            ftp.login("", "")  # device has no creds by default
            ftp.cwd("/mnt/sandbox/NPXS20001_000")  # device has path as specified (NPXS20001: SCE_LNC_APP_TYPE_SHELL_UI)
            ftp.quit()  # close FTP connection
        except Exception as e:
            print(f"test_for_ps4():     No FTP server found on '{ip}'. '{e}'.")
            return False  # some error was encountered, FTP server required does not exist on given IP
        else:
            print(f"test_for_ps4():     PS4 found on '{ip}'")
            return True  # no errors were encountered, an FTP server with no login creds, and "/mnt/sandbox" exists

    def save_config(self, ip):
        self.config["var"]["ip"] = ip
        with config_path.open(mode="w+") as f:  # will create file if it doesn't exist, overwrite it if it does
            json.dump(self.config, f, indent=4)     # write entire config to file
            f.close()   # close file, needed for when file is open in smart text editors (e.g. notepad++) to reload

    def connect_to_discord(self):  # Not called by any other function in PrepWork()
        while True:
            try:
                self.RPC = Presence(self.config["var"]["client_id"])  # clientID from Discord developer application
                self.RPC.connect()  # attempt to connect to Discord
                print("Connected to Discord client")
                break  # break out of while loop
            except DiscordNotFound as e:  # handle scenarios where Discord is not running or is otherwise broken.
                print(f"! Could not find Discord running. '{e}'.")
                sleep(20)  # wait 20 seconds before retrying

    def save_game_info(self, data):     # called in GatherDetails class, probably shouldn't be here
        self.config["mapped"].append(data)  # contains {"titleid": val, "name": val, "image": val}
        with config_path.open(mode="w+") as f:
            json.dump(self.config, f, indent=4)
            f.close()


class GatherDetails:
    def __init__(self):
        self.title_id = None
        self.game_type = None
        self.game_name = None
        self.game_image = None
        self.dev_app_changed = False

    def get_title_id(self):     # function always called
        ftp = FTP()
        data = []
        self.title_id, self.game_type, = None, None     # reset every run
        try:
            ftp.connect(pw.config["var"]["ip"], 2121)  # uses port 2121 for ftp
            ftp.login("", "")   # no login credentials
            ftp.cwd("/mnt/sandbox")     # change directory
            ftp.dir(data.append)    # get directory listing, add each item to list
            ftp.quit()  # close FTP connection
        except (ConnectionRefusedError, TimeoutError) as e:     # couldn't connect to PS4
            # pw.RPC.clear()    # TODO?
            print("get_title_id():  PS4 not found, sleeping")
            while pw.test_for_ps4(pw.config["var"]["ip"]) is False:
                if pw.config["var"]["hibernate"] is False:
                    sleep(pw.config["var"]["wait_time"])
                else:
                    sleep(pw.config["var"]["hibernate_time"])
        else:   # neither error above were raised
            print(data)     # "debugging" for Github issue 4
            for item in data:   # loop through each folder found from directory
                if (res := re.search("(?!NPXS)([a-zA-Z0-9]{4}[0-9]{5})", item)) is not None:    # Assignment expression,
                    # do not match NPXS, do match 4 characters followed by 5 numbers (Homebrew can use titleIDs with prefix other than "CUSA")
                    self.title_id = res.group(0)     # remove regex junk
            if self.title_id is None:    # user is on homescreen
                self.title_id = "main_menu"     # discord art asset naming conventions (no spaces, no capitals)
                self.game_image = self.title_id
            else:   # user is in some program (PS4 game, homebrew, retro game, etc)
                if self.title_id[:4] in title_id_dict.get("PS4"):    # first 4 characters from title_id removes numbers
                    self.game_type = "PS4"
                elif self.title_id[:4] in title_id_dict.get("PS1/2"):
                    self.game_type = "PS1/2"
                else:
                    self.game_type = "Homebrew"
        print(f"get_title_id():  {self.title_id, self.game_type}")

    def check_mapped(self):
        self.game_name, self.game_image = None, self.title_id   # game_image is title_id to assume user is on home screen
        found = False   # boolean to know if a game has to be mapped
        for mapped in pw.config["mapped"]:  # mapped is dict of {titleid, name, image}
            if self.title_id == mapped["titleid"]:  # currently open game is already mapped, retrieve name and image
                self.game_name = mapped["name"]
                self.game_image = mapped["image"]
                print(f"check_mapped():  {self.game_name, self.game_image}")
                found = True
                break   # stop loop as there should only ever be one match per titleID
        if not found and self.title_id != "main_menu":   # currently open game is NOT already mapped, don't save m menu
            print("check_mapped():  game has not been mapped yet.")
            if self.game_type == "PS4":     # use tmdb to try and get name and image from titleID
                self.get_ps4_game_info()
            elif self.game_type == "PS1/2":     # use web doc of ps1/2 to get name from titleID
                self.get_classic_game_info()
            else:
                self.get_other_game_info()

    def get_ps4_game_info(self):    # Uses Sony's TMDB api to resolve a titleID to a name and image
        # note that some titleIDs do NOT have an entry in the TMDB
        title_id = self.title_id+"_00"
        title_id_hash = hmac.new(tmdb_key, bytes(title_id, "utf-8"), sha1)    # get hash of tmdb key using sha1
        title_id_hash = title_id_hash.hexdigest().upper()
        url = f"http://tmdb.np.dl.playstation.net/tmdb2/{title_id}_{title_id_hash}/{title_id}.json"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})     # get data from url
        if response.ok:     # webpage exists
            j = json.loads(response.text)   # convert from string to dict
            self.game_name = j["names"][0]["name"]
            self.game_image = j["icons"][0]["icon"]
            print(f"get_ps4_game_info():     {self.game_name, self.game_image}")
        else:   # webpage does not exist
            print(f"get_ps4_game_info():     No entry found in TMDB for {self.title_id}")
            self.game_name = self.title_id
            self.game_image = self.title_id.lower()     # lower() for Discord developer app images
        pw.save_game_info({"titleid": self.title_id, "name": self.game_name, "image": self.game_image})

    def get_classic_game_info(self):    # Uses online text document of PS1 and PS1 games to resolve a titleID to a name
        # game_image will be the titleID, for use in Discord developer application image names
        p1 = "https://raw.githubusercontent.com/zorua98741/PS4-Rich-Presence-for-Discord/main/PS1%20games.md"   # PS1
        p2 = "https://raw.githubusercontent.com/zorua98741/PS4-Rich-Presence-for-Discord/main/PS2%20games.md"   # PS2
        if pw.config["var"]["retro_covers"] is True:
            self.game_image = self.title_id.lower()     # try and use image from Discord dev app
        else:
            self.game_image = "ps2ps1temp"  # use single image
        if (res := self.search_classic(p1)) is not False:
            self.game_name = res    # PS1 game detected
        elif (res := self.search_classic(p2)) is not False:
            self.game_name = res    # PS2 game detected
        else:
            self.game_name = "Unknown"  # titleID not found in either external file
        pw.save_game_info({"titleid": self.title_id, "name": self.game_name, "image": self.game_image})
        print(f"get_classic_game_info():     {self.game_name, self.game_image}")

    def search_classic(self, url):
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})     # send request to page
        if response.ok:     # webpage exists
            if (res := re.search(f"{self.title_id}.*", response.text)) is not None:
                name = res.group(0).split(";", 1)   # name is a list of [titleID, game name]
                return name[1]
        return False

    def get_other_game_info(self):  # Homebrew, and anything else not detected as either PS4 or PS1/PS2 game
        # This is a placeholder for when/if a way to map other programs is thought of
        if self.title_id != "main_menu":
            self.game_name = self.title_id
            self.game_image = self.title_id.lower()     # lower() for Discord dev app images
            pw.save_game_info({"titleid": self.title_id, "name": self.game_name, "image": self.game_image})
            print(f"get_other_game_info():   {self.game_name, self.game_image}")

    def change_dev_app(self):
        found = False
        for app in pw.config["devapps"]:
            if app["titleid"] == self.title_id:
                print("change_dev_app():    changing to new developer app")
                found = True
                self.dev_app_changed = True
                pw.RPC.close()  # disconnect presence
                pw.RPC = Presence(app["devid"])     # change "Presence()" client_id
                pw.RPC.connect()    # reconnect presence here
                break   # exit loop since match was found
        if not found and self.dev_app_changed is True:
            print("change_dev_app():    reverting to default developer app")
            self.dev_app_changed = False
            pw.RPC.close()
            pw.RPC = Presence(pw.config["var"]["client_id"])
            pw.RPC.connect()



pw = PrepWork()
gd = GatherDetails()
timer = time()

def driver():   # hopefully temp driver function, overly messy
    pw.read_config()
    pw.connect_to_discord()  # called here as *something* clashes with networkscan
    prev_titleid = ""
    while True:
        gd.get_title_id()
        if prev_titleid == gd.title_id:     # same program as before is open
            print(f"reusing previous presence data for {gd.game_name}")
        else:   # a new program has been opened
            gd.check_mapped()
            prev_titleid = gd.title_id
            if pw.config["var"]["use_devapps"] is True:
                gd.change_dev_app()
        if pw.config["var"]["presence_on_home"] is False and gd.title_id == "main_menu":
            pw.RPC.clear()  # may need to be changed to RPC.close() ?
        else:
            try:
                if pw.config["var"]["show_timer"] is False:
                    pw.RPC.update(details=gd.game_name, large_image=gd.game_image, large_text=gd.title_id)
                else:
                    pw.RPC.update(details=gd.game_name, large_image=gd.game_image, large_text=gd.title_id, start=timer)
            except PipeClosed as e:
                print("Error with Discord: ", e)
                pw.connect_to_discord()
        print('')
        sleep(pw.config["var"]["wait_time"])


driver()