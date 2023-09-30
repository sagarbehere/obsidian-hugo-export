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

# Below regex detects instances of ![Optional Alt text](path/to/image.ext "Optional title")
# Match group 0 is the whole matched text. Match group 1 is the file path. Match group 2 is the Optional title
images = re.compile(r'!\[[^\]]*\]\((?P<filename>.*?)(?=\"|\))(?P<optionalpart>\".*\")?\)')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', help="Location of Obsidian vault", default="/home/sagar/Documents/notes")
    parser.add_argument('destination', help="Location of notes folder in Hugo. Typically, something like $HUGO_SITE/content/notes", default="./notes")
    args = parser.parse_args()
    return (args.origin, args.destination)

def recreate_target(destination):
    if os.path.isdir(destination):
        shutil.rmtree(destination)
    else:
        logging.info("DESTINATION folder %s does not exist.", str(destination))
    destination.mkdir(parents=True, exist_ok=False)

def to_be_published(file):
    post = frontmatter.load(file)
    if 'publish' in post.keys():
        return (post['publish'])
    else:
        logging.error("ERROR: File %s has no publish key in frontmatter", str(file))
        return False

def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/copy-assets.log', filemode='w', encoding='utf-8', level=logging.DEBUG)
    # examples: origin_str = /home/sagar/Documents/notes/ ; destination_str = /home/sagar/sagar.se/static/assets/images/
    (origin_str, destination_str) = parse_args()
    origin = pathlib.Path(origin_str)
    destination = pathlib.Path(destination_str)
    logging.info("ORIGIN: %s , DESTINATION: %s", str(origin), str(destination))
    if not os.path.isdir(origin):
        print("ORIGIN folder does not exist. Aborting!")
        sys.exit(1)

    logging.info("DELETING target folder %s", destination_str)
    recreate_target(destination)

    for file in origin.rglob("*.md"):
        if to_be_published(file):
            with open(file, 'r') as f:
                file_content = f.read()
                for image in images.finditer(file_content): # image.group(0) is the matched string, image.group(1) is the path/to/image.ext, image.group(2) is the title, if present
                    full_imagefile_path = pathlib.Path(origin, image.group(1).strip("/")) # Need to remove leading / else pathlib.Path will ignore origin. pathlib.Path() ignores all arguments preceding an argument which contains absolute paths
                    # print(str(file), " --> ", str(full_imagefile_path))
                    if os.path.isfile(full_imagefile_path):
                        # Copy it over?
                        logging.info("COPYING %s to %s", str(full_imagefile_path), str(destination))
                        # TODO: Actually copy it
                        shutil.copy2(full_imagefile_path, destination)
                    else:
                        logging.info("FAILED to copy %s because it does not exist.", str(full_imagefile_path))
                f.close()
        else:
            logging.info("SKIPPING %s because it is not to be published.", str(file))

if __name__ == "__main__":
    main()
