import pathlib
import shutil
import logging
import os
import sqlite3
import frontmatter
from datetime import datetime
import argparse
import sys
import io
import regex as re

images = re.compile(r'!\[[^\]]*\]\((?P<filename>.*?)(?=\"|\))(?P<optionalpart>\".*\")?\)')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', help="Location of Obsidian vault", default="/home/sagar/Documents/notes")
    parser.add_argument('destination', help="Location of notes folder in Hugo. Typically, something like $HUGO_SITE/content/notes", default="./notes")
    args = parser.parse_args()
    return (args.origin, args.destination)

def delete_target(destination):
    if os.path.isdir(destination):
        shutil.rmtree(destination)
    else:
        logging.info("DESTINATION folder %s does not exist.", str(destination))

def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/copy-assets.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    (origin_str, destination_str) = parse_args()
    origin = pathlib.Path(origin_str)
    destination = pathlib.Path(destination_str)
    logging.info("ORIGIN: %s , DESTINATION: %s", origin_str, destination_str)
    if not os.path.isdir(origin):
        print("ORIGIN folder does not exist. Aborting!")
        sys.exit(1)

    logging.info("DELETING target folder %s", destination_str)
    delete_target(destination)

    sqlitedbfilename = 'logs/assets.db' #TODO: Avoid hardcoded logs directory here
    dbconn = sqlite3.connect(sqlitedbfilename) #TODO: Error checking on this function

    dbconn.execute('''CREATE TABLE IF NOT EXISTS assets (id INTEGER UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT, "from" TEXT NOT NULL, from_title TEXT, "to" TEXT NOT NULL)''')
    dbconn.execute('''DELETE FROM assets''')
    dbconn.execute('''DELETE FROM SQLITE_SEQUENCE WHERE name="assets"''') # reset the autoincrement id
    dbconn.commit()

    for file in origin.rglob("*.md"):
        with open(file, 'r') as f:
            file_content = f.read()
            for image in images.finditer(file_content): # image.group(0) is the matched string, image.group(1) is the path/to/image.ext, image.group(2) is the title, if present
                print(str(file), " --> ", image.group(1))



    #logging.info("COPYING Obsidian vault to target folder %s", destination_str)
    #copy_source_to_target(origin, destination)

    #logging.info("CREATING _index.md files")
    #create_index_files(destination)
    #root_to_index(destination)

    #logging.info ("PRUNING files with publish != True")
    #prune_nopublish(destination)

    #logging.info("ADDING dates to frontmatter")
    #add_frontmatter_date(destination)

if __name__ == "__main__":
    main()
