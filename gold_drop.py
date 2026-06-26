import pygame
import math

# ================================================================================================
# CLASS GOLDDROP — Vàng rơi từ quái, tự động hút về player khi đến gần
# ================================================================================================

class GoldDrop:
    PICKUP_RADIUS  = 60   # Phạm vi bắt đầu hút về player (px)
    COLLECT_RADIUS = 15   # Phạm vi kích hoạt nhặt (px)
    MAGNET_SPEED   = 5.0  # Tốc độ hút về player

    def __init__(self, x, y, value=10):
        """
        x, y: vị trí rơi (world coordinates)
        value: số vàng nhận được khi nhặt
        """
        self.x = float(x)
        self.y = float(y)
        self.value = value
        self.collected = False  # Đã nhặt xong
        
        # Trạng thái: falling (rơi) → collecting (hiệu ứng nhặt)
        self.state = "falling"
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_duration = 50  # 50ms mỗi frame
        
        # Scale cho 2 loại sprite
        self.scale_falling = 2.0   # gold01: vàng xoay khi rơi
        self.scale_collect = 3.0   # gold02: hiệu ứng khi nhặt
        
        # Frame cho 2 trạng thái
        self.falling_frames = []   # 10 frame vàng xoay
        self.collect_frames = []   # 5 frame hiệu ứng nhặt
        self._load_frames()
        
        self.current_sprite = self.falling_frames[0] if self.falling_frames else None
        
        # Vật lý rơi: bounce nhẹ khi chạm đất
        self._bounce_vy = -3.0   # Vận tốc ban đầu (hướng lên)
        self._gravity = 0.3      # Gia tốc trọng lực
        self._on_ground = False  # Đã chạm đất
        
        # Lưu vị trí player khi nhặt để hiệu ứng bám theo
        self.target_player = None
        self.offset_x = 0  # Offset giữa vàng và player
        self.offset_y = 0

    # Load 10 frame vàng xoay (gold01) + 5 frame hiệu ứng nhặt (gold02)
    def _load_frames(self):
        for i in range(1, 11):
            img = pygame.image.load(f"assets/gold/gold01/gold{i}.png").convert_alpha()
            new_width = int(img.get_width() * self.scale_falling)
            new_height = int(img.get_height() * self.scale_falling)
            img = pygame.transform.scale(img, (new_width, new_height))
            self.falling_frames.append(img)
        
        for i in range(1, 6):
            img = pygame.image.load(f"assets/gold/gold02/gold_efect{i}.png").convert_alpha()
            new_width = int(img.get_width() * self.scale_collect)
            new_height = int(img.get_height() * self.scale_collect)
            img = pygame.transform.scale(img, (new_width, new_height))
            self.collect_frames.append(img)

    # Cập nhật animation theo trạng thái, trả về True nếu đã nhặt xong
    def _update_animation(self):
        if not self.current_sprite:
            return False
        current_time = pygame.time.get_ticks()
        
        # Falling: loop 10 frame vàng xoay
        if self.state == "falling":
            if current_time - self.frame_timer >= self.frame_duration:
                self.frame_timer = current_time
                self.current_frame = (self.current_frame + 1) % len(self.falling_frames)
                self.current_sprite = self.falling_frames[self.current_frame]
                self.offset_y += 50

        # Collecting: chạy 1 lần 5 frame rồi biến mất
        elif self.state == "collecting":
            if current_time - self.frame_timer >= self.frame_duration:
                self.frame_timer = current_time
                self.current_frame += 1
                if self.current_frame < len(self.collect_frames):
                    self.current_sprite = self.collect_frames[self.current_frame]
                else:
                    self.collected = True  # Xong → xóa
                    return True
        return False

    # Cập nhật vị trí: rơi → hút về player → nhặt
    def update(self, player):
        if self.collected:
            return
        if self._update_animation():
            return
        
        if self.state == "falling":
            # Vật lý rơi: bounce nhẹ
            if not self._on_ground:
                self._bounce_vy += self._gravity
                self.y += self._bounce_vy
                if self._bounce_vy >= 0 and self._bounce_vy < self._gravity * 2:
                    self._on_ground = True
                    self._bounce_vy = 0
            
            # Hút về player nếu trong phạm vi PICKUP_RADIUS
            px = player.x + player.width // 2
            py = player.y + player.height // 2
            dist = math.hypot(self.x - px, self.y - py)
            if dist < self.PICKUP_RADIUS and dist > 0:
                ratio = self.MAGNET_SPEED / dist
                self.x += (px - self.x) * ratio
                self.y += (py - self.y) * ratio
            
            # Trong phạm vi COLLECT_RADIUS → bắt đầu hiệu ứng nhặt
            if dist < self.COLLECT_RADIUS:
                self.state = "collecting"
                self.current_frame = -1
                self.frame_timer = pygame.time.get_ticks()
                player.gold += self.value  # Cộng vàng ngay
                # Lưu vị trí player để hiệu ứng bám theo
                self.target_player = player
                self.offset_x = self.x - (player.x + player.width // 2)
                self.offset_y = self.y - (player.y + player.height // 2)
        
        # Collecting: hiệu ứng bám theo player
        elif self.state == "collecting" and self.target_player:
            px = self.target_player.x + self.target_player.width // 2
            py = self.target_player.y + self.target_player.height // 2
            self.x = px + self.offset_x
            self.y = py + self.offset_y

    # Vẽ vàng (trừ camera)
    def draw(self, screen, camera):
        if self.collected and self.state != "collecting":
            return
        if not self.current_sprite:
            return
        sx = int(self.x - camera.x - self.current_sprite.get_width() // 2)
        sy = int(self.y - camera.y - self.current_sprite.get_height() // 2)
        screen.blit(self.current_sprite, (sx, sy))