__author__ = 'anicca'


import cv2

from PIL import Image

def avhash(im):
    if not isinstance(im, Image.Image):
        im = Image.open(im)
    im = im.resize((8, 8), Image.ANTIALIAS).convert('L')
    avg = reduce(lambda x, y: x + y, im.getdata()) / 64.
    return reduce(lambda x, (y, z): x | (z << y),
                  enumerate(map(lambda i: 0 if i < avg else 1, im.getdata())),
                  0)

def hamming(h1, h2):
    h, d = 0, h1 ^ h2
    while d:
        h += 1
        d &= d - 1
    return h

def distance(img1, img2):
    hash1 = avhash(img1)
    hash2 = avhash(img2)
    return hamming(hash1, hash2)


def closest(query, filenames):
    trial = list()
    for filename in filenames:
        _distance=distance(filename, query)
        print filename
        print _distance
        trial.append(dict(filename=filename, distance=_distance))

    matches = sorted(trial, key = lambda x:x['distance'])
    return matches[0]['filename']


if __name__ == '__main__':
    filenames=['IMG-0.png', 'IMG-1.png', 'IMG-2.png', 'IMG-3.png']
    query = 'image_to_match.png'
    print closest(query, filenames)
