#! /bin/sh

OBSIDIAN_VAULT=/home/sagar/Documents/notes
HUGO_SITE=/home/sagar/sagar.se
#HUGO_SITE=/home/sagar/experiments/obsidian-hugo-export/tmpsite

rm -rf logs/
python3 export-files.py $OBSIDIAN_VAULT $HUGO_SITE/content/notes
python3 process-wikilinks.py $HUGO_SITE/content/notes
python3 add-backlinks.py $HUGO_SITE/content/notes
python3 copy-assets.py $OBSIDIAN_VAULT $HUGO_SITE/static/assets/images/
