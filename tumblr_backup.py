
# standard Python library imports
import os
import sys
import urllib2
import csv

# add BeautifulSoup submobule to path
lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beautifulsoup')
sys.path.append(lib_dir)

# extra required packages (StoneSoup is the version for XML)
from BeautifulSoup import BeautifulStoneSoup

# Tumblr specific constants
TUMBLR_URL = ".tumblr.com/api/read"


def unescape(s):
    """ replace Tumblr's escaped characters with ones that make sense for saving in an HTML file """

    # special character corrections
    s = s.replace(u"\xa0", "&amp;nbsp;")
    s = s.replace(u"\xe1", "&amp;aacute;")

    # standard html
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&") # this has to be last

    return s


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
        file_name = os.path.join(save_folder, slug + ".html")
        f = open(file_name, "w")

        # header info which is the same for all posts
        f.write(header)
        f.write("<p>" + date_gmt + "</p>")

    if post["type"] == "regular":
        title = unescape(post.find("regular-title").string)
        body = unescape(post.find("regular-body").string)

        if use_csv:
            row.append(title)
            row.append(body)
        else:
            f.write("<h3>" + title + "</h3>" + body)
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')

    if post["type"] == "photo":
        caption = unescape(post.find("photo-caption").string)
        image_url = post.find("photo-url", {"max-width": "1280"}).string

        image_filename = image_url.rpartition("/")[2] + ".jpg" # the 1280 size doesn't end with an extension strangely
        image_folder = os.path.join(save_folder, "images")
        if not os.path.exists(image_folder):
            os.mkdir(image_folder)
        local_image_path = os.path.join(image_folder, image_filename)

        if not os.path.exists(local_image_path):
            # only download images if they don't already exist
            print "Downloading a photo. This may take a moment."
            image_response = urllib2.urlopen(image_url)
            image_file = open(local_image_path, "wb")
            image_file.write(image_response.read())
            image_file.close()

        if use_csv:
            row.append(caption)
            row.append('images/' + image_filename)
        else:
            f.write(caption + '<img alt="' + caption + '" src="images/' + image_filename + '" />')
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')

    if post["type"] == "quote":
        quote = unescape(post.find("quote-text").string)
        source = unescape(post.find("quote-source").string)

        if use_csv:
            row.append(quote)
            row.append(source)
        else:
            f.write("<blockquote>" + quote + "</blockquote><p>" + source + "</p>")
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')

    if post["type"] == "link":
        link_text = unescape(post.find("link-text").string)
        link_url = unescape(post.find("link-url").string)
        link_desc = unescape(post.find("link-description").string)

        if use_csv:
            row.append(link_text)
            row.append(link_url)
            row.append(link_desc)
        else:
            f.write('<h3><a href="' + link_url + '">' + link_text + '</a></h3><p>' + link_desc + '</p>')
    elif use_csv:
        # add in blank columns to maintain the correct number
        row.append('')
        row.append('')
        row.append('')

    tags = post.findAll("tags")
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
        writer.writerow(row)
    else:
        # common footer
        f.write("</body></html>")
    f.close()


def backup(account, use_csv=False):
    """ make an HTML file for each post or a single CSV file for all posts on a public Tumblr blog account """

    if use_csv:
        print "CSV mode activated."
        print "Data will be saved to " + account + "/" + account + ".csv"

    print "Getting basic information."

    # make sure there's a folder to save in
    save_folder = os.path.join(os.getcwd(), account)
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    # start by calling the API with just a single post
    url = "http://" + account + TUMBLR_URL + "?num=1"
    response = urllib2.urlopen(url)
    soup = BeautifulStoneSoup(response.read())

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
        header = "<html><head><title>" + title + "</title></head><body>"
        header += "<h1>" + title + "</h1><h2>" + unescape(description) + "</h2>"

    # then find the total number of posts
    posts_tag = soup.find("posts")
    total_posts = int(posts_tag["total"])

    # then get the XML files from the API, which we can only do with a max of 50 posts at once
    for i in range(0, total_posts, 50):
        # find the upper bound
        j = i + 49
        if j > total_posts:
            j = total_posts

        print "Getting posts " + str(i) + " to " + str(j) + "."

        url = "http://" + account + TUMBLR_URL + "?num=50&start=" + str(i)
        response = urllib2.urlopen(url)
        soup = BeautifulStoneSoup(response.read())

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
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                option, value = arg[2:].split("=")
                if option == "csv" and value == "true":
                    use_csv = True
            else:
                account = arg

    assert account, "Invalid command line arguments. Please supply the name of your Tumblr account."

    backup(account, use_csv)

