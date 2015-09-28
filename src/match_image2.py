__author__ = 'anicca'


import cv2
from skimage.measure import structural_similarity as ssim


def similarity_test(img1_filename, img2_filename):
    img1 = cv2.imread(img1_filename, 0)          # queryImage
    img2 = cv2.imread(img2_filename, 0) # trainImage

    print "SSIM={0}".format(ssim(img1, img2))




if __name__ == '__main__':
    filenames=['IMG-0.png', 'IMG-1.png', 'IMG-2.png', 'IMG-3.png']
    for filename in filenames:
        print filename
        similarity_test(filename, 'image_to_match.png')