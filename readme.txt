Tumblr Backup will make a local backup of your Tumblr account.

To use it, just give it the name of your account:

    python tumblr_backup.py account_name

By default, it creates a new folder with post data saved in individual HTML
files and resources like images saved in appropriately named subfolders. The
alternative is to save the post data in a single CSV file, behavior which you
can specify via the command line:

    python tumblr_backup.py --csv=true account_name

It is possible to specify an alternate save directory :

    python tumblr_backup.py --save_folder=/path/to/folder account_name

Note that private accounts requiring authorization are not currently supported.

