 # PS4-Rich-Presence-for-Discord
 Rich presence script for jailbroken playstation 4.  
 Display what game you are playing on the PS4 via Discord, no PSN required!  
 ---
 [![pypresence](https://img.shields.io/badge/using-pypresence-00bb88.svg?style=for-the-badge&logo=discord&logoWidth=20)](https://github.com/qwertyquerty/pypresence)

## Display Example
No game 	| 	PS4 game 	|	PS2 game* 	|	PS1 game* 	|
 -----------|---------------|---------------|---------------|
 ![noGame](https://i.imgur.com/MTrBFew.png) | ![PS4Game](https://i.imgur.com/gtIW76h.png) | ![PS2Game](https://i.imgur.com/riihpST.png) 	| ![PS1Game](https://i.imgur.com/CRRjGFZ.png) 	|  
 
\* PS2 and PS1 will only have custom game covers if you manually upload or [change](https://github.com/zorua98741/PS4-Rich-Presence-for-Discord/wiki#changing-image) the default 

## Warning
```
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```  
If using the compiled .exe, your anti-virus is likely to flag the file, while i promise no malicious code has been added to my release, 
it is the users responsibility to ensure they are not running an "unofficial" release/trojan.

## Quickstart-guide
1. download "PS4RPD.exe" or "PS4RPD.py"
2. enable GoldHen on the PS4.
3. enable the FTP server on the PS4.
4. run the script on your computer (with Discord open).
5. enter either "M" or "A" depending on how you want the script to get the PS4's IP address, and press *enter*.
6. a config file will be generated in the same directory as the script that will allow you to change some options. (values will only update on restart of script)
7. your Discord presence should be updated automatically.

## Contact Me
you can contact me via Discord: "zorua98741".

## Aditional information
[wiki](https://github.com/zorua98741/PS4-Rich-Presence-for-Discord/wiki).

## Known issues/Limitations
- putting the PS4 into rest mode or disconnecting it from the internet and then turning it back on/reconnecting it can cause the FTP server to not respond.
To fix, disable and re-enable the FTP server. (PS4 limitation).
- no mobile support or way to run without a PC (Discord limitation).
- if the user changes the NP Title of a game (or it is incorrect by default), then the presence will use whatever the user changed it to, making the presence display the wrong game (PS4(?) limitation) (needs further research)

## Acknowledgment
- [ORBISPatches](https://orbispatches.com/) and 0x199 for pointing me in the direction of using the tmdb api
- [PS2 games.md](https://github.com/zorua98741/PS4-Rich-Presence-for-Discord/blob/main/PS2%20games.md) sourced from [Veritas83](https://github.com/Veritas83/PS2-OPL-CFG/blob/master/test/PS2-GAMEID-TITLE-MASTER.csv)
- [PS1 games.md](https://github.com/zorua98741/PS4-Rich-Presence-for-Discord/blob/main/PS1%20games.md) sourced from [CRX](https://psxdatacenter.com/information.html)  
- [Tustin](https://github.com/Tustin/PlayStationDiscord-Games/blob/master/script.py) for their tmdb hash code

---
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/N4N87V7K5)
