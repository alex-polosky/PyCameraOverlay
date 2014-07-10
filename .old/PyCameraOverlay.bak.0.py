#!python
# PyCameraOverlay
import numpy
import os
import pygame
import pygame.camera
import pygame.font
import pygame.image
import random
import sys
import win32gui

from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *

from math import cos, radians, sin

class Texture(object):
    def __init__(self):
        self.xSize, self.ySize = 0, 0
        self.rawReference = None
        self.rawReferenceFormat = None

class RandomTexture(Texture):
    def __init__(self, xSizeP, ySizeP):
        self.xSize, self.ySize = xSizeP, ySizeP
        self.textureArray = numpy.array([random.randint(0, 255) for i in range( 3 * self.xSize * self.ySize)])
        self.rawReference = ''.join([chr(i) for i in self.textureArray])
        self.rawReferenceFormat = "P"

class FileTexture(Texture):
    def __init__(self, fileName):
        image = pygame.image.load(fileName)
        self._image = image
        self.xSize, self.ySize = self._image.get_size()
        self.rawReference = pygame.image.tostring(self._image, "RGB")
        self.rawReferenceFormat = "RGB"



############################
# This is all just the testing stuff
if __name__ == "__main__":
    # Window Vars
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    screen_size = [800, 600]

    # Init pygame stuff
    pygame.init()
    pygame.camera.init()
    pygame.font.init()

    # Set up our display
    pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS,0)
    pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES,0)
    pygame.display.set_mode(screen_size,OPENGL|DOUBLEBUF)

    # Set up OpenGL
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

    glEnable(GL_TEXTURE_2D)
    glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_MODULATE)
    glTexEnvi(GL_POINT_SPRITE,GL_COORD_REPLACE,GL_TRUE)

    # Set up Camera
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, screen_size[0], screen_size[1], 0, 0, 1)
    glMatrixMode(GL_MODELVIEW)

    glDisable(GL_DEPTH_TEST)

    # Load up resources
    #ImageSrc = RandomTexture(400, 400)
    ImageSrc = FileTexture("P:/test2.jpg")

    def rectangle(x, y):
        glBegin(GL_QUADS)
        glColor3f(1, 0, 1)
        glVertex2f(0, 0)
        glColor3f(0, 1, 1)
        glVertex2f(x, 0)
        glColor3f(1, 1, 0)
        glVertex2f(x, y)
        glColor3f(1, 1, 1)
        glVertex2f(0, y)
        glEnd()

    def circle(x, y, radius):
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(1, 1, 1)
        glVertex2f(x, y)
        for angle in range(0, 361):
        #    glColor3f(
        #        (angle + random.randrange(-50, 50)) / 360.0, 
        #        (angle + random.randrange(-50, 50)) / 360.0, 
        #        (angle + random.randrange(-50, 50)) / 360.0
        #    )
            glVertex2f(x + sin(angle) * radius, y + cos(angle) * radius)
        glEnd()
    
    def texturedQuad(x, y, texture, length=None, width=None):
        # Set up defaults
        if length == None:
            length = texture.xSize
        if width == None:
            width = texture.ySize

        # Set up info about the texture
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, texture.xSize, texture.ySize, 0,
                    GL_RGB, GL_UNSIGNED_BYTE, texture.rawReference )

        glColor3f(1, 1, 1)

        glBegin(GL_QUADS)
        
        glTexCoord2f(0, 1)
        glVertex2f(x, y+width)
        glTexCoord2f(0, 0)
        glVertex2f(x, y)
        glTexCoord2f(1, 0)
        glVertex2f(x+length, y)
        glTexCoord2f(1, 1)
        glVertex2f(x+length, y+width)

        glEnd()

    # Drawing
    def draw():
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(1,1,1)

        #rectangle(*screen_size)
        #circle(screen_size[0]/2, screen_size[1]/2, screen_size[1]/2)
        texturedQuad(0, 0, ImageSrc)

        pygame.display.flip()

    # Input
    def get_input():
        keys_pressed = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_position = pygame.mouse.get_pos()
        mouse_rel = pygame.mouse.get_rel()
        for event in pygame.event.get():
            if   event.type == QUIT: return False
            elif event.type == KEYDOWN:
                if   event.key == K_ESCAPE: return False
        return True

    while True:
        if not get_input(): break
        draw()
