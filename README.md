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
this script tries to identify a parent node by its text assuming that a box (can be a group or a container) 
description is created in "bold" letters. If it finds one it adds it's text to an dict on the 
cables dict. If there is no "bold" text found, it looks up the parent 
cables connected to boxes with "bold" text and adds this instead.

## How to use:
1. save your drawing as uncompressed file with one of this extensions: 
  - `*.drawio`
  - `*.xml`
2. clone this repo and initialize a virtual environement inside the repository:
  - `git clone https://github.com/novski/diagrams.net-cable-list.git`
  - `cd diagrams.net-cable-list`
  - `python3.9 -m venv <env name>`
  - activate the venv with 
    - [lin/mac] `source <env name>/bin/activate` 
    - [win PS] `<env name>\Scripts\Activate.ps1`
    - [win cmd] `<env name>\Scripts\Activate.bat`
3. install requirements.txt `python -m pip install -r requirements.txt`
4. execute `python main.py -h` for list of CLI functions
5. execute `python window.py` for the Graphical Interface

..or download the installers from the 
[releases](https://github.com/novski/diagrams.net-cable-list/releases/latest) page.

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
- `example-output.drawio.csv` wich you can import to your spreadsheet programm of choice and use as list of cables.

## Restrictions:
- Not connected cables (loose ends) are omitted.
- Cable Labels are fixed to digits 00000-09999.
- Cable Numbers are incremented from the highest number found on any page.
- wxpython has certain problems with python 3.10+

## How to debugg:
Debug in stdout with helpers.ET.dump(elements) or to a file with helpers.toOutputXmlFile(elements) function.

## TODO:
- [] filter CSV export for !page_header lines
- [] add and perform testing suite
