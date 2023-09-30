# This script loads each file, searches for a wikilink i.e. [[path/to/link | alias]] and replaces it with [alias]({{< ref "path/to/link >}})
# Because we don't want to process wikilinks inside a fenced code block (text with ``` before and after it), the script does something truly horrible
#     - It first uses a regex to detect all fenced code blocks and mangles any [[wikilinks]] to -[[wikilinks]] so that the wikilinks regex will not match
#     - Then the wikilinks processing regex is run
#     - Then the wikilinks inside the fenced code blocks are unmangled i.e. -[[wikilink]] becomes [[wikilink]] again. Phew!
# NOTE: This script will not work for wikilinks that do not have whitespace just before them. The script will also mistakenly process wikilinks in `inline code`

import regex as re
import os
import io
import pathlib
import sqlite3
import frontmatter
import logging
import argparse

wikilinks = re.compile(r"\s\[\[(([^\]|]|\](?=[^\]]))*)(\|(([^\]]|\](?=[^\]]))*))?\]\]")
codeblocks = re.compile(r"```\w*[^`]+```")
# destdir = pathlib.Path("notes/")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', help="Location of notes folder in Hugo. Typically, something like $HUGO_SITE/content/notes", default="./notes")
    args = parser.parse_args()
    return (args.destination)

def mangle_codeblocks(match):
	return match.group().replace("[[", "-[[")

def unmangle_codeblocks(match):
	return match.group().replace("-[[", "[[")

def get_post_title(file):
	post = frontmatter.load(file)
	title = post['title']
	if title:
		return title
	else:
		return 'Unknown title of'+str(file)

def process_wikilink(match, dbconn, destination, file):
	dbcursor = dbconn.cursor()
	
	label = match.group(4)
	url = match.group(1)
	if label == None:
		label = url
	else:
		label = label.strip()

	title = get_post_title(file)
	# print("From: ", str(file), "From title: ", title, "To :", str(destination)+"/"+url+".md")
	dbcursor.execute('''INSERT INTO links ("from", "from_title", "to") VALUES (?, ?, ?)''', ("/"+str(file.relative_to(destination.parent)), title, "/"+str(destination.name)+"/"+url+".md"))
	dbconn.commit()
	if url.endswith("_index"): # In Hugo, an _index.md file can only be referenced by its containing folder. So if any urls end with _index, that trailing _index needs to be removed
		url = url.rpartition("/")[0] #split the url at the last occurrence of "/" and return a 3-tuple containing the part before the separator i.e. [0], the separator itself i.e[1], and the part after the separator i.e. [2]
	newlink = " ["+label+"]({{< ref \""+"/"+destination.name+"/"+url+"\" >}})"

	logging.info("File %s: Found %s and replacing it with %s", "/"+str(file.relative_to(destination.parent)), match.group(0), newlink)
	return newlink

def main():
	logging.basicConfig(filename='logs/process-wikilinks.log', filemode='w', encoding='utf-8', level=logging.DEBUG)
	logging.info('STARTING processing of wikilinks')

	destination_str = parse_args()
	destination = pathlib.Path(destination_str)
	logging.info("DESTINATION: %s", destination_str)
	if not os.path.isdir(destination):
		print("DESTINATION folder does not exist. Aborting!")
		sys.exit(1)

	sqlitedbfilename = 'logs/relations.db' #TODO: Avoid hardcoded logs directory here
	dbconn = sqlite3.connect(sqlitedbfilename) #TODO: Error checking on this function

	dbconn.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT, "from" TEXT NOT NULL, from_title TEXT, "to" TEXT NOT NULL, to_title TEXT)''')
	dbconn.execute('''DELETE FROM links''')
	dbconn.execute('''DELETE FROM SQLITE_SEQUENCE WHERE name="links"''') # reset the autoincrement id
	dbconn.commit()
	
	for file in destination.glob('**/*'):
		if str(file).endswith(".md"):
			newfiledata = ''
			with open(file, 'r') as f:
				tuples = f.read().rpartition("## Backlinks") # [0] before delimiter [1]delimiter [2] after delimiter OR entire string if no delimiter
				if tuples[0]:
					filedata = tuples[0].strip()
				else:
					filedata = tuples[2].strip()
				# Seek out all fenced codeblocks in the file and if they contain a wikilink, mangle it by replacing all [[ with -[[ so that the wikilink detector regex will not match it. This will prevent the processing of wikilinks inside fenced code blocks.
				mangledfiledata = codeblocks.sub(lambda x: mangle_codeblocks(x), filedata)
				processedlinksdata = wikilinks.sub(lambda x: process_wikilink(x, dbconn, destination, file), mangledfiledata)
				# Now that wikilinks are processed, unmagle any wikilinks inside fenced code blocks
				newfiledata = codeblocks.sub(lambda x: unmangle_codeblocks(x), processedlinksdata)
				if tuples[0]: # If the file did contain a ## Backlinks section, add it back
					newfiledata += "\n\n"+tuples[1] + tuples[2]
			with open(file, 'w') as f:
				f.write(newfiledata)
				f.close()

	dbconn.close()
	logging.info('FINISHED processing of wikilinks')

if __name__ == "__main__":
    main()
