from StringIO import StringIO
from PIL import Image, ImageDraw

from bountyfunding.core.data import retrieve_all_sponsorships


def create_image(issue):
    sponsorships = retrieve_all_sponsorships(issue.issue_id)
    bounty = sum(s.amount for s in sponsorships)
    #text = u"bounty: %s\u20ac" % bounty
    text = u"bounty: %s" % bounty

    image = Image.new("RGBA", (100,20), (255,255,255,255))
    draw = ImageDraw.Draw(image)
    draw.text((3,3), text, fill=(0,0,0,255))
    image_io = StringIO()
    image.save(image_io, 'PNG')
    image_io.seek(0)
    return image_io

