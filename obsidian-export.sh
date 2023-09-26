#! /bin/sh

OBSIDIAN_VAULT=/home/sagar/Documents/notes
HUGO_SITE=/home/sagar/sagar.se

rm -rf logs/
rm -rf $HUGO_SITE/content/notes/*
python3 export-files.py $OBSIDIAN_VAULT ./notes
python3 process-wikilinks.py ./notes
python3 add-backlinks.py
cp -a notes/* $HUGO_SITE/content/notes/
cp -a $OBSIDIAN_VAULT/assets $HUGO_SITE/static/
