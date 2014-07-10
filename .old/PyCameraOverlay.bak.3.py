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
    shader_vertex = '''
    // Vertex program
    varying vec3 pos;
    void main() {
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        pos = gl_Vertex.xyz;
    }
    '''
    shader_frag = '''
    // Fragment program
    varying vec3 pos;
    void main() {
        gl_FragColor.r = sin(pos.x);
        gl_FragColor.g = sin(pos.y);
        gl_FragColor.b = sin(pos.z);
        gl_FragColor.a = 1.0;
    }
    '''
    # Compile shader
    shader = ShaderProgram([
        ShaderVertex(shader_vertex),
        ShaderFragment(shader_frag)
    ])

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

    edgeDetectionShader = ShaderProgram([
        ShaderVertex('''
            void main() {
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
        '''),
        ShaderFragment('''
            uniform sampler2D texture1;
            varying vec3 pos;

float threshold(in float thr1, in float thr2 , in float val) {
 if (val < thr1) {return 0.0;}
 if (val > thr2) {return 1.0;}
 return val;
}

// averaged pixel intensity from 3 color channels
float avg_intensity(in vec4 pix) {
 return (pix.r + pix.g + pix.b)/3.;
}

vec4 get_pixel(in vec2 coords, in float dx, in float dy) {
 return texture2D(texture1,coords + vec2(dx, dy));
}

// returns pixel color
float IsEdge(in vec2 coords){
  float dxtex = 1.0 / 800.0 /*image width*/;
  float dytex = 1.0 / 600.0 /*image height*/;
  float pix[9];
  int k = -1;
  float delta;

  // read neighboring pixel intensities
  for (int i=-1; i<2; i++) {
   for(int j=-1; j<2; j++) {
    k++;
    pix[k] = avg_intensity(get_pixel(coords,float(i)*dxtex,
                                          float(j)*dytex));
   }
  }

  // average color differences around neighboring pixels
  delta = (abs(pix[1]-pix[7])+
          abs(pix[5]-pix[3]) +
          abs(pix[0]-pix[8])+
          abs(pix[2]-pix[6])
           )/2.;

  return threshold(0.25,0.4,clamp(1.8*delta,0.0,1.0));
}

void main()
{  
  vec2 pixel = gl_TexCoord[0].xy;

  vec4 color = vec4(0.0,0.0,0.0,1.0);
  //color.r =  IsEdge(pixel);
  color.g =  IsEdge(pixel);
  //color.b =  IsEdge(pixel);

  gl_FragColor = color;

}
        ''')
    ])

    crapifyShader = ShaderProgram([
        ShaderVertex('''
            void main() {
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
        '''),
        ShaderFragment('''
            uniform sampler2D texture1;
            void main() {
                float fidelity = 4.8;

                vec2 pixel = gl_TexCoord[0].xy;
                vec4 color = texture(texture1, pixel);

                color *= fidelity;
                color = round(color);
                color /= fidelity;

                gl_FragColor = color;
            }
        ''')
    ])

    cartoonShader = ShaderProgram([
        ShaderVertex('''
            void main() {
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
                gl_TexCoord[0] = gl_MultiTexCoord0;
            }
        '''),
        ShaderFragment('''
            uniform sampler2D texture1;
            varying vec3 pos;

float threshold(in float thr1, in float thr2 , in float val) {
 if (val < thr1) {return 0.0;}
 if (val > thr2) {return 1.0;}
 return val;
}

// averaged pixel intensity from 3 color channels
float avg_intensity(in vec4 pix) {
 return (pix.r + pix.g + pix.b)/3.;
}

vec4 get_pixel(in vec2 coords, in float dx, in float dy) {
 return texture2D(texture1,coords + vec2(dx, dy));
}

// returns pixel color
float IsEdge(in vec2 coords){
  float dxtex = 1.0 / 800.0 /*image width*/;
  float dytex = 1.0 / 600.0 /*image height*/;
  float pix[9];
  int k = -1;
  float delta;

  // read neighboring pixel intensities
  for (int i=-1; i<2; i++) {
   for(int j=-1; j<2; j++) {
    k++;
    pix[k] = avg_intensity(get_pixel(coords,float(i)*dxtex,
                                          float(j)*dytex));
   }
  }

  // average color differences around neighboring pixels
  delta = (abs(pix[1]-pix[7])+
          abs(pix[5]-pix[3]) +
          abs(pix[0]-pix[8])+
          abs(pix[2]-pix[6])
           )/2.;

  return threshold(0.25,0.4,clamp(1.8*delta,0.0,1.0));
}

void main()
{
  float fidelity = 4.8;
  float whiteThreshold = 0.5;
  float whiteCap = 0.9;
  
  vec2 pixel = gl_TexCoord[0].xy;
  /*if (pixel.x > 0.5) {
    pixel.x = 1 - pixel.x;
  }
  if (pixel.y < 0.5) {
    pixel.y = 1 - pixel.y;
  }*/

  vec4 tempColor = texture(texture1, pixel);

  vec4 color = vec4(0.0,0.0,0.0,1.0);
  color.r =  IsEdge(pixel);
  color.g =  IsEdge(pixel);
  color.b =  IsEdge(pixel);

  tempColor *= fidelity;
  tempColor = round(tempColor);
  tempColor /= fidelity;

  if (color.r <= whiteThreshold 
   && color.g <= whiteThreshold 
   && color.b <= whiteThreshold) {
    color = tempColor;
  }

  if (color.r <= whiteCap 
   && color.g <= whiteCap 
   && color.b <= whiteCap) {
    color = color * 0.2 + tempColor * 0.8;
  }

  if (color.r > whiteCap 
   && color.g > whiteCap 
   && color.b > whiteCap) {
    color = vec4(0, 0, 0, 1);
  }
  
  color.a = 1.0;

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
        #texturedQuad(0, 0, ImageSrc, 400, 400)

        #ShaderProgram.use(shader)
        #rectangle(100, 100, 300, 300)
        #ShaderProgram.clear()
        
        #texturedQuadShader(0, 0, ImageSrc, camShader)
        
        texturedQuadShader(0, 0, camTexture, camShader)

        #texturedQuadShader(0, 0, camTexture, camShader, 640, 360)
        #texturedQuadShader(640, 0, camTexture, edgeDetectionShader, 640, 360)
        #texturedQuadShader(0, 360, camTexture, crapifyShader, 640, 360)
        #texturedQuadShader(640, 360, camTexture, cartoonShader, 640, 360)

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
        clock.tick(30)
        if not get_input(): break
        snapshot = cam.get_image(snapshot)
        camTexture.rawReference = pygame.image.tostring(snapshot, "RGB")
        camTexture.xSize, camTexture.ySize = cam_size
        draw()
