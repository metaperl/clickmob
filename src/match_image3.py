__author__ = 'anicca'


import cv2

def showk(img, kpts):
    for k in kpts:
        print 'key'
        x, y = k.pt
        x = int(x)
        y = int(y)
        cv2.rectangle(img,(x,y), (x+2,y+2),(0,0,255),2)

    cv2.imshow("Result",img)
    cv2.waitKey(0);


def similarity_test(img1_filename, img2_filename):
    img1 = cv2.imread(img1_filename, cv2.CV_LOAD_IMAGE_GRAYSCALE)          # queryImage
    img2 = cv2.imread(img2_filename, cv2.CV_LOAD_IMAGE_GRAYSCALE) # trainImage

    fd = cv2.FeatureDetector_create('ORB')
    kpts = fd.detect(img1)
    showk(img1,kpts)
    print kpts
    kpts2 = fd.detect(img2)
    showk(img2,kpts2)

    # Now that we have the keypoints we must describe these points (x,y)
    # and match them.
    descriptor = cv2.DescriptorExtractor_create("BRIEF")
    matcher = cv2.DescriptorMatcher_create("BruteForce-Hamming")


    # descriptors (we must describe the points in some way)
    k1, d1 = descriptor.compute(img1, kpts)
    k2, d2 = descriptor.compute(img2, kpts2)

    # match the keypoints
    matches = matcher.match(d1, d2)

    # similarity
    print '#matches:', len(matches)


if __name__ == '__main__':
    filenames=['IMG-0.png', 'IMG-1.png', 'IMG-2.png', 'IMG-3.png']
    for filename in filenames:
        print filename
        similarity_test(filename, 'image_to_match.png')