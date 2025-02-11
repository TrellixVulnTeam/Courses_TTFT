## CSC320 Winter 2019 
## Assignment 2
## (c) Kyros Kutulakos
##
## DISTRIBUTION OF THIS CODE ANY FORM (ELECTRONIC OR OTHERWISE,
## AS-IS, MODIFIED OR IN PART), WITHOUT PRIOR WRITTEN AUTHORIZATION 
## BY THE INSTRUCTOR IS STRICTLY PROHIBITED. VIOLATION OF THIS 
## POLICY WILL BE CONSIDERED AN ACT OF ACADEMIC DISHONESTY

##
## DO NOT MODIFY THIS FILE ANYWHERE EXCEPT WHERE INDICATED
##

import numpy as np
import cv2 as cv

# File psi.py define the psi class. You will need to 
# take a close look at the methods provided in this class
# as they will be needed for your implementation
import psi        

# File copyutils.py contains a set of utility functions
# for copying into an array the image pixels contained in
# a patch. These utilities may make your code a lot simpler
# to write, without having to loop over individual image pixels, etc.
import copyutils

#########################################
## PLACE YOUR CODE BETWEEN THESE LINES ##
#########################################

# If you need to import any additional packages
# place them here. Note that the reference 
# implementation does not use any such packages

#########################################

def normalize2d(l):
    assert(len(l) == 2)
    norm = np.linalg.norm(l)
    if norm == 0:
        return 0, 0
    else:
        return l[0]/norm, l[1]/norm


#########################################
#
# Computing the Patch Confidence C(p)
#
# Input arguments: 
#    psiHatP: 
#         A member of the PSI class that defines the
#         patch. See file inpainting/psi.py for details
#         on the various methods this class contains.
#         In particular, the class provides a method for
#         accessing the coordinates of the patch center, etc
#    filledImage:
#         An OpenCV image of type uint8 that contains a value of 255
#         for every pixel in image I whose color is known (ie. either
#         a pixel that was not masked initially or a pixel that has
#         already been inpainted), and 0 for all other pixels
#    confidenceImage:
#         An OpenCV image of type uint8 that contains a confidence 
#         value for every pixel in image I whose color is already known.
#         Instead of storing confidences as floats in the range [0,1], 
#         you should assume confidences are represented as variables of type 
#         uint8, taking values between 0 and 255.
#
# Return value:
#         A scalar containing the confidence computed for the patch center
#

def computeC(psiHatP=None, filledImage=None, confidenceImage=None):
    assert confidenceImage is not None
    assert filledImage is not None
    assert psiHatP is not None
    
    #########################################
    ## PLACE YOUR CODE BETWEEN THESE LINES ##
    #########################################
    
    filled, valid = copyutils.getWindow(filledImage, psiHatP._coords, psiHatP._w, outofboundsvalue=False)
    conf, _ = copyutils.getWindow(confidenceImage, psiHatP._coords, psiHatP._w)

    filled_mask = filled / 255
    C = np.sum(conf * filled_mask) / np.sum(valid)

    # print("conf:\n{}".format(conf))
    # print("filled_mask:\n{}".format(filled_mask))
    # print("sum(conf): {}".format(np.sum(conf)))
    # print("sum(conf*filled): {}".format(np.sum(conf*filled_mask)))
    # print("sum(valid): {}".format(np.sum(valid)))
    # print("C: {}".format(C))

    #########################################
    
    return C

#########################################
#
# Computing the max Gradient of a patch on the fill front
#
# Input arguments: 
#    psiHatP: 
#         A member of the PSI class that defines the
#         patch. See file inpainting/psi.py for details
#         on the various methods this class contains.
#         In particular, the class provides a method for
#         accessing the coordinates of the patch center, etc
#    filledImage:
#         An OpenCV image of type uint8 that contains a value of 255
#         for every pixel in image I whose color is known (ie. either
#         a pixel that was not masked initially or a pixel that has
#         already been inpainted), and 0 for all other pixels
#    inpaintedImage:
#         A color OpenCV image of type uint8 that contains the 
#         image I, ie. the image being inpainted
#
# Return values:
#         Dy: The component of the gradient that lies along the 
#             y axis (ie. the vertical axis).
#         Dx: The component of the gradient that lies along the 
#             x axis (ie. the horizontal axis).
#
    
