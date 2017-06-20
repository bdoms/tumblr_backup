Copyright &copy; 2009, [Brendan Doms](http://www.bdoms.com/)  
Licensed under the [MIT license](http://www.opensource.org/licenses/MIT)


# Tumblr Backup

Tumblr Backup is a tool for making a local backup of your Tumblr account.


## Setup

There is one dependency: version 4 of [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/).
If you already have it installed globally then you can grab the single `.py` file and it should work.

Otherwise, install via pip:

```bash
pip install -r requirements.txt
```

### Parsers

This script is capable of using the default parser included with Python, `html.parser`.
However, it will use the faster `lxml` libary if it can be imported.
See [the BeautifulSoup docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser)
for details and the pros and cons of each.


## Use

To backup your account, just include the URL of your Tumblr website:

```bash
python tumblr_backup.py example.tumblr.com
```

If you use a custom domain, then that will also work:

```bash
python tumblr_backup.py www.example.com
```

By default, a new folder with post data saved in individual HTML files will be created,
and resources like images will be saved in appropriately named subfolders.
The alternative is to save the post data in a single CSV file,
behavior which you can specify via the command line option `csv` like so:

```bash
python tumblr_backup.py --csv=true example.tumblr.com
```

You can also specify a different directory to save to with the command line option `save_folder`:

```bash
python tumblr_backup.py --save_folder=/path/to/folder example.tumblr.com
```

Specify the post number to start from (useful with bad internet connection to continue from the last posts group):
```bash
python tumblr_backup.py --start_post=N example.tumblr.com
```


## Supported Post Types

Tumblr has a lot of different types of posts. The ones currently supported by Tumblr Backup are:

 * Regular
 * Photo
 * Quote
 * Link


## Tags

Tumblr allows you to add "tags" to posts. Tumblr Backup supports tags on any post type by simply
adding a list of all the tags for a post to the bottom of the page if in HTML mode,
or as its own pipe ( | ) separated list if in CSV mode.


## Notes

Private accounts requiring authentication are not currently supported.

The default encoding is UTF-8. If you wish to change this, you can simply modify or override the
global `ENCODING` variable.
