import pygame

# ================================================================================================
# MODULE QUẢN LÝ ÂM THANH TOÀN CỤC
# ================================================================================================

# Danh sách sound effect đã đăng ký — để cập nhật volume đồng loạt
_sfx_sounds   = []

# Volume mặc định 50%
_music_volume = 0.5  # Nhạc nền
_sfx_volume   = 0.5  # Hiệu ứng âm thanh

# Danh sách voice NPC (tách riêng để có thể quản lý độc lập sau này)
_npc_voices   = []

# Đăng ký sound effect vào hệ thống, tự động áp dụng volume hiện tại
def register_sound(sound):
    _sfx_sounds.append(sound)
    sound.set_volume(_sfx_volume)

# Đăng ký voice NPC, hiện dùng chung volume với SFX
def register_npc_voice(voice):
    _npc_voices.append(voice)
    voice.set_volume(_sfx_volume)

# Điều chỉnh volume nhạc nền (0.0 - 1.0)
def set_music_volume(volume):
    global _music_volume
    _music_volume = max(0.0, min(1.0, volume))  # Clamp [0, 1]
    pygame.mixer.music.set_volume(_music_volume)

# Điều chỉnh volume tất cả SFX và voice NPC (0.0 - 1.0)
def set_sfx_volume(volume):
    global _sfx_volume
    _sfx_volume = max(0.0, min(1.0, volume))  # Clamp [0, 1]
    
    # Cập nhật toàn bộ sound effect đã đăng ký
    for sound in _sfx_sounds:
        try:
            sound.set_volume(_sfx_volume)
        except:
            pass  # Bỏ qua nếu sound đã bị giải phóng
    
    # Cập nhật toàn bộ voice NPC
    for voice in _npc_voices:
        try:
            voice.set_volume(_sfx_volume)
        except:
            pass

# Trả về volume nhạc nền hiện tại
def get_music_volume():
    return _music_volume

# Trả về volume SFX hiện tại
def get_sfx_volume():
    return _sfx_volume

# Tự động đăng ký mọi pygame.mixer.Sound được tạo ra trong game
# Nhờ vậy không cần sửa từng file quái, NPC, v.v.
_original_sound = pygame.mixer.Sound

class _AutoSound(_original_sound):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        register_sound(self)

pygame.mixer.Sound = _AutoSound