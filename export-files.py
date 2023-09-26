import pathlib
import shutil
import logging
import os
import sqlite3
import frontmatter
from datetime import datetime
import argparse
import sys

# List of folder and files to be excluded
excludes = ['daily notes', 'drafts', 'no publish', '.git', '.obsidian', '.gitignore'] #TODO: Avoid hardcoding?

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', help="Location of Obsidian vault", default="/home/sagar/Documents/notes")
    parser.add_argument('destination', help="Location of notes folder in Hugo. Typically, something like $HUGO_SITE/content/notes", default="./notes")
    args = parser.parse_args()
    return (args.origin, args.destination)

def prune_nopublish(destination):
    for file in destination.rglob("*.md"):
        post = frontmatter.load(file)
        if 'publish' in post.keys():
            if post['publish'] != True:
                logging.info("%s has frontmatter publish = %s which is not True", file, post['publish'])
                logging.info("Removing file %s because publish != True", file)
                os.remove(file)
        else:
            logging.warning("Removing file %s because it has no publish key in frontmatter", file)
            os.remove(file)

def copy_source_to_target(origin, destination):
    # The * in *excludes below is the unpack operator. It unpacks the list and presents its contents as arguments to the function
    # the ignore= is used to exclude the folders/files in excludes from being copied
    shutil.copytree(origin, destination, ignore=shutil.ignore_patterns(*excludes) , dirs_exist_ok=True)

def delete_target(destination):
    if os.path.isdir(destination):
        shutil.rmtree(destination)
    else:
        logging.info("DESTINATION folder %s does not exist.", str(destination))

def create_index_files(destination):
    for root, dirs, files in os.walk(destination):
        for dir in dirs:
            # If it contains at least one .md file, then create _index.md if it does not already exist
            if any(filename.endswith(".md") for filename in os.listdir(os.path.join(root, dir))):
                if not os.path.isfile(os.path.join(root, dir, '_index.md')): #_index.md does not exist
                    indx_file = pathlib.Path(os.path.join(root,dir), '_index.md')
                    indx_file.touch()
                    post = frontmatter.load(indx_file)
                    post['title'] = indx_file.parent.name.capitalize() # explanation: path = pathlib.Path('/folderA/folderB/folderC/file.md'); path.parent.name is 'folderC'
                    post['created'] = datetime.now()#.strftime("%Y-%m-%dT%H:%M:%S")
                    # NOTE: post['date'] will be added later from the add_frontmatter_date() function
                    # post['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    post['publish'] = True
                    f = open(indx_file, 'wb') # Note the 'wb'. Need to open file for binary writing, else frontmatter.dump() will not work
                    frontmatter.dump(post, f) # Note that this reformats the 'created' string
                    f.close()
                    logging.info("CREATED file %s", indx_file)

def root_to_index(destination): # moves root.md in notes/_index.md and modifies frontmatter
    indx_file = pathlib.Path(destination, '_index.md')
    shutil.move(pathlib.Path(destination, 'root.md'), indx_file)
    post = frontmatter.load(indx_file)
    post['title'] = 'Notes'
    post['cascade'] = {'type': 'docs'}
    post['menu'] = {'main': {'title': 'Notes', 'weight': '45'}}
    post['created'] = datetime.now()#.strftime("%Y-%m-%d %H:%M:%S") #After dump() the datetime.now() will be written as an unquoted datetime string in the default YAML format YYYY-MM-DD HH:MM.SS.microseconds?. If you use datetime.now.strftime() then dump() will write as string surrounded by ''. The former will be parsed by frontmatter.load() as a datetime object. The latter will be parsed as a string
    # NOTE: post['date'] will be added later from the add_frontmatter_date() function
    # post['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    post['publish'] = True
    f = open(indx_file, 'wb') # Note the 'wb'. Need to open file for binary writing, else frontmatter.dump() will not work
    frontmatter.dump(post, f)
    f.close()

def add_frontmatter_date(destination): # add 'date' frontmatter variable because Hugo needs it
    for file in destination.glob('**/*'):
        if str(file).endswith(".md"):
            post = frontmatter.load(file)
            post['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if 'updated' in post.keys():
                post['date'] = post['updated'].strftime("%Y-%m-%d %H:%M:%S")
            elif 'created' in post.keys():
                post['date'] =  post['created'].strftime("%Y-%m-%d %H:%M:%S") # Prints it to file as 'string'. When parsed back, is not datetime object, but a string, due to the '' surrounding the string.
            f = open(file, 'wb')
            frontmatter.dump(post, f)
            f.close()

def main():
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True) # Create logs/ dir if it does not exist
    logging.basicConfig(filename='logs/export-files.log', filemode='w', encoding='utf-8', level=logging.DEBUG)

    (origin_str, destination_str) = parse_args()
    origin = pathlib.Path(origin_str)
    destination = pathlib.Path(destination_str)
    logging.info("ORIGIN: %s , DESTINATION: %s", origin_str, destination_str)
    if not os.path.isdir(origin):
        print("ORIGIN folder does not exist. Aborting!")
        sys.exit(1)

    logging.info("DELETING target folder %s", destination_str)
    delete_target(destination)
    logging.info("COPYING Obsidian vault to target folder %s", destination_str)
    copy_source_to_target(origin, destination)

    logging.info("CREATING _index.md files")
    create_index_files(destination)
    root_to_index(destination)

    logging.info ("PRUNING files with publish != True")
    prune_nopublish(destination)

    logging.info("ADDING dates to frontmatter")
    add_frontmatter_date(destination)

if __name__ == "__main__":
    main()
