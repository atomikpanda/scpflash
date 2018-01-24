# scpflash
Flash/Install and Uninstall Zips to your jailbroken device

### Place a control file at mypackagefolder/FLASH/control
Just like DEBIAN/control

![Finder Screen Shot](http://cl.ly/p1oi/Screen%20Shot%202018-01-23%20at%2019.13.06.png)

### Then zip your mypackage folder to mypackage.zip
now it is ready to be flashed using scpflash!

```
Usage: ./scpflash.py --ip <ip_addr> --port <device_port> --zip <path_to_archive> [--theos] [--uninstall=pkg_identifier]

Install From Zip: ./scpflash.py --ip 127.0.0.1 --port 2222 --zip mypackage.zip
Uninstall Package Id: ./scpflash.py --ip 127.0.0.1 --port 2222 --uninstall com.yourpackage.id
Uninstall From Zip: ./scpflash.py --ip 127.0.0.1 --port 2222 --zip mypackage.zip --uninstall-zip
Theos Example: ./scpflash.py --zip tweak.zip --theos
```
# TODO:
- after install script
- handle directories
- a tool for converting debs to flashable zips
