import struct
import hashlib
import os
from pathlib import Path

class ESPShader:
    """Генерирует модифицированные шейдеры для ESP через цветовую подсветку"""

    def __init__(self, output_dir="output"):
        self.output = Path(output_dir)
        self.output.mkdir(exist_ok=True)

    def generate_outline_shader(self):
        """
        Создаёт модифицированный USF (Unreal Shader Format) файл.
        Заменяет стандартный шейдер персонажей на шейдер с обводкой.
        """
        shader_code = """
// Modified CharacterOutline.usf
// ESP highlight shader - renders enemy outline through geometry

#include "Common.ush"
#include "PostProcess.ush"

// Outline parameters
float4 OutlineColor;
float OutlineWidth;
float OutlineOpacity;
float DepthBias;

// Depth comparison for through-wall rendering
float4 CharacterOutlinePS(float4 ScreenPos : SV_POSITION) : SV_Target0
{
    float2 UV = ScreenPos.xy / ScreenPos.w;
    float SceneDepth = SceneDepthTexture.Sample(SceneDepthSampler, UV).r;
    
    // Render at reduced depth priority - visible through walls
    if (DepthBias > 0.01)
    {
        return float4(OutlineColor.rgb, OutlineOpacity);
    }
    
    return float4(OutlineColor.rgb, OutlineOpacity * 0.5);
}
"""
        
        output_file = self.output / "CharacterOutline.usf"
        with open(output_file, 'w') as f:
            f.write(shader_code)
        
        return output_file

    def generate_material_override(self):
        """
        Генерирует бинарный override материала.
        Red channel = 1.0, Green = 0.0, Blue = 0.0, Alpha = 0.9
        Это даёт красную подсветку врагов сквозь стены.
        """
        # Упрощённая структура material instance
        mat_data = bytearray()
        
        # Header
        mat_data += struct.pack('<I', 0x9E2A83C1)  # Package magic
        mat_data += struct.pack('<I', 514)  # Version (UE 4.23)
        mat_data += struct.pack('<I', 0)    # Flags
        mat_data += struct.pack('<I', 86)   # Name count
        mat_data += struct.pack('<I', 128)  # Name offset
        
        # Names
        name_table = [
            ("None", 0), ("Root", 0), ("Material", 0),
            ("MI_CharacterOutline", 0), ("BaseColor", 0),
            ("Opacity", 0), ("WorldPositionOffset", 0),
            ("OutlineWidth", 0), ("DepthPriority", 0),
        ]
        
        for name, num in name_table:
            mat_data += struct.pack('<I', len(name))
            mat_data += name.encode('ascii')
            mat_data += struct.pack('<I', num)
        
        # Vector parameters (color)
        mat_data += struct.pack('<ffff', 1.0, 0.0, 0.0, 0.9)  # Red outline
        mat_data += struct.pack('<ffff', 0.0, 1.0, 0.0, 0.9)  # Backup green
        
        # Scalar parameters
        mat_data += struct.pack('<f', 2.0)    # OutlineWidth
        mat_data += struct.pack('<f', 0.9)    # Opacity
        mat_data += struct.pack('<f', -1.0)   # DepthBias (renders on top)
        mat_data += struct.pack('<f', 1000.0) # DrawDistance
        
        output_file = self.output / "MI_CharacterOutline.uasset"
        with open(output_file, 'wb') as f:
            f.write(bytes(mat_data))
        
        return output_file

    def generate_color_hack_config(self):
        """
        Конфиг для изменения цветов через ini.
        Заставляет движок рендерить врагов ярко-красными.
        """
        config = """[/Script/ShadowTrackerExtra.STExtraGameUserSettings]
bUseCustomCharacterColor=True
CustomCharacterColorR=1.0
CustomCharacterColorG=0.0
CustomCharacterColorB=0.0
CustomCharacterColorA=0.9

[/Script/Engine.RendererSettings]
r.CustomDepth=3
r.DepthOfFieldQuality=0
r.PostProcessAAQuality=0

[/Script/ShadowTrackerExtra.STExtraCharacter]
bShowThroughWalls=True
ThroughWallOpacity=0.8
OutlineColor=(R=1.0,G=0.0,B=0.0,A=1.0)
"""
        
        output_file = self.output / "DefaultGame.ini"
        with open(output_file, 'w') as f:
            f.write(config)
        
        return output_file


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--enable', action='store_true')
    args = parser.parse_args()
    
    esp = ESPShader()
    esp.generate_outline_shader()
    esp.generate_material_override()
    esp.generate_color_hack_config()
    print("[+] ESP shaders generated.")
