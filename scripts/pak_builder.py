import os
import struct
import zlib
import hashlib
import json
from pathlib import Path

class PakBuilder:
    """Сборка .pak файлов для PUBG Mobile (Unreal Engine 4)"""

    MAGIC = 0x5A6F12E1  # UE4 pak magic
    
    def __init__(self, output_dir="output"):
        self.output = Path(output_dir)
        self.output.mkdir(exist_ok=True)
        
    def create_empty_pak(self, filename, original_size=None):
        """Создаёт пустой/пустыш pak файл для замены ресурсов"""
        pak_data = self._build_pak_header()
        
        # Если знаем оригинальный размер — паддинг
        if original_size:
            padding = original_size - len(pak_data)
            if padding > 0:
                pak_data += b'\x00' * padding
        
        filepath = self.output / filename
        with open(filepath, 'wb') as f:
            f.write(pak_data)
        
        return filepath

    def create_no_grass_pak(self):
        """Убирает траву — заменяет grass asset на пустой"""
        # Внутренняя структура для замены травы
        grass_replacements = [
            "ShadowTrackerExtra/Content/Environments/Grass/*",
            "ShadowTrackerExtra/Content/Materials/GrassMaterial.uasset",
            "ShadowTrackerExtra/Content/Meshes/SM_GrassCluster*.uasset",
        ]
        
        entries = []
        for path in grass_replacements:
            entry_data = b'\x00' * 64  # пустой ассет
            entries.append({
                'path': path,
                'offset': 0,
                'size': len(entry_data),
                'data': entry_data,
                'compression': 0x00  # none
            })
        
        pak_file = self._build_pak_with_entries(entries, "no_grass.pak")
        return pak_file

    def create_esp_pak(self):
        """ESP через модификацию материалов — враги подсвечены"""
        # Модифицируем материалы персонажей для пост-обработки
        entries = []
        
        # Прозрачные стены через модификацию материалов
        wall_materials = [
            "ShadowTrackerExtra/Content/Materials/Building/*",
            "ShadowTrackerExtra/Content/Materials/Environment/*",
        ]
        
        # Подсветка врагов через материал
        esp_material = self._generate_esp_material()
        
        entries.append({
            'path': "ShadowTrackerExtra/Content/Materials/CharacterOutline.uasset",
            'offset': 0,
            'size': len(esp_material),
            'data': esp_material,
            'compression': 0x00
        })
        
        pak_file = self._build_pak_with_entries(entries, "esp_highlight.pak")
        return pak_file

    def create_reduced_fog_pak(self):
        """Убирает туман"""
        entries = []
        fog_assets = [
            "ShadowTrackerExtra/Content/Environments/Fog/*",
            "ShadowTrackerExtra/Content/Materials/FogMaterial.uasset",
        ]
        
        for path in fog_assets:
            entries.append({
                'path': path,
                'offset': 0,
                'size': 32,
                'data': b'\x00' * 32,
                'compression': 0x00
            })
        
        return self._build_pak_with_entries(entries, "no_fog.pak")

    def _build_pak_header(self):
        """UE4 Pak Header (Version 8/9)"""
        header = struct.pack('<I', self.MAGIC)
        header += struct.pack('<I', 8)  # version
        header += struct.pack('<q', 0)  # index offset
        header += struct.pack('<q', 0)  # index size
        header += hashlib.sha256(b'').digest()[:20]  # hash
        header += b'\x00' * 205  # padding to 224 bytes
        return header

    def _build_pak_with_entries(self, entries, filename):
        """Собирает pak с записями"""
        body = b''
        index_entries = []
        
        for entry in entries:
            offset = len(self._build_pak_header()) + len(body)
            compressed = zlib.compress(entry['data'])
            
            index_entries.append({
                'path': entry['path'],
                'offset': offset,
                'size': len(entry['data']),
                'compressed_size': len(compressed),
            })
            body += compressed
        
        index = self._build_index(index_entries)
        header = self._build_pak_header()
        
        pak_data = header + body + index
        
        filepath = self.output / filename
        with open(filepath, 'wb') as f:
            f.write(pak_data)
        
        return filepath

    def _build_index(self, entries):
        """Построение индекса pak"""
        index = struct.pack('<I', len(entries))
        
        for entry in entries:
            path_bytes = entry['path'].encode('utf-8')
            index += struct.pack('<I', len(path_bytes))
            index += path_bytes
            index += struct.pack('<q', entry['offset'])
            index += struct.pack('<q', entry['size'])
            index += struct.pack('<q', entry['compressed_size'])
        
        return index

    def _generate_esp_material(self):
        """Генерирует материал для подсветки врагов (упрощённый uasset)"""
        # Это упрощённая заглушка структуры uasset
        # В реальности нужен полный UE4 asset parser
        material_data = b''
        
        # Package header
        material_data += struct.pack('<I', 0x9E2A83C1)  # UE4 package magic
        material_data += struct.pack('<I', 8)  # version
        material_data += struct.pack('<I', 0)  # flags
        
        # Name table
        names = ["None", "Root", "CharacterOutline", "Material", 
                 "PostProcess", "OutlineColor", "Red", "Opacity"]
        material_data += struct.pack('<I', len(names))
        for name in names:
            material_data += struct.pack('<I', len(name))
            material_data += name.encode('utf-8')
        
        # Материал — красная обводка с opacity 0.8
        material_data += struct.pack('<ffff', 1.0, 0.0, 0.0, 0.8)
        
        return material_data


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='full', choices=['full', 'grass', 'esp'])
    args = parser.parse_args()
    
    builder = PakBuilder()
    
    if args.mode in ('full', 'grass'):
        builder.create_no_grass_pak()
        builder.create_reduced_fog_pak()
    
    if args.mode in ('full', 'esp'):
        builder.create_esp_pak()
    
    print("[+] Build complete. Output in ./output/")
