# obsidian-hugo-export

The scripts in this repository are used to export contents of an Obsidian vault (a bunch of markdown files and associated images or other asset files) such that they can be published with the [Hugo](https://gohugo.io/) static site generator.

These scripts are meant to be called in sequence, as exemplified by the contents of `obsidian-export.sh`.

The detailed explanations of what these scripts do and how they work is documented [here](https://sagar.se/notes/computers/hugo/digital-garden/publishing-obsidian-vault-with-hugo/). Briefly,

`export-files.py`: Copies the files in the Obsidian vault (excluding those that should not be published) to a destination folder. Generates any missing `_index.md` files that may be needed by Hugo alongwith frontmatter variables like `date`.

`process-wikilinks.py`: Finds `[[path/to/file | Optional Link Title]]` in the exported files and replaces them with Hugo `ref` links in the form of `[Optional Link Title]({{< ref "path/to/file" >}})`

`add-backlinks.py`: Adds a backlinks section to files that do have backlinks (are referred to by other files).

`copy-assets.py`: Finds images referenced in any markdown files to be published and copies them to the appropriate location for publishing with Hugo.
