# diagrams.net-cable-list
A script to generate a cable list out of diagrams.net (draw.io) drawings.

## What it does:
Find all Cables in an diagrams.net (former draw.io) drawing and create a cable list.

## How to use:
1. Define output as debuglevel in __main__.
2. Define your not compressed exported diagrams.net file as path in scrape().
3. start as script with `python3 cable.py`.

## How it works:
Iterateing over each page it scrapes all nodes in the xml that have the tag 'source' 
and (!) 'target' creating dicts for each cable and its connections or labels.
While labels are text boxes on the cables connected relationships are often in a group,
this script tries to identify a parent node by its text assuming that an box description is 
created in "bold" letters. If it finds one it adds it's text to an separate dict on the 
cables descriptive dict. If there is no "bold" text found it looks up the parent 
cables connected to boxes with "bold" text and adds this instead.

## Restrictions:
Not connected cables (loose ends) are omitted.

## How to debugg:
Debug in stdout with  ET.dump(elements) or to a file with toOutputXmlFile(elements) function.

## TODO:
- [] Add CSV export
- [] Add loglevel as CLI input
- [] think about possibilities of interactive path/file and options  