def computeGradient(psiHatP=None, inpaintedImage=None, filledImage=None):
    assert inpaintedImage is not None
    assert filledImage is not None
    assert psiHatP is not None
    
    #########################################
    ## PLACE YOUR CODE BETWEEN THESE LINES ##
    #########################################

    # Create a mask of valid `q`s'
    #   - Previously filled
    #   - Valid, i.e. inside boundary
    #   - Filled conv with np.ones((3,3)) is exactly 255*3*3
    #       indicates gradient values that is not corrupted by unfilled pixels
    #       assuming gradient estimated with a 3x3 kernel

    pix, valid = copyutils.getWindow(inpaintedImage, psiHatP._coords, psiHatP._w)
    filled, _ = copyutils.getWindow(filledImage, psiHatP._coords, psiHatP._w, outofboundsvalue=False)
    gray = cv.cvtColor(pix, cv.COLOR_BGR2GRAY)

    filled_padded = cv.copyMakeBorder(filled,1,1,1,1,cv.BORDER_CONSTANT,value=0)
    uncorrupted = cv.filter2D(filled_padded,cv.CV_16S,np.ones((3,3)))

    valid_q = np.logical_and(np.logical_and(valid, filled), uncorrupted[1:-1,1:-1] == 255*3*3)

    grad_x = cv.Scharr(gray,cv.CV_32F,1,0) * valid_q
    grad_y = cv.Scharr(gray,cv.CV_32F,0,1) * valid_q

    grad_l2 = grad_x*grad_x + grad_y*grad_y
    q = np.unravel_index(np.argmax(grad_l2), grad_l2.shape)
    Dx = grad_x[q]
    Dy = grad_y[q]

    # print("gray:\n{}".format(gray))
    # print("valid:\n{}".format(valid))
    # print("filled:\n{}".format(filled))
    # print("uncorrupted:\n{}".format(uncorrupted[1:-1,1:-1]))
    # print("q mask:\n{}".format(valid_q))
    # print("gradx masked:\n{}".format(grad_x))
    # print("grad_magnitude:\n{}".format(grad_l2))
    # print("q; Dx,Dy: {} ; {}".format(q, (Dx,Dy)))

    #########################################

    return Dy, Dx

#########################################
#
# Computing the normal to the fill front at the patch center
#
# Input arguments: 
#    psiHatP: 
#         A member of the PSI class that defines the
#         patch. See file inpainting/psi.py for details
#         on the various methods this class contains.
#         In particular, the class provides a method for
#         accessing the coordinates of the patch center, etc
#    filledImage:
#         An OpenCV image of type uint8 that contains a value of 255
#         for every pixel in image I whose color is known (ie. either
#         a pixel that was not masked initially or a pixel that has
#         already been inpainted), and 0 for all other pixels
#    fillFront:
#         An OpenCV image of type uint8 that whose intensity is 255
#         for all pixels that are currently on the fill front and 0 
#         at all other pixels
#
# Return values:
#         Ny: The component of the normal that lies along the 
#             y axis (ie. the vertical axis).
#         Nx: The component of the normal that lies along the 
#             x axis (ie. the horizontal axis).
#
# Note: if the fill front consists of exactly one pixel (ie. the
#       pixel at the patch center), the fill front is degenerate
#       and has no well-defined normal. In that case, you should
#       set Nx=None and Ny=None
#

def computeNormal(psiHatP=None, filledImage=None, fillFront=None):
    assert filledImage is not None
    assert fillFront is not None
    assert psiHatP is not None

    #########################################
    ## PLACE YOUR CODE BETWEEN THESE LINES ##
    #########################################
    
    fill, _ = copyutils.getWindow(filledImage, psiHatP._coords, psiHatP._w)

    # simply use a 3x3 sobel kernel over `p` 
    #   can use gradient as substitute for normal 
    #   since computing 
    #       | gradI \cdot n_p| = | norm(gradI) norm(n_p) cos(theta) |
    #       same regardless or orientation of `n_p` by |cos(theta)| = |-cos(theta + \pi)|
    
    grad_x = cv.Sobel(fill,cv.CV_32F,1,0,ksize=5)
    grad_y = cv.Sobel(fill,cv.CV_32F,0,1,ksize=5)
    Nx = grad_x[psiHatP._w, psiHatP._w]
    Ny = grad_y[psiHatP._w, psiHatP._w]
    Nx,Ny = normalize2d([Nx,Ny])

    # print("Nx,Ny,norm: {}".format((Nx,Ny,N_norm)))

    #########################################

    return Ny, Nx

