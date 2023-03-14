# diagrams.net-cable-list

## What it does:
Find all Cables in an diagrams.net (former draw.io) drawing and create a cable list.

## How it works:
This piece of software contains two entry points. 
The CLI can be executed directly with `python main.py`.
The GUI can be used by starting the `python window.py` which then invokes on the CLI part in a more user frendly way. 
Iterateing over each page it findes all nodes in the xml that have the tag `type`. 
It then creates python dicts for each `type:cable` and it's connected labels.
While "labels" are text boxes ON the cables, connected relationships are often in a group or container,
this script tries to identify a parent node by its text assuming that a box (can be a group or a container) 
description is created in "bold" letters. If it finds one it adds it's text to the 
cables dict. If there is no "bold" text found, it looks up the parent 
cables connected to boxes with "bold" text and adds this instead.

## How to use

### Installation
Download the installers from the 
[releases](https://github.com/novski/diagrams.net-cable-list/releases/latest) page.

or try the manual way:
1. save your drawing as uncompressed file (see Menu) with one of this extensions: 
  - `*.drawio`
  - `*.xml`
2. clone this repo and initialize a virtual environement inside the repository:
  - `git clone https://github.com/novski/diagrams.net-cable-list.git`
  - `cd diagrams.net-cable-list`
  - `python3.10 -m venv <env name>`
  - activate the venv with 
    - [lin/mac] `source <env name>/bin/activate` 
    - [win PS] `<env name>\Scripts\Activate.ps1`
    - [win cmd] `<env name>\Scripts\Activate.bat`
3. install requirements.txt `python -m pip install -r requirements.txt`
4. install post requirements.txt `python -m pip install -r post-requirements.txt`
5. execute `python main.py -h` for list of CLI functions
6. execute `python window.py` for the Graphical Interface

if you run in to problems it will most likely be on Linux. Read this 
[source](https://wxpython.org/Phoenix/snapshot-builds/README.txt) to understand why.
gh-actions linux build works like [this](https://askubuntu.com/questions/1073145/how-to-install-wxpython-4-ubuntu-18-04) with [weel](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.0-cp310-cp310-linux_x86_64.whl).

```bash
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

Test with: `python main.py -nr True -log info -c csv ./tests/drawings/example.drawio`
The output should look somekind like this:
```
python main.py -nr True -log info -c csv ./tests/drawings/example.drawio
2023-01-03 06:58:49,372 {INFO} main.py:[58]:main() starting..
2023-01-03 06:58:49,372 {INFO} scraper.py:[16]:scrape() filepath:./tests/drawings/example.drawio
2023-01-03 06:58:49,372 {INFO} scraper.py:[17]:scrape() starting XML parse...
2023-01-03 06:58:49,373 {INFO} scraper.py:[21]:scrape() get all cables on all pages...
2023-01-03 06:58:49,394 {INFO} cables.py:[20]:get_cables_on_pages() page_name:Sheet-1 - amount of cables: 5
2023-01-03 06:58:49,405 {INFO} cables.py:[20]:get_cables_on_pages() page_name:Sheet-2 - amount of cables: 3
2023-01-03 06:58:49,412 {INFO} cables.py:[20]:get_cables_on_pages() page_name:Sheet-3 - amount of cables: 2
2023-01-03 06:58:49,412 {INFO} cables.py:[34]:set_cables_on_pages() set all cable labels on all pages starting with last number:100
2023-01-03 06:58:49,451 {INFO} cables.py:[50]:set_cables_on_pages() page_name:Sheet-1 - amount of cables: 5
2023-01-03 06:58:49,472 {INFO} cables.py:[50]:set_cables_on_pages() page_name:Sheet-2 - amount of cables: 3
2023-01-03 06:58:49,486 {INFO} cables.py:[50]:set_cables_on_pages() page_name:Sheet-3 - amount of cables: 2
2023-01-03 06:58:49,486 {INFO} export.py:[24]:export() creating drawio...
2023-01-03 06:58:49,487 {INFO} export.py:[28]:export() creating csv...
2023-01-03 06:58:49,487 {INFO} scraper.py:[30]:scrape() total amount of cables: 10
2023-01-03 06:58:49,487 {INFO} main.py:[61]:main() created files: ['./tests/drawings/example-output.drawio', './tests/drawings/example-output.drawio.csv'] in 0.11548658297397196sec.
```
And your /tests/drawings/ folder should now be populated with two additional files:
- `example-output.drawio` that you can open with diagrams.net
- `example-output.csv` wich you can import to your spreadsheet programm of choice and use as list of cables.

### how to draw
- Create a drawing that has uncompressed filesize, for that look in to the menu to uncheck the commpressed save.
- Add two lines or connections and add in the style the datafield `type` with value `cable`. 
  If you have multiple cables the datafield can be copied and pasted to many at once. 
- do the same for `type:device` to get a list of devices (by now it's a future feeture)
- add a source and target label ON the cable (it needs the relationship to the cable) to get 
  an incremented Number on both sides.

## Restrictions:
- window hangs on long tasks (big files) and needs looooong to solve the task. -> read Apendix A
- Not connected cables (loose ends) are omitted.
- Cable Labels are fixed to only digits 00000-09999.
- Cable Numbers are incremented upwards from the highest number found on any page.
- wxpython has certain problems with python 3.10+

## How to debugg:
Debug in stdout with helpers.ET.dump(elements) or to a file with helpers.toOutputXmlFile(elements) function.

## How to start github actions to automaticaly build releases
commit normaly and then add
`git tag v0.1.x`
`git push origin v0.1.x`

## TODO:
- [] change dist output name for linux build to include dist info 'Debian x86'
- [] add Devicelist export
- [] add information panel in menu
- [] create test file import in menu
- [] remove old logfiles in ./log folder
- [] filter CSV export for !page_header lines
- [] add and perform testing suite

# APENDIX
A: Trying to implement threads to dispatch tasks from gui leads to segmentation faults 
due to the usage of logging. The recomended way to solve that is to use a wx.PubSub implementation and 
let the cli app communicate with the gui through that instead of logging to the logger txtbox. This
seams to be another big task and i don't have time right now to solve it. PR are welcome. :-)
