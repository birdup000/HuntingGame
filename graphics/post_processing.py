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
        """Update bloom effect."""
        print("Bloom update not implemented")
        return task.cont
        
    def adjust_exposure(self, exposure_value):
        """Adjust exposure for different lighting conditions."""
        print("Exposure adjustment not implemented")

    def enable_motion_blur(self, strength=0.5):
        """Enable motion blur effect."""
        print("Motion blur not implemented")


class CinematicEffects:
    """Cinematic visual effects for immersion."""
    
    def __init__(self, base_app: ShowBase):
        self.base = base_app
        self.motion_blur_active = False
        self.depth_of_field_active = False
        self.color_grading_active = False
        
    def enable_motion_blur(self, strength=0.5):
        """Add motion blur for cinematic movement."""
        print("Motion blur not implemented")
        
    def enable_depth_of_field(self, focus_distance=20.0, blur_amount=0.7):
        """Simulate camera depth of field."""
        print("Depth of field not implemented")
        
    def set_chromatic_aberration(self, amount=0.01):
        """Add subtle chromatic aberration for camera realism."""
        print("Chromatic aberration not implemented")
        
    def add_vignette(self, intensity=0.3):
        """Add darkened edges for cinematic look."""
        print("Vignette not implemented")


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
