#! /bin/sh

OBSIDIAN_VAULT=/home/sagar/Documents/notes
#HUGO_SITE=/home/sagar/sagar.se
HUGO_SITE=./tmpsite

rm -rf logs/
#rm -rf $HUGO_SITE/content/notes/* $HUGO_SITE/static/assets/*
python3 export-files.py $OBSIDIAN_VAULT $HUGO_SITE/content/notes
python3 process-wikilinks.py $HUGO_SITE/content/notes
#python3 add-backlinks.py
python3 copy-assets.py $OBSIDIAN_VAULT $HUGO_SITE/static/assets/images/
#cp -a notes/* $HUGO_SITE/content/notes/
#cp -a $OBSIDIAN_VAULT/assets $HUGO_SITE/static/
