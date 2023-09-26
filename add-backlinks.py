import pathlib
import sqlite3
import logging

def add_backlinks(dbconn):
	dbcursor = dbconn.cursor()
	dbcursor.execute('''SELECT DISTINCT "to" FROM links''')
	file_list = dbcursor.fetchall()
	for file in file_list: # file list is [(path/to/file, ), (path/to/another/file, )]
		if file[0].endswith(".md"):
			logging.info('Processing file %s', file[0])
			dbcursor.execute('''SELECT DISTINCT "from", "from_title" FROM links WHERE "to" = ?''', (file[0], ))
			backlinks_list = dbcursor.fetchall()
			# print (file[0], backlinks_list) # TODO Replace with logging.info() call
			newfiledata = ''
			with open(pathlib.Path(file[0]), 'r') as f:
				tuples = f.read().rpartition("## Backlinks") # [0] before delimiter [1]delimiter [2] after delimiter OR entire string if no delimiter
				if tuples[0]:
					filedata = tuples[0].strip()
				else:
				    filedata = tuples[2].strip()
				filedata +=  "\n\n## Backlinks\n"
				for backlink in backlinks_list:
					filedata += "\n- ["+backlink[1]+"]({{< ref \""+"/"+backlink[0]+"\" >}})"
					logging.info("Adding backlink to %s", backlink[0])
				newfiledata = filedata
			# print (newfiledata)
			with open(pathlib.Path(file[0]), 'w') as f:
				f.write(newfiledata)
				f.close()

def main():
	logging.basicConfig(filename='logs/add-backlinks.log', filemode='w', encoding='utf-8', level=logging.DEBUG)
	logging.info('STARTING addition of backinks')
	sqlitedbfilename = 'logs/relations.db'
	dbconn = sqlite3.connect(sqlitedbfilename)
	
	add_backlinks(dbconn)

	dbconn.close()		
	logging.info('FINISHED addition of backlinks')
	
if __name__ == "__main__":
    main()
