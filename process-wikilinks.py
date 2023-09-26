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

wikilinks = re.compile(r"\s\[\[(([^\]|]|\](?=[^\]]))*)(\|(([^\]]|\](?=[^\]]))*))?\]\]")
codeblocks = re.compile(r"```\w*[^`]+```")
destdir = pathlib.Path("notes/") 

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

def process_wikilink(match, dbconn, file):
	dbcursor = dbconn.cursor()
	
	label = match.group(4)
	url = match.group(1)
	if label == None:
		label = url
	else:
		label = label.strip()

	title = get_post_title(file)
	# print("From: ", str(file), "From title: ", title, "To :", str(destdir)+"/"+url+".md")
	dbcursor.execute('''INSERT INTO links ("from", "from_title", "to") VALUES (?, ?, ?)''', (str(file), title, str(destdir)+"/"+url+".md"))
	dbconn.commit()
	newlink = " ["+label+"]({{< ref \""+"/"+str(destdir)+"/"+url+"\" >}})"

	logging.info("File %s: Found %s and replacing it with %s", str(file), match.group(0), newlink)
	return newlink

def main():
	logging.basicConfig(filename='logs/process-wikilinks.log', filemode='w', encoding='utf-8', level=logging.DEBUG)
	logging.info('STARTING processing of wikilinks')
	sqlitedbfilename = 'logs/relations.db'
	dbconn = sqlite3.connect(sqlitedbfilename)

	dbconn.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER UNIQUE NOT NULL PRIMARY KEY AUTOINCREMENT, "from" TEXT NOT NULL, from_title TEXT, "to" TEXT NOT NULL, to_title TEXT)''')
	dbconn.execute('''DELETE FROM links''')
	dbconn.execute('''DELETE FROM SQLITE_SEQUENCE WHERE name="links"''') # reset the autoincrement id
	dbconn.commit()
	
	for file in destdir.glob('**/*'):
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
				processedlinksdata = wikilinks.sub(lambda x: process_wikilink(x, dbconn, file), mangledfiledata)
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
