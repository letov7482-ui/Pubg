import os
import hashlib
import struct
import shutil
from pathlib import Path
from datetime import datetime

class AntiBan:
    """Анти-детект: маскировка файлов, очистка метаданных, контроль отпечатков"""

    # Известные пути сканирования античита
    DETECTION_PATHS = [
        "Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/",
        "Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs/",
        "Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Config/",
    ]

    def __init__(self, output_dir="output"):
        self.output = Path(output_dir)
        self.output.mkdir(exist_ok=True)

    def sign_pak(self, filepath):
        """
        Подписывает pak файл корректным хешем.
        Античит проверяет SHA-1 от содержимого + размер.
        Генерируем валидную подпись.
        """
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Вычисляем SHA-1
        sha1 = hashlib.sha1(data).digest()
        
        # Записываем хеш в конец файла (последние 20 байт)
        # Если файл больше 20 байт — заменяем
        with open(filepath, 'r+b') as f:
            f.seek(-20, 2)  # последние 20 байт
            f.write(sha1)
        
        print(f"  [+] Signed: {filepath.name}")

    def generate_fake_manifest(self, pak_files):
        """
        Генерирует фальшивый манифест, чтобы античит
        считал файлы легитимными DLC/патчами.
        """
        manifest = {
            "version": "3.4.0",
            "build": datetime.now().strftime("%Y%m%d"),
            "files": []
        }
        
        for pak in pak_files:
            with open(pak, 'rb') as f:
                data = f.read()
            
            manifest["files"].append({
                "name": pak.name,
                "size": len(data),
                "md5": hashlib.md5(data).hexdigest(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "type": "patch",
                "priority": 1000,  # высокий приоритет загрузки
                "compressed": True,
                "encrypted": False
            })
        
        manifest_path = self.output / "manifest.json"
        with open(manifest_path, 'w') as f:
            import json
            json.dump(manifest, f, indent=2)
        
        return manifest_path

    def generate_cleanup_script(self):
        """
        ADB-скрипт для очистки следов после сессии.
        Удаляет логи и временные файлы которые может прочитать античит.
        """
        cleanup = """#!/bin/bash
# PUBG Mobile trace cleanup
# Запускать после каждой игровой сессии

echo "[*] Cleaning PUBG Mobile traces..."

# Удаление логов
rm -rf /storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs/*
rm -rf /storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Crashes/*

# Очистка временных файлов античита
rm -rf /storage/emulated/0/Android/data/com.tencent.ig/files/.tp/
rm -rf /storage/emulated/0/Android/data/com.tencent.ig/cache/

# Удаление метаданных сессии
rm -f /storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/*.log
rm -f /storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/*.tmp

# Сброс времени доступа к mod файлам
touch /storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/*.pak

echo "[+] Cleanup complete."
"""
        
        script_path = self.output / "cleanup.sh"
        with open(script_path, 'w') as f:
            f.write(cleanup)
        os.chmod(script_path, 0o755)
        
        return script_path

    def generate_safe_install_script(self):
        """
        ADB-скрипт для безопасной установки модов.
        Правильные права, скрытие от обнаружения.
        """
        install = """#!/bin/bash
# PUBG Mobile safe mod installer
# Устанавливает моды с правильными правами доступа

PAK_DIR="/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks"

echo "[*] Installing PUBG Mobile mods..."

# Создание директории если не существует
adb shell mkdir -p $PAK_DIR

# Копирование мод файлов
echo "[+] Copying no_grass.pak..."
adb push output/no_grass.pak $PAK_DIR/

echo "[+] Copying esp_highlight.pak..."
adb push output/esp_highlight.pak $PAK_DIR/

echo "[+] Copying no_fog.pak..."
adb push output/no_fog.pak $PAK_DIR/

echo "[+] Copying manifest..."
adb push output/manifest.json $PAK_DIR/

# Установка прав
adb shell chmod 644 $PAK_DIR/*.pak
adb shell chmod 644 $PAK_DIR/manifest.json

# Установка timestamps для маскировки
adb shell touch -t 202401010000 $PAK_DIR/*.pak

echo "[+] Installation complete."
echo "[!] Restart PUBG Mobile to apply changes."
"""
        
        script_path = self.output / "install.sh"
        with open(script_path, 'w') as f:
            f.write(install)
        os.chmod(script_path, 0o755)
        
        return script_path

    def pad_pak_files(self):
        """
        Добавляет паддинг к pak файлам чтобы они совпадали
        по размеру с оригиналами (античит проверяет размер).
        """
        # Известные размеры оригинальных pak файлов
        expected_sizes = {
            "no_grass.pak": 1024,
            "esp_highlight.pak": 2048,
            "no_fog.pak": 512,
        }
        
        for filename, size in expected_sizes.items():
            filepath = self.output / filename
            if filepath.exists():
                current_size = filepath.stat().st_size
                if current_size < size:
                    with open(filepath, 'ab') as f:
                        f.write(b'\x00' * (size - current_size))
                    print(f"  [+] Padded {filename} to {size} bytes")

    def obfuscate_filenames(self):
        """
        Переименовывает файлы в формат, похожий на официальные патчи.
        Античит ищет файлы с подозрительными именами.
        """
        renames = {
            "no_grass.pak": "pacth_ui_font_fix_2841.pak",
            "esp_highlight.pak": "pacth_material_patch_9712.pak", 
            "no_fog.pak": "pacth_weather_fix_5533.pak",
        }
        
        for old_name, new_name in renames.items():
            old_path = self.output / old_name
            new_path = self.output / new_name
            if old_path.exists():
                shutil.copy2(old_path, new_path)
                print(f"  [+] Renamed: {old_name} -> {new_name}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean', action='store_true')
    args = parser.parse_args()
    
    ab = AntiBan()
    ab.pad_pak_files()
    ab.obfuscate_filenames()
    
    pak_files = [
        ab.output / "pacth_ui_font_fix_2841.pak",
        ab.output / "pacth_material_patch_9712.pak",
        ab.output / "pacth_weather_fix_5533.pak",
    ]
    
    for pak in pak_files:
        if pak.exists():
            ab.sign_pak(pak)
    
    ab.generate_fake_manifest([p for p in pak_files if p.exists()])
    ab.generate_cleanup_script()
    ab.generate_safe_install_script()
    
    print("[+] Anti-ban setup complete.")
