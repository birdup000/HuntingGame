"""
Post-processing effects for photorealistic rendering.
Provides bloom, SSAO, anti-aliasing, and other visual enhancements.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    WindowProperties, FrameBufferProperties, Texture, GraphicsOutput,
    Camera, NodePath, TextureAttrib, RenderState, Shader, CardMaker
)


class PostProcessing:
    """Post-processing effects manager for cinematic quality."""
    
    def __init__(self, base_app: ShowBase):
        self.base = base_app
        self.bloom_enabled = True
        self.ssao_enabled = False  # Disabled by default for performance
        self.fxaa_enabled = True
        self.motion_blur_enabled = False
        self.bloom_intensity = 1.2
        self.ssao_radius = 1.0
        self.is_setup = False
        self.bloom_task = None  # Initialize bloom task
        self.filters = None
        
    def enable_bloom(self, intensity=1.2, threshold=1.0):
        """Enable bloom (HDR) effect for bright objects."""
        if not self.is_setup:
            self._setup_render_pipeline()
        bloom_vert = """
        #version 120
        void main() {
            gl_Position = ftransform();
            gl_TexCoord[0] = gl_MultiTexCoord0;
        }
        """
        bloom_frag = """
        #version 120
        uniform sampler2D tex;
        uniform float intensity;
        uniform float threshold;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec4 color = texture2D(tex, uv);
            float brightness = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
            if (brightness > threshold) {
                vec4 glow = vec4(0);
                for (int i = -1; i <= 1; i++) {
                    for (int j = -1; j <= 1; j++) {
                        vec2 offset = vec2(i, j) * 0.005;
                        glow += texture2D(tex, uv + offset);
                    }
                }
                glow /= 9.0;
                gl_FragColor = color + glow * intensity;
            } else {
                gl_FragColor = color;
            }
        }
        """
        self.bloom_shader = Shader.make(Shader.SL_GLSL, bloom_vert, bloom_frag)
        self.post_quad.set_shader(self.bloom_shader)
        self.post_quad.set_shader_input('tex', self.scene_tex)
        self.post_quad.set_shader_input('intensity', intensity)
        self.post_quad.set_shader_input('threshold', threshold)
        self.bloom_enabled = True
        
    def disable_bloom(self):
        """Disable bloom effect."""
        if hasattr(self, 'bloom_shader'):
            self.post_quad.set_shader(None)
            self.bloom_enabled = False
            
    def enable_ssao(self, radius=1.0, intensity=1.5):
        """Enable screen space ambient occlusion."""
        if not self.is_setup:
            self._setup_render_pipeline()
        ssao_vert = """
        #version 120
        void main() {
            gl_Position = ftransform();
            gl_TexCoord[0] = gl_MultiTexCoord0;
        }
        """
        ssao_frag = """
        #version 120
        uniform sampler2D tex;
        uniform sampler2D depthTex;
        uniform vec2 texelSize;
        uniform float radius;
        uniform float intensity;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec4 color = texture2D(tex, uv);
            float depth = texture2D(depthTex, uv).r;
            float occlusion = 0.0;
            for (int i = -2; i <= 2; i++) {
                for (int j = -2; j <= 2; j++) {
                    vec2 offset = vec2(i, j) * texelSize * radius;
                    float sampleDepth = texture2D(depthTex, uv + offset).r;
                    occlusion += (sampleDepth < depth - 0.01) ? 1.0 : 0.0;
                }
            }
            occlusion /= 25.0;
            float ao = 1.0 - occlusion * intensity;
            gl_FragColor = color * vec4(vec3(ao), 1.0);
        }
        """
        self.ssao_shader = Shader.make(Shader.SL_GLSL, ssao_vert, ssao_frag)
        self.post_quad.set_shader(self.ssao_shader)
        self.post_quad.set_shader_input('tex', self.scene_tex)
        self.post_quad.set_shader_input('depthTex', self.depth_tex)
        self.post_quad.set_shader_input('texelSize', (1.0 / self.base.win.get_x_size(), 1.0 / self.base.win.get_y_size()))
        self.post_quad.set_shader_input('radius', radius)
        self.post_quad.set_shader_input('intensity', intensity)
        self.ssao_enabled = True
        
    def enable_fxaa(self):
        """Enable fast approximate anti-aliasing."""
        if not self.is_setup:
            self._setup_render_pipeline()
        fxaa_vert = """
        #version 120
        void main() {
            gl_Position = ftransform();
            gl_TexCoord[0] = gl_MultiTexCoord0;
        }
        """
        fxaa_frag = """
        #version 120
        uniform sampler2D tex;
        uniform vec2 texelSize;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec4 color = texture2D(tex, uv);
            vec4 left = texture2D(tex, uv - vec2(texelSize.x, 0));
            vec4 right = texture2D(tex, uv + vec2(texelSize.x, 0));
            vec4 up = texture2D(tex, uv + vec2(0, texelSize.y));
            vec4 down = texture2D(tex, uv - vec2(0, texelSize.y));
            vec4 avg = (left + right + up + down + color) / 5.0;
            float edge = length(color - avg);
            gl_FragColor = mix(color, avg, clamp(edge * 2.0, 0.0, 1.0));
        }
        """
        self.fxaa_shader = Shader.make(Shader.SL_GLSL, fxaa_vert, fxaa_frag)
        self.post_quad.set_shader(self.fxaa_shader)
        self.post_quad.set_shader_input('tex', self.scene_tex)
        self.post_quad.set_shader_input('texelSize', (1.0 / self.base.win.get_x_size(), 1.0 / self.base.win.get_y_size()))
        self.fxaa_enabled = True
        
    def _setup_render_pipeline(self):
        """Set up enhanced rendering pipeline."""
        import logging
        logging.info("Setting up post-processing render pipeline")
        # Create offscreen buffer with color and depth
        fbprops = FrameBufferProperties()
        fbprops.set_rgb_color(True)
        fbprops.set_rgba_bits(8, 8, 8, 0)
        fbprops.set_depth_bits(24)
        self.scene_buffer = self.base.win.make_texture_buffer("scene", self.base.win.get_x_size(), self.base.win.get_y_size(), to_ram=False, fbp=fbprops)
        self.scene_tex = Texture()
        self.scene_tex.set_format(Texture.F_rgba)
        self.depth_tex = Texture()
        self.depth_tex.set_format(Texture.F_depth_component)
        self.scene_buffer.add_render_texture(self.scene_tex, GraphicsOutput.RTMCopyTexture, GraphicsOutput.RTP_color)
        self.scene_buffer.add_render_texture(self.depth_tex, GraphicsOutput.RTMCopyTexture, GraphicsOutput.RTP_depth)
        self.scene_camera = self.base.make_camera(self.scene_buffer)
        self.scene_camera.reparent_to(self.base.render)
        # Create quad for post-processing
        cm = CardMaker('post_quad')
        cm.set_frame_fullscreen_quad()
        self.post_quad = self.base.render2d.attach_new_node(cm.generate())
        self.post_quad.set_texture(self.scene_tex)
        self.is_setup = True
        logging.info("Post-processing render pipeline setup completed")
        
    def _update_bloom(self, task):
        """Update bloom effect — handled by shader, no per-frame work needed."""
        return task.cont
        
    def adjust_exposure(self, exposure_value):
        """Adjust exposure for different lighting conditions."""
        # Exposure adjustment stub — would require HDR pipeline
        pass

    def enable_motion_blur(self, strength=0.5):
        """Enable motion blur effect using frame accumulation shader."""
        if not self.is_setup:
            return
        blur_vert = """
        #version 120
        void main() {
            gl_Position = ftransform();
            gl_TexCoord[0] = gl_MultiTexCoord0;
        }
        """
        blur_frag = """
        #version 120
        uniform sampler2D tex;
        uniform sampler2D prevTex;
        uniform float strength;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec4 current = texture2D(tex, uv);
            vec4 previous = texture2D(prevTex, uv);
            gl_FragColor = mix(current, previous, strength);
        }
        """
        self.motion_blur_shader = Shader.make(Shader.SL_GLSL, blur_vert, blur_frag)
        self.post_quad.set_shader(self.motion_blur_shader)
        self.post_quad.set_shader_input('tex', self.scene_tex)
        self.post_quad.set_shader_input('prevTex', self.scene_tex)
        self.post_quad.set_shader_input('strength', strength)
        self.motion_blur_enabled = True


class CinematicEffects:
    """Cinematic visual effects for immersion."""
    
    def __init__(self, base_app: ShowBase):
        self.base = base_app
        self.motion_blur_active = False
        self.depth_of_field_active = False
        self.color_grading_active = False
        self._vignette_quad = None
        self._color_grade_quad = None
        
    def enable_color_grading(self, preset='neutral'):
        """Apply color grading via a fullscreen post-process shader."""
        if self._color_grade_quad:
            return
        
        presets = {
            'neutral': (1.0, 1.0, 1.0, 0.0, 0.0, 0.0),  # (contrast, saturation, brightness, r_shift, g_shift, b_shift)
            'warm': (1.05, 1.1, 1.02, 0.05, 0.02, -0.02),
            'cool': (1.05, 0.95, 1.0, -0.02, 0.0, 0.04),
            'vibrant': (1.1, 1.3, 1.0, 0.0, 0.0, 0.0),
        }
        params = presets.get(preset, presets['neutral'])
        
        vert = """
        #version 120
        void main() {
            gl_Position = ftransform();
            gl_TexCoord[0] = gl_MultiTexCoord0;
        }
        """
        frag = """
        #version 120
        uniform sampler2D tex;
        uniform float contrast;
        uniform float saturation;
        uniform float brightness;
        uniform vec3 colorShift;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec4 color = texture2D(tex, uv);
            // Contrast
            color.rgb = (color.rgb - 0.5) * contrast + 0.5;
            // Saturation
            float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
            color.rgb = mix(vec3(gray), color.rgb, saturation);
            // Brightness
            color.rgb *= brightness;
            // Color shift
            color.rgb += colorShift;
            gl_FragColor = clamp(color, 0.0, 1.0);
        }
        """
        from panda3d.core import CardMaker, TransparencyAttrib, Shader
        cm = CardMaker('color_grade')
        cm.setFrameFullscreenQuad()
        self._color_grade_quad = self.base.render2d.attachNewNode(cm.generate())
        self._color_grade_quad.setTransparency(TransparencyAttrib.MNone)
        self._color_grade_quad.setBin('fixed', 50)
        self._color_grade_quad.setDepthTest(False)
        self._color_grade_quad.setDepthWrite(False)
        grade_shader = Shader.make(Shader.SL_GLSL, vert, frag)
        self._color_grade_quad.setShader(grade_shader)
        self._color_grade_quad.setShaderInput('tex', self.base.win.getTexture())
        self._color_grade_quad.setShaderInput('contrast', params[0])
        self._color_grade_quad.setShaderInput('saturation', params[1])
        self._color_grade_quad.setShaderInput('brightness', params[2])
        self._color_grade_quad.setShaderInput('colorShift', (params[3], params[4], params[5]))
        self.color_grading_active = True
        
    def add_vignette(self, intensity=0.3):
        """Add darkened edges for cinematic look using a fullscreen shader quad."""
        if self._vignette_quad:
            return
        vignette_vert = """
        #version 120
        void main() {
            gl_Position = ftransform();
            gl_TexCoord[0] = gl_MultiTexCoord0;
        }
        """
        vignette_frag = """
        #version 120
        uniform float intensity;
        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec2 center = uv - 0.5;
            float dist = length(center);
            float vignette = 1.0 - dist * intensity * 1.5;
            vignette = smoothstep(0.0, 1.0, vignette);
            gl_FragColor = vec4(0.0, 0.0, 0.0, (1.0 - vignette) * 0.85);
        }
        """
        from panda3d.core import CardMaker, TransparencyAttrib, Shader
        cm = CardMaker('vignette')
        cm.setFrameFullscreenQuad()
        self._vignette_quad = self.base.render2d.attachNewNode(cm.generate())
        self._vignette_quad.setTransparency(TransparencyAttrib.MAlpha)
        self._vignette_quad.setBin('fixed', 100)
        self._vignette_quad.setDepthTest(False)
        self._vignette_quad.setDepthWrite(False)
        vignette_shader = Shader.make(Shader.SL_GLSL, vignette_vert, vignette_frag)
        self._vignette_quad.setShader(vignette_shader)
        self._vignette_quad.setShaderInput('intensity', intensity)


# Common post-processing presets
PRESETS = {
    'realistic': {
        'bloom': True,
        'bloom_intensity': 1.0,
        'fxaa': True,
        'motion_blur': False,
        'color_grading': False
    },
    'cinematic': {
        'bloom': True,
        'bloom_intensity': 1.5,
        'fxaa': True,
        'motion_blur': True,
        'color_grading': True,
        'vignette': 0.2
    },
    'performance': {
        'bloom': False,
        'fxaa': True,
        'motion_blur': False,
        'ssao': False
    },
    'high_quality': {
        'bloom': True,
        'ssao': True,
        'fxaa': True,
        'motion_blur': True,
        'chromatic_aberration': 0.01
    }
}
