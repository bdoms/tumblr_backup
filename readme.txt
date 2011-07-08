Tumblr Backup will make a local backup of your Tumblr website.

To use it, just give it the URL of your Tumblr website:

    python tumblr_backup.py website_url

By default, it creates a new folder with post data saved in individual HTML
files and resources like images saved in appropriately named subfolders. The
alternative is to save the post data in a single CSV file, behavior which you
can specify via the command line:

    python tumblr_backup.py --csv=true website_url 

It is possible to specify an alternate save directory :

    python tumblr_backup.py --save_folder=/path/to/folder website_url

Note that private accounts requiring authorization are not currently supported.

