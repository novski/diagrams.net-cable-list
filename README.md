# diagrams.net-cable-list


## What it does:
Find all Cables in an diagrams.net (former draw.io) drawing and create a cable list.

## How it works:
This piece of software contains two user-levels. 
The CLI can be executed directly with `python main.py`.
The GUI can be used by starting the `python window.py` which then invokes on the CLI part in a more user frendly way. 
Iterateing over each page it findes all nodes in the xml that have the tag 'source' 
and (!) 'target' creating python dicts for each cable and its connections or labels.
While "labels" are text boxes on the cables, connected relationships are often in a group,
this script tries to identify a parent node by its text assuming that a box (can be a group or a container) description is created in "bold" letters. If it finds one it adds it's text to an dict on the 
cables dict. If there is no "bold" text found, it looks up the parent 
cables connected to boxes with "bold" text and adds this instead.

## How to use:
1. use virtual env `python3 -m venv <env name>`
2. install requirements.txt `python -m pip install -r requirements.txt`
3. execute `python main.py -h` for list of functions

```
usage: main.py [-h] [-o OUTPUTPATH] [-n OUTPUTNAME] [-c [CABLESHEET]] [-nr [RENUMBER]] [-log [LOGGLEVEL]] [-loggpath [LOGGPATH]] filepath

positional arguments:
  filepath              add filepath

options:
  -h, --help            show this help message and exit
  -o OUTPUTPATH         define where to save the generated files.
  -n OUTPUTNAME         output filename
  -c [CABLESHEET]       define if cablesheet should be saved. There are two choices: 'json' or 'csv'.
  -nr [RENUMBER]        define if the cable numbers should be . renumbered as True or False. Default is True
  -log [LOGGLEVEL]      define the logglevel. Default is INFO
  -loggpath [LOGGPATH]  define if the path where the log should be stored. Default is ./log/
```

## Restrictions:
Not connected cables (loose ends) are omitted.

## How to debugg:
Debug in stdout with  ET.dump(elements) or to a file with toOutputXmlFile(elements) function.

## TODO:
- [] Add CSV export
