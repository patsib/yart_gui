# YART GUI Refactoring
Refactoring of Dominique Gallands YART GUI/Client

This repo only adresses the GUI of YART, without touching the communication to the raspi/scanner.<br/>
This version can be used in parallel with the original GUI. Just put the GUIControl_Refactor directory next to your existing GUIControl.

While using YART, we had to adress some runtime issues on the fly.
Also, the handling of the settings was inconsistent when not following a very strict protocol, sometimes even causing exeptions.
For a bit more clarity, we reorganized the GUI and detached input from output channels.
Matplotlib is not threadsafe and was causing headaches. So that was adressed.

**This is work in progress and meant to support the main YART project.**<br/>
See main project: https://github.com/dgalland/yart



#### v0.81:

Generic:
- Switched matplot to Agg backend
- Adressed tk refresh/shutdown exceptions


#### v0.8:

Generic:
- GUI reorganisation and global update method
- Adressed storage of all local values
- Minor text corrections

Connection:
- Adressed connection timeouts
- Adressed disconnect sequence

Threads:
- Moved tk methods to main thread (tk not threadsafe)

Camera:
- Separation of all camera settings (get and put)
- Separation of primary settings and current capture settings (feedback channel)

Capture:
- Display of scan status (process status & current frame)
- Display of current camera valuers (gains, shutter)
- Separated post processing control
- Adressed exception for nonexisting base dir
- Added base framenumber in addition to tape & clip

Screenshot:

![Screenshot v0.8](https://github.com/patsib/yart_gui/blob/main/img/v0.8b.jpg)
