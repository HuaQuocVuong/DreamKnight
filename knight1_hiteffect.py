import pygame
import os

# ================================================================================================
# MODULE KNIGHT1_HITEFFECT — Hiệu ứng animation khi tấn công trúng kẻ địch
# Load 7 frame từ assets/effect_attack02/frame0001.png ... frame0007.png
# ================================================================================================


# Load 7 frame hiệu ứng hit, cache lại để tránh load nhiều lần
def load_hit_frames():
    frames = []
    for i in range(1, 8):  # frame0001 → frame0007
        path = os.path.join("assets", "effect_attack02", f"frame{i:04d}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            frames.append(img)
        except FileNotFoundError:
            print(f"⚠️ Không tìm thấy file: {path}")
            # Placeholder vàng nếu thiếu ảnh
            placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(placeholder, (255, 220, 0, 180), (32, 32), 28)
            frames.append(placeholder)
    return frames


# Cache toàn cục — load 1 lần, dùng nhiều lần
_cached_hit_frames = None

def get_hit_frames():
    global _cached_hit_frames
    if _cached_hit_frames is None:
        _cached_hit_frames = load_hit_frames()
    return _cached_hit_frames


# ================================================================================================
# CLASS HITEFFECT — 1 hiệu ứng hit đang phát tại 1 vị trí, tự hủy khi xong
# ================================================================================================

class HitEffect:
    def __init__(self, x, y, frame_duration=40):
        """
        x, y: tọa độ tâm hiệu ứng (world coordinates)
        frame_duration: thời gian mỗi frame (ms), mặc định 40ms → tổng ~280ms
        """
        self.frames = get_hit_frames()
        self.frame_duration = frame_duration
        self.current_frame_index = 0
        self.last_update_time = pygame.time.get_ticks()
        self.is_done = False  # True khi animation kết thúc

        self.x = x  # Tọa độ world X
        self.y = y  # Tọa độ world Y

    # Chuyển frame sau mỗi frame_duration ms, đánh dấu done khi hết
    def update(self):
        if self.is_done:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time >= self.frame_duration:
            self.last_update_time = current_time
            self.current_frame_index += 1
            if self.current_frame_index >= len(self.frames):
                self.is_done = True

    # Vẽ frame hiện tại, căn giữa tại vị trí world (có trừ camera)
    def draw(self, screen, camera):
        if self.is_done:
            return

        frame = self.frames[self.current_frame_index]
        frame_w = frame.get_width()
        frame_h = frame.get_height()

        draw_x = self.x - frame_w // 2 - camera.x
        draw_y = self.y - frame_h // 2 - camera.y

        screen.blit(frame, (draw_x, draw_y))


# ================================================================================================
# CLASS HITEFFECTMANAGER — Quản lý tất cả HitEffect đang hoạt động
# ================================================================================================

class HitEffectManager:
    def __init__(self):
        self.effects = []  # Danh sách HitEffect đang chạy

    # Tạo hiệu ứng hit mới tại vị trí (x, y)
    def spawn(self, x, y, frame_duration=40):
        effect = HitEffect(x, y, frame_duration)
        self.effects.append(effect)

    # Cập nhật tất cả hiệu ứng, xóa cái đã done
    def update(self):
        for effect in self.effects:
            effect.update()
        self.effects = [e for e in self.effects if not e.is_done]

    # Vẽ tất cả hiệu ứng đang chạy
    def draw(self, screen, camera):
        for effect in self.effects:
            effect.draw(screen, camera)