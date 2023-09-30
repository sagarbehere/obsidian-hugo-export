import pathlib
import sqlite3
import logging
import argparse
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', help="Location of notes folder in Hugo. Typically, something like $HUGO_SITE/content/notes", default="./notes")
    args = parser.parse_args()
    return (args.destination)

def add_backlinks(dbconn, destination):
	dbcursor = dbconn.cursor()
	dbcursor.execute('''SELECT DISTINCT "to" FROM links''')
	file_list = dbcursor.fetchall()
	for file in file_list: # file list is [(/notes/path/to/file, ), (/notes/path/to/another/file, )]
		if file[0].endswith(".md"):
			logging.info('Processing file %s', str(destination.parent)+file[0]) #destination already ends with /notes and file already begins with /notes. So we use destination.parent to remove the /notes from the end of destination
			dbcursor.execute('''SELECT DISTINCT "from", "from_title" FROM links WHERE "to" = ?''', (file[0], ))
			backlinks_list = dbcursor.fetchall()
			# print (file[0], backlinks_list) # TODO Replace with logging.info() call
			newfiledata = ''
			with open(pathlib.Path(destination.parent, file[0].strip("/")), 'r') as f: # Need to remove leading / else pathlib.Path will ignore destination. pathlib.Path() ignores all arguments preceding an argument which contains absolute paths
				tuples = f.read().rpartition("## Backlinks") # [0] before delimiter [1]delimiter [2] after delimiter OR entire string if no delimiter
				if tuples[0]:
					filedata = tuples[0].strip()
				else:
				    filedata = tuples[2].strip()
				filedata +=  "\n\n## Backlinks\n"
				for backlink in backlinks_list:
					filedata += "\n- ["+backlink[1]+"]({{< ref \""+backlink[0]+"\" >}})"
					logging.info("Adding backlink to %s", backlink[0])
				newfiledata = filedata
			# print (newfiledata)
			with open(pathlib.Path(destination.parent, file[0].strip("/")), 'w') as f: # Need to remove leading / else pathlib.Path will ignore destination. pathlib.Path() ignores all arguments preceding an argument which contains absolute paths
				f.write(newfiledata)
				f.close()

def main():
	logging.basicConfig(filename='logs/add-backlinks.log', filemode='w', encoding='utf-8', level=logging.DEBUG)
	logging.info('STARTING addition of backinks')

	destination_str = parse_args()
	destination = pathlib.Path(destination_str)
	logging.info("DESTINATION: %s", destination_str)
	if not os.path.isdir(destination):
		print("DESTINATION folder does not exist. Aborting!")
		sys.exit(1)

	sqlitedbfilename = 'logs/relations.db' #TODO: Avoid hardcoded logs folder
	dbconn = sqlite3.connect(sqlitedbfilename) #TODO: Error checking
	
	add_backlinks(dbconn, destination)

	dbconn.close()		
	logging.info('FINISHED addition of backlinks')
	
if __name__ == "__main__":
    main()
