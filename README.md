# YART GUI Refactoring
Refactoring of Dominique Gallands YART GUI/Client

This repo only adresses the GUI of YART, without touching the communication to the raspi/scanner.

While using YART, we had to adress some runtime issues on the fly.
Also, the handling of the settings was inconsistent when not following a very strict protocol, sometimes even causing exeptions.
For a bit more clarity, we reorganized the GUI and detached input from output channels.
Matplotlib is not threadsafe and was causing headaches. So that was adressed.
This is work in progress and meant to support the main YART project.

See main project:
https://github.com/dgalland/yart



## v0.81:

Generic:
- Switched matplot to Agg backend


## v0.8:

Generic:
- GUI reorganisation
- Global GUI update method
- Storage of all local values
- Relabelling for some GUI elements

Connection:
- Catching timeouts for connections
- Disconnect cleanup steps for motor and camera
Threads:
- Moved image and histo-display from thread to main

Camera:
- Rework of all camera settings (get and put)
- Separation of local settings and current dynamic settings of raspi

Capture:
- Display of scan status (process status & current frame)
- Display of current camera valuers (gains, shutter)
- Separated post processing control
- Runtime crash for nonexisting base dir fixed
- Added base framenumber in addition to tape & clip
Screenshot:

![Screenshot v0.8](https://github.com/patsib/yart_gui/blob/main/img/v0.8b.jpg)
