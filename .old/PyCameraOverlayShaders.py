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

    