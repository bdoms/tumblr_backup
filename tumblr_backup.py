# standard Python library imports
import os
import sys
import urllib2
import csv
import codecs
import logging

# extra required packages
from bs4 import BeautifulSoup

# Tumblr specific constants
TUMBLR_URL = "/api/read"

# configuration variables
ENCODING = "utf-8"

# most filesystems have a limit of 255 bytes per name but we also need room for a '.html' extension
NAME_MAX_BYTES = 250


def unescape(s):
    """ replace Tumblr's escaped characters with ones that make sense for saving in an HTML file """

    if s is None:
        return ""

    # html entities
    s = s.replace("&#13;", "\r")

    # standard html
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&") # this has to be last

    return s


# based on http://stackoverflow.com/a/13738452
def utf8_lead_byte(b):
    """ a utf-8 intermediate byte starts with the bits 10xxxxxx """
    return (ord(b) & 0xC0) != 0x80


def byte_truncate(text):
    """ if text[max_bytes] is not a lead byte, back up until one is found and truncate before that character """
    s = text.encode(ENCODING)
    if len(s) <= NAME_MAX_BYTES:
        return s

    if ENCODING == "utf-8":
        lead_byte = utf8_lead_byte
    else:
        raise NotImplementedError()

    i = NAME_MAX_BYTES
    while i > 0 and not lead_byte(s[i]):
        i -= 1
    return s[:i]


def savePost(post, save_folder, header="", use_csv=False, save_file=None):
    """ saves an individual post and any resources for it locally """

    if use_csv:
        assert save_file, "Must specify a file to save CSV data to."

    slug = post["url-with-slug"].rpartition("/")[2]
    date_gmt = post["date-gmt"]

    if use_csv:
        # only append here to preserve other posts
        # must be opened in binary mode to avoid line break bugs on Windows
        f = open(save_file, "ab")
        writer = csv.writer(f)
        row = [slug, date_gmt]
    else:
        slug = byte_truncate(slug)
        file_name = os.path.join(save_folder, slug + ".html")
        f = codecs.open(file_name, "w", encoding=ENCODING)

        # header info which is the same for all posts
        f.write(header)
        f.write('<p class="timestamp">' + date_gmt + '</p>')

    if post["type"] == "regular":
        title = ""
        title_tag = post.find("regular-title")
        if title_tag:
            title = unescape(title_tag.string)
        body = ""
        body_tag = post.find("regular-body")
        if body_tag:
            body = unescape(body_tag.string)

        if use_csv:
            row.append(title)
            row.append(body)
        else:
            if title:
                f.write("<h3>" + title + "</h3>")
            if body:
                f.write(body)
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')

    if post["type"] == "photo":
        caption = ""
        caption_tag = post.find("photo-caption")
        if caption_tag:
            caption = unescape(caption_tag.string)
        image_url = post.find("photo-url", {"max-width": "1280"}).string

        image_filename = image_url.rpartition("/")[2].encode(ENCODING)
        image_folder = os.path.join(save_folder, "images")
        if not os.path.exists(image_folder):
            os.mkdir(image_folder)
        local_image_path = os.path.join(image_folder, image_filename)

        if not os.path.exists(local_image_path):
            # only download images if they don't already exist
            print "Downloading a photo. This may take a moment."
            try:
                image_response = urllib2.urlopen(image_url)
                image_file = open(local_image_path, "wb")
                image_file.write(image_response.read())
                image_file.close()
            except urllib2.HTTPError, e:
                logging.warning('HTTPError = ' + str(e.code))
            except urllib2.URLError, e:
                logging.warning('URLError = ' + str(e.reason))
            except httplib.HTTPException, e:
                logging.warning('HTTPException')
            except Exception:
                import traceback
                logging.warning('generic exception: ' + traceback.format_exc())

        if use_csv:
            row.append(caption)
            row.append('images/' + image_filename)
        else:
            f.write(caption + '<img alt="' + caption.replace('"', '&quot;') + '" src="images/' + image_filename + '" />')
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')

    if post["type"] == "quote":
        quote = ""
        quote_tag = post.find("quote-text")
        if quote_tag:
            quote = unescape(quote_tag.string)
        source = ""
        source_tag = post.find("quote-source")
        if source_tag:
            source = unescape(source_tag.string)

        if use_csv:
            row.append(quote)
            row.append(source)
        else:
            if quote:
                f.write("<blockquote>" + quote + "</blockquote>")
            if source:
                f.write('<p class="quotesource">' + source + '</p>')
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')

    if post["type"] == "link":
        link_text = ""
        text_tag = post.find("link-text")
        if text_tag:
            link_text = unescape(text_tag.string)
        link_url = ""
        url_tag = post.find("link-url")
        if url_tag:
            link_url = unescape(url_tag.string)
        link_desc = ""
        desc_tag = post.find("link-description")
        if desc_tag:
            link_desc = unescape(desc_tag.string)

        if use_csv:
            row.append(link_text)
            row.append(link_url)
            row.append(link_desc)
        else:
            if link_url or link_text:
                f.write('<h3>')
                if link_url:
                    f.write('<a href="' + link_url + '">')
                if link_text:
                    f.write(link_text)
                if link_url:
                    f.write('</a>')
                f.write('</h3>')
            if link_desc:
                f.write('<p class="linkdescription">' + link_desc + '</p>')
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')
        row.append('')

    tags = post.findAll("tag")
    if tags:
        if use_csv:
            tags_string = [unescape(tag.string) for tag in tags]
            tags_joined = "|".join(tags_string)
            row.append(tags_joined)
        else:
            f.write('<h4>Tagged</h4>')
            f.write('<ul>')
            for tag in tags:
                f.write('<li>' + unescape(tag.string) + '</li>')
            f.write('</ul>')
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')

    if use_csv:
        encoded_row = [cell.encode(ENCODING) for cell in row]
        writer.writerow(encoded_row)
    else:
        # common footer
        f.write("</body></html>")
    f.close()


