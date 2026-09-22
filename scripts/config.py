# PUBG Mobile Mod Configuration

# Пути на устройстве
DEVICE_PATHS = {
    "paks": "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks/",
    "obb": "/storage/emulated/0/Android/obb/com.tencent.ig/",
    "data": "/storage/emulated/0/Android/data/com.tencent.ig/",
    "config": "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Config/",
}

# ESP настройки
ESP_CONFIG = {
    "enabled": True,
    "outline_color": (1.0, 0.0, 0.0, 0.9),      # красный, 90% непрозрачность
    "outline_width": 2.0,
    "through_walls": True,
    "render_distance": 1000.0,
    "depth_priority": -1.0,  # рендер поверх геометрии
}

# Настройки окружения
WORLD_CONFIG = {
    "remove_grass": True,
    "remove_fog": True,
    "reduce_foliage": True,
}

# Анти-детект
ANTIBAN_CONFIG = {
    "sign_paks": True,
    "pad_files": True,
    "obfuscate_names": True,
    "fake_manifest": True,
    "cleanup_logs": True,
    "spoof_timestamps": True,
    "backup_originals": True,
}

# Имена для обфускации
FAKE_NAMES = {
    "no_grass.pak": "pacth_ui_font_fix_2841.pak",
    "esp_highlight.pak": "pacth_material_patch_9712.pak",
    "no_fog.pak": "pacth_weather_fix_5533.pak",
}
