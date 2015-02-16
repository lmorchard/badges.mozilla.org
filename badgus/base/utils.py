import logging
import re
from time import time, gmtime, strftime
import os.path
from os.path import dirname
from urlparse import urljoin
from cStringIO import StringIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

try:
    from PIL import Image
except ImportError:
    import Image


log = logging.getLogger('funfactory')


# Set up a file system for badge uploads that can be kept separate from the
# rest of /media if necessary. Lots of hackery to ensure sensible defaults.
UPLOADS_ROOT = getattr(settings, 'UPLOADS_ROOT',
    os.path.join(getattr(settings, 'MEDIA_ROOT', 'media/'), 'uploads'))
UPLOADS_URL = getattr(settings, 'UPLOADS_URL',
    urljoin(getattr(settings, 'MEDIA_URL', '/media/'), 'uploads/'))
UPLOADS_FS = FileSystemStorage(location=UPLOADS_ROOT,
                               base_url=UPLOADS_URL)


def make_random_code(length=7):
    """Generare a random code, using a set of alphanumeric characters that
    attempts to avoid ambiguously similar shapes."""
    s = '3479acefhjkmnprtuvwxy'
    return ''.join([random.choice(s) for x in range(length)])


def show_unicode(obj):
    return unicode(obj)
show_unicode.short_description = "Display"


def show_image(obj):
    if not obj.image:
        return 'None'
    img_url = "%s%s" % (UPLOADS_URL, obj.image)
    return ('<a href="%s" target="_new"><img src="%s" width="48" height="48" /></a>' % 
        (img_url, img_url))

show_image.allow_tags = True
show_image.short_description = "Image"


# Taken from http://stackoverflow.com/a/4019144
def slugify(txt):
    """A custom version of slugify that retains non-ascii characters. The
    purpose of this function in the application is to make URLs more readable
    in a browser, so there are some added heuristics to retain as much of the
    title meaning as possible while excluding characters that are troublesome
    to read in URLs. For example, question marks will be seen in the browser
    URL as %3F and are thereful unreadable. Although non-ascii characters will
    also be hex-encoded in the raw URL, most browsers will display them as
    human-readable glyphs in the address bar -- those should be kept in the
    slug."""
    # remove trailing whitespace
    txt = txt.strip()
    # remove spaces before and after dashes
    txt = re.sub('\s*-\s*', '-', txt, re.UNICODE)
    # replace remaining spaces with dashes
    txt = re.sub('[\s/]', '-', txt, re.UNICODE)
    # replace colons between numbers with dashes
    txt = re.sub('(\d):(\d)', r'\1-\2', txt, re.UNICODE)
    # replace double quotes with single quotes
    txt = re.sub('"', "'", txt, re.UNICODE)
    # remove some characters altogether
    txt = re.sub(r'[?,:!@#~`+=$%^&\\*()\[\]{}<>]', '', txt, re.UNICODE)
    return txt


def absolutify(url):
    """Takes a URL and prepends the SITE_URL"""
    site_url = getattr(settings, 'SITE_URL', False)

    # If we don't define it explicitly
    if not site_url:
        protocol = settings.PROTOCOL
        hostname = settings.DOMAIN
        port = settings.PORT
        if (protocol, port) in (('https://', 443), ('http://', 80)):
            site_url = ''.join(map(str, (protocol, hostname)))
        else:
            site_url = ''.join(map(str, (protocol, hostname, ':', port)))

    return site_url + url


def mk_upload_to(field_fn):
    """upload_to builder for file upload fields"""
    def upload_to(instance, filename):
        base, slug = instance.get_upload_meta()
        time_now = int(time())
        return '%(base)s/%(slug)s/%(time_now)s_%(field_fn)s' % dict(
            time_now=time_now, slug=slug, base=base, field_fn=field_fn)
    return upload_to


def scale_image(img_upload, img_max_size):
    """Crop and scale an image file."""
    try:
        img = Image.open(img_upload)
    except IOError:
        return None

    src_width, src_height = img.size
    src_ratio = float(src_width) / float(src_height)
    dst_width, dst_height = img_max_size
    dst_ratio = float(dst_width) / float(dst_height)

    if dst_ratio < src_ratio:
        crop_height = src_height
        crop_width = crop_height * dst_ratio
        x_offset = int(float(src_width - crop_width) / 2)
        y_offset = 0
    else:
        crop_width = src_width
        crop_height = crop_width / dst_ratio
        x_offset = 0
        y_offset = int(float(src_height - crop_height) / 2)

    img = img.crop((x_offset, y_offset,
        x_offset + int(crop_width), y_offset + int(crop_height)))
    img = img.resize((dst_width, dst_height), Image.ANTIALIAS)

    if img.mode != "RGB":
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "PNG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)