def backup(account, use_csv=False, save_folder=None, start_post = 0):
    """ make an HTML file for each post or a single CSV file for all posts on a public Tumblr blog account """

    if use_csv:
        print "CSV mode activated."
        print "Data will be saved to " + account + "/" + account + ".csv"

    print "Getting basic information."

    # make sure there's a folder to save in
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    # start by calling the API with just a single post
    url = "http://" + account + TUMBLR_URL + "?num=1"
    response = urllib2.urlopen(url)
    soup = BeautifulSoup(response.read(), features="xml")

    # if it's a backup to CSV then make sure that we have a file to use
    if use_csv:
        save_file = os.path.join(save_folder, account + ".csv")
        # add the header row
        f = open(save_file, "w") # erases any existing data
        f.write("Slug,Date (GMT),Regular Title,Regular Body,Photo Caption,Photo URL,Quote Text,Quote Source,Link Text,Link URL,Link Description,Tags\r\n") # 12 columns
        f.close()
    else:
        # collect all the meta information
        tumblelog = soup.find("tumblelog")
        title = tumblelog["title"]
        description = tumblelog.string

        # use it to create a generic header for all posts
        header = '<html><meta http-equiv="content-type" content="text/html; charset=' + ENCODING + '"/>'
        header += "<head><title>" + title + "</title></head><body>"
        header += "<h1>" + title + "</h1><h2>" + unescape(description) + "</h2>"

    # then find the total number of posts
    posts_tag = soup.find("posts")
    total_posts = int(posts_tag["total"])

    # then get the XML files from the API, which we can only do with a max of 50 posts at once
    for i in range(start_post, total_posts, 50):
        # find the upper bound
        j = i + 49
        if j > total_posts:
            j = total_posts

        print "Getting posts " + str(i) + " to " + str(j) + "."

        url = "http://" + account + TUMBLR_URL + "?num=50&start=" + str(i)
        response = urllib2.urlopen(url)
        soup = BeautifulSoup(response.read(), features="xml")

        posts = soup.findAll("post")
        for post in posts:
            if use_csv:
                savePost(post, save_folder, use_csv=use_csv, save_file=save_file)
            else:
                savePost(post, save_folder, header=header)

    print "Backup Complete"


if __name__ == "__main__":

    account = None
    use_csv = False
    save_folder = None
    start_post = 0
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                option, value = arg[2:].split("=")
                if option == "csv" and value == "true":
                    use_csv = True
                if option == "save_folder":
                    save_folder = value
                if option == "start_post":
                    start_post = int(value)
            else:
                account = arg

    assert account, "Invalid command line arguments. Please supply the name of your Tumblr account."

    if (save_folder == None):
        save_folder = os.path.join(os.getcwd(), account)

    backup(account, use_csv, save_folder, start_post)
