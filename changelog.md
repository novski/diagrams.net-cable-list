## changelog
### version 0.3.0
changed cable detection based on connections to bold text labels (in parent 
elements as well) to specially created data field `type:cable` due to some common 
Problems when people use bold text somewhere on the page.  
### version 0.2.0
changed the way window.py interacted with main from subproces to import because
pyinstaller can not handle subprocesses with the packaged modules. 
### version 0.2.1
1. added File Menu
2. added Logfile opener
### version 0.2.2-6
1. debug logging levels
### version 0.2.7
1. fix json export