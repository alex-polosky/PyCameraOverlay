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
from OpenGL.GL.ARB.shader_objects import *
from OpenGL.GL.ARB.vertex_shader import *
from OpenGL.GL.ARB.fragment_shader import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *

from math import cos, radians, sin

######################################################
## Texture
class Texture(object):
    def __init__(self):
        self.xSize, self.ySize = 0, 0
        self.rawReference = None
        self.rawReferenceFormat = None
        self.gl_id = glGenTextures(1)

class RandomTexture(Texture):
    def __init__(self, xSizeP, ySizeP):
        Texture.__init__(self)
        self.xSize, self.ySize = xSizeP, ySizeP
        self.textureArray = numpy.array([random.randint(0, 255) for i in range( 3 * self.xSize * self.ySize)])
        self.rawReference = ''.join([chr(i) for i in self.textureArray])
        self.rawReferenceFormat = "P"

class FileTexture(Texture):
    def __init__(self, fileName):
        Texture.__init__(self)
        image = pygame.image.load(fileName)
        self._image = image
        self.xSize, self.ySize = self._image.get_size()
        self.rawReference = pygame.image.tostring(self._image, "RGB")
        self.rawReferenceFormat = "RGB"

######################################################
## Shader
class ShaderBase(object):
    def __init__(self, source, type):
        '''source = GLSL Code
           type = GLSL type (GL_VERTEX_SHADER|GL_FRAGMENT_SHADER)
        '''
        self.source = source

        self.shader = glCreateShader(type)

        glShaderSource(self.shader, [source])
        glCompileShader(self.shader)

        status = c_int()
        glGetShaderiv(self.shader, GL_COMPILE_STATUS, status)
        if not status.value:
            #self.print_errors()
            raise ValueError, "Shader compiliation failed"
        
        self.print_log()

    def __del__(self): 
        #glDeleteObjectARB(self.shader)
        pass

    def print_log(self):
        #print glGetProgramInfoLog(self.shader)
        pass

class ShaderVertex(ShaderBase):
    def __init__(self, source):
        ShaderBase.__init__(self, source, GL_VERTEX_SHADER)

class ShaderFragment(ShaderBase):
    def __init__(self, source):
        ShaderBase.__init__(self, source, GL_FRAGMENT_SHADER)

class ShaderProgram(object):
    def __init__(self, shaders):
        self.shader = glCreateProgram()

        for shader in shaders:
            glAttachShader(self.shader, shader.shader)

        glValidateProgram(self.shader)
        glLinkProgram(self.shader)
        
        self.symbol_locations = {}

        self.print_log()

    def __del__(self):
        #glDeleteObjectARB(self.shader)
        pass

    def print_log(self):
        print glGetProgramInfoLog(self.shader)
        pass

    def get_location(self,symbol):
        if not symbol in self.symbol_locations.keys():
            self.symbol_locations[symbol] = glGetUniformLocation(self.shader, symbol.encode())
            if self.symbol_locations[symbol] == -1:
                print("Cannot get the location of symbol \""+symbol+"\"!")
        return self.symbol_locations[symbol]

    @staticmethod
    def use(shader=None):
        if shader == None:
            glUseProgram(0)
        else:
            glUseProgram(shader.shader)
    @staticmethod
    def clear():
        glUseProgram(0)


######################################################
## Window
class Window(object):
    def __init__(self):
        pass


############################
# This is all just the testing stuff
if __name__ == "__main__":
    # Window Vars
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    #screen_size = [800, 600]
    #cam_size = [800, 600]
    screen_size = [1280, 720]
    cam_size = [1280, 720]

    # Init pygame stuff
    glutInit([])
    pygame.init()
    pygame.camera.init()
    pygame.font.init()

    # Set up our display
    pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS,0)
    pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES,0)
    window = pygame.display.set_mode(screen_size,OPENGL|DOUBLEBUF)
    windowScreen = pygame.display.get_surface()

    # Clock stuff
    clock = pygame.time.Clock()

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
    RandSrc = RandomTexture(800, 600)
    ImageSrc = FileTexture("P:/test2.jpg")
    ImageSrc2 = FileTexture("P:/test3.jpg")

    # Load up shaders here
    camShader = ShaderProgram([
        ShaderVertex('''
            void main() {
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
        '''),
        ShaderFragment('''
            uniform sampler2D texture1;
            void main() {
                vec2 pixel = gl_TexCoord[0].xy;
                vec4 color = texture(texture1, pixel);

                gl_FragColor = color;
            }
        ''')
    ])
    
    
    ###########################
    # SETTING UP CAM STUFF HERE
    snapshot = pygame.surface.Surface(cam_size, 0, windowScreen)
    camTexture = Texture()
    camTexture.xSize, camTexture.ySize = cam_size
    camTexture.rawReference = snapshot

    cam = pygame.camera.Camera(pygame.camera.list_cameras()[0], cam_size)
    cam.set_resolution(*cam_size)
    cam.start()
    ###########################

    def rectangle(x, y, length, width):
        glBegin(GL_QUADS)

        glColor3f(1, 0, 1)
        glVertex2f(x, y)
        glColor3f(0, 1, 1)
        glVertex2f(x+length, y)
        glColor3f(1, 1, 0)
        glVertex2f(x+length, y+width)
        glColor3f(1, 1, 1)
        glVertex2f(x, y+width)
        
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
        
        glTexCoord2f(0,0); glVertex2f(0, 0)
        glTexCoord2f(1,0); glVertex2f(x+length, 0)
        glTexCoord2f(1,1); glVertex2f(x+length, y+width)
        glTexCoord2f(0,1); glVertex2f(0, y+width)

        glEnd()

    def texturedQuadShader(x, y, texture, shader, length=None, width=None):
        # Set up defaults
        if length == None:
            length = texture.xSize
        if width == None:
            width = texture.ySize
            
        ShaderProgram.use(shader)

        glActiveTexture(GL_TEXTURE0)
        active_texture = glGetIntegerv(GL_ACTIVE_TEXTURE) - GL_TEXTURE0
        loc = shader.get_location("texture1")
        glUniform1i(loc, active_texture)
        glBindTexture(GL_TEXTURE_2D, texture.gl_id)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, texture.xSize, texture.ySize, 0,
                    GL_RGB, GL_UNSIGNED_BYTE, texture.rawReference )

        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(x, y)
        glTexCoord2f(1,0); glVertex2f(x+length, y)
        glTexCoord2f(1,1); glVertex2f(x+length, y+width)
        glTexCoord2f(0,1); glVertex2f(x, y+width)
        glEnd()

        ShaderProgram.clear()

    # Drawing
    def draw():
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)
        glColor4f(1,1,1,1)

        #circle(screen_size[0]/2, screen_size[1]/2, screen_size[1]/2)
        #rectangle(0, 0, *screen_size)
        #texturedQuad(0, 0, camTexture)
        #texturedQuad(0, 0, ImageSrc, 800,600)
        
        texturedQuadShader(0, 0, camTexture, camShader)

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
                if   event.key == K_F2:
                    pygame.image.save(windowScreen, "P:/testSave.png")
        return True

    while True:
        clock.tick(30)
        if not get_input(): break
        snapshot = cam.get_image(snapshot)
        camTexture.rawReference = pygame.image.tostring(snapshot, "RGB")
        camTexture.xSize, camTexture.ySize = cam_size
        draw()
