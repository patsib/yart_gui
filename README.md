# YART GUI Refactoring
Refactoring of Dominique Gallands YART GUI/Client

See:
https://github.com/dgalland/yart


v0.8:
Generic:
- GUI reorganisation
- Global GUI update method
- Storage of all local values
- Threadsafe image display
- Relabelling for some GUI elements
Connection:
- Catching timeouts for connections
- Disconnect cleanup steps for motor and camera
Camera:
- Rework of all camera settings (get and put)
- Separation of local settings and current dynamic settings of raspi
Capture:
- Display of scan status (process status & current frame)
- Separated post processing control
- Runtime crash for nonexisting base dir fixed
- Added base framenumber in addition to tape & clip


