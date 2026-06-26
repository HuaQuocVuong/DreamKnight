from typing import Self
import math
import pygame
from config import PLAYER_SPEED, RUN_SPEED, DEBUG_MODE
from knight1_hiteffect import HitEffectManager
import sound_manager
from knight1_animation import (
    Animation, load_idle_frames, load_walk_frames, load_run_frames, 
    load_attack_idle_frames, load_attack_walk_frames, load_attack_run_frames,
    load_dash_frames,
    load_hit_frames  # Animation khi bị đánh
)


# ================================================================================================
# CLASS PLAYER1 — Nhân vật chính (hiệp sĩ)
# Quản lý: di chuyển, tấn công, dash, hit, animation, máu, vàng, ghost mode
# ================================================================================================

class Player1(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # KHỞI TẠO CÁC BỘ ANIMATION THEO HƯỚNG
        # Idle: đứng yên (200-500ms/frame tùy hướng)
        self.idle_animations = {
            "up": Animation(load_idle_frames("up"), frame_duration=500),
            "down": Animation(load_idle_frames("down"), frame_duration=200), 
            "left": Animation(load_idle_frames("left"), frame_duration=200),
            "right": Animation(load_idle_frames("right"), frame_duration=500),
        }
        
        # Walk: đi bộ (100ms/frame)
        self.walk_animations = {
            "up": Animation(load_walk_frames("up")),
            "down": Animation(load_walk_frames("down")), 
            "left": Animation(load_walk_frames("left")),
            "right": Animation(load_walk_frames("right")),
        }
        
        # Run: chạy (80ms/frame)
        self.run_animations = {
            "up": Animation(load_run_frames("up"), frame_duration=80),
            "down": Animation(load_run_frames("down"), frame_duration=80), 
            "left": Animation(load_run_frames("left"), frame_duration=80),
            "right": Animation(load_run_frames("right"), frame_duration=80),
        }
        
        # Attack khi đứng yên (60ms/frame)
        self.attack_idle_animations = {
            "up": Animation(load_attack_idle_frames("up"), frame_duration=60),
            "down": Animation(load_attack_idle_frames("down"), frame_duration=60), 
            "left": Animation(load_attack_idle_frames("left"), frame_duration=60),
            "right": Animation(load_attack_idle_frames("right"), frame_duration=60),
        }
        
        # Attack khi đi bộ (60ms/frame)
        self.attack_walk_animations = {
            "up": Animation(load_attack_walk_frames("up"), frame_duration=60),
            "down": Animation(load_attack_walk_frames("down"), frame_duration=60), 
            "left": Animation(load_attack_walk_frames("left"), frame_duration=60),
            "right": Animation(load_attack_walk_frames("right"), frame_duration=60),
        }
        
        # Attack khi chạy (50ms/frame — nhanh nhất)
        self.attack_run_animations = {
            "up": Animation(load_attack_run_frames("up"), frame_duration=50),
            "down": Animation(load_attack_run_frames("down"), frame_duration=50), 
            "left": Animation(load_attack_run_frames("left"), frame_duration=50),
            "right": Animation(load_attack_run_frames("right"), frame_duration=50),
        }
        
        # Dash: lướt nhanh (40ms/frame)
        self.dash_animations = {
            "up": Animation(load_dash_frames("up"), frame_duration=40),
            "down": Animation(load_dash_frames("down"), frame_duration=40),
            "left": Animation(load_dash_frames("left"), frame_duration=40),
            "right": Animation(load_dash_frames("right"), frame_duration=40),
        }

        # Hit: bị đánh trúng (100ms/frame)
        self.hit_animations = {
            "up": Animation(load_hit_frames("up"), frame_duration=100),
            "down": Animation(load_hit_frames("down"), frame_duration=100),
            "left": Animation(load_hit_frames("left"), frame_duration=100),
            "right": Animation(load_hit_frames("right"), frame_duration=100),
        }

        # KHỞI TẠO ÂM THANH
        pygame.mixer.init()
        # 4 âm thanh tấn công (luân phiên)
        self.attack_sound_1 = pygame.mixer.Sound("03_sounds/attack/Sword1.mp3")
        self.attack_sound_2 = pygame.mixer.Sound("03_sounds/attack/Sword2.mp3")
        self.attack_sound_3 = pygame.mixer.Sound("03_sounds/attack/Sword3.mp3")
        self.attack_sound_4 = pygame.mixer.Sound("03_sounds/attack/Sword4.mp3")
        
        # Âm thanh dash
        self.dash_sound = pygame.mixer.Sound("03_sounds/dash/dash03.mp3")
        
        # Âm thanh khi bị đánh
        self.hit_sound = pygame.mixer.Sound("03_sounds/Hk Stun 01.mp3")

        # Danh sách âm thanh tấn công để luân phiên
        self.attack_sounds = [
            self.attack_sound_1,
            self.attack_sound_2,
            self.attack_sound_3,
            self.attack_sound_4,
        ]
        
        self.current_attack_sound_index = 0

        # Đăng ký tất cả sound vào SoundManager để quản lý volume tập trung
        for s in self.attack_sounds:
            sound_manager.register_sound(s)
        sound_manager.register_sound(self.dash_sound)
        sound_manager.register_sound(self.hit_sound)

        # BIẾN TRẠNG THÁI CỦA PLAYER
        self.direction = "down"          # Hướng hiện tại
        self.is_running = False          # Đang chạy (shift)
        self.is_attacking = False        # Đang tấn công
        self.attack_start_time = 0       # Thời điểm bắt đầu tấn công
        self.attack_duration = 300       # Thời gian animation tấn công (ms)
        self.sound_played_for_this_attack = False  # Đã phát âm thanh chưa
        
        # Trạng thái hit (bị đánh)
        self.is_hit = False              # Đang trong trạng thái bị đánh
        self.hit_start_time = 0          # Thời điểm bắt đầu bị đánh
        self.hit_duration = 300          # Thời gian dính đòn (ms)
        self.hit_knockback_distance = 30 # Khoảng cách bị đẩy lùi (px)
        self.hit_knockback_speed = 0     # Tốc độ đẩy lùi (px/ms)
        self.hit_start_x = 0             # Vị trí bắt đầu bị đẩy
        self.hit_start_y = 0
        self.hit_target_x = 0            # Vị trí đích sau khi bị đẩy
        self.hit_target_y = 0
        self.hit_direction_vector = (0, 0)  # Hướng đẩy (dx, dy)
        
        # Toggle run: nhấn shift 1 lần để bật/tắt chạy
        self.run_mode = False            # Chế độ chạy đang bật
        self.shift_just_pressed = False  # Shift vừa được nhấn (tránh toggle liên tục)
        
        # Dash: lướt nhanh về phía trước
        self.is_dashing = False          # Đang dash
        self.dash_start_time = 0         # Thời điểm bắt đầu dash
        self.dash_duration = 150         # Thời gian dash (ms)
        self.dash_distance = 100         # Khoảng cách dash (px)
        self.dash_start_x = 0            # Vị trí bắt đầu dash
        self.dash_start_y = 0
        self.dash_target_x = 0           # Vị trí đích dash
        self.dash_target_y = 0
        self.dash_cooldown = 500         # Thời gian hồi dash (ms)
        self.last_dash_time = 0          # Thời điểm dash cuối cùng
        self.dash_direction = "down"     # Hướng dash
        
        # Kích thước sprite khi dash (rộng hơn bình thường)
        self.dash_sprite_sizes = {
            "left": (63, 32),
            "right": (63, 32),
            "up": (32, 63),
            "down": (32, 63)
        }
        
        # HÌNH ẢNH VÀ VỊ TRÍ
        self.image = self.idle_animations[self.direction].current_frame
        self.rect = self.image.get_rect(center=(x, y))

        self.x = x
        self.y = y

        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # Hitbox thu nhỏ (nhỏ hơn sprite để cảm giác chính xác hơn)
        self.hitbox_width = 30
        self.hitbox_height = 50
        self.hitbox_offset_x = 45  # Offset từ góc trái sprite
        self.hitbox_offset_y = 40  # Offset từ góc trên sprite

        self.dx = 0  # Vận tốc X
        self.dy = 0  # Vận tốc Y
        
        self.debug = DEBUG_MODE
        self.attack_hitbox = None  # Hitbox tấn công (tạo khi attack)

        # HỆ THỐNG MÁU VÀ TIỀN
        self.health = 100
        self.max_health = 100
        self.gold = 0
        self.is_dead = False
        
        # Ghost mode: bất tử tạm thời sau khi bị đánh (1.5s)
        self.ghost_mode = False
        self.ghost_start_time = 0
        self.ghost_duration = 1500  # 1.5 giây
        self.ghost_alpha = 100      # Độ mờ khi ghost mode
        self.ghost_flicker = False  # Hiệu ứng nhấp nháy (0.5s cuối)

        # Chỉ số tấn công
        self.damage = 1500000000000             # Sát thương cơ bản
        self.attack_range = 60       # Phạm vi tấn công
        self.attack_damage_level = 0 # Cấp nâng cấp damage
        self.attack_speed_level = 0  # Cấp nâng cấp tốc độ đánh
        self.dash_upgrade_level = 0  # Cấp nâng cấp dash
        self.range_upgrade_level = 0 # Cấp nâng cấp phạm vi
        self.has_dealt_damage = False  # Đã gây sát thương trong lần attack này
        self.damage_cooldown = 400    # Thời gian giữa các lần gây sát thương (ms)
        self.last_damage_time = 0     # Thời điểm gây sát thương cuối
        self.enemies = None           # Danh sách enemy (gán từ game)
        
        # Hiệu ứng hit (vết chém khi đánh trúng)
        self.hit_effect_manager = HitEffectManager()

    # Kích hoạt trạng thái bị đánh
    def trigger_hit(self, damage, knockback_direction=None):
        if self.is_dead or self.is_dashing:
            return
        
        # Bật ghost mode ngay khi bị đánh
        self.ghost_mode = True
        self.ghost_start_time = pygame.time.get_ticks()
        print("🛡️ Player kích hoạt ghost mode - bất tử 1.5s!")
        
        # Trừ máu
        self.health = max(0, self.health - damage)
        print(f"💥 Player nhận {damage} sát thương! Máu còn: {self.health}/{self.max_health}")
        
        # Phát âm thanh hit
        try:
            self.hit_sound.play()
        except:
            pass
        
        # Kiểm tra chết
        if self.health <= 0:
            self.is_dead = True
            print("💀 Player đã chết!")
            return
        
        # Bắt đầu animation hit
        self.is_hit = True
        self.hit_start_time = pygame.time.get_ticks()
        self.hit_animations[self.direction].reset()
        
        # Tạo hiệu ứng hit (vết chém)
        self.hit_effect_manager.spawn(self.x + self.width//2, self.y + self.height//2)
        
        # Xử lý knockback (đẩy lùi)
        if knockback_direction:
            # Dùng hướng được chỉ định
            dx, dy = knockback_direction
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length
            else:
                dx, dy = 0, 0
        else:
            # Tự động đẩy lùi ngược hướng đang đối mặt
            if self.direction == "up":
                dx, dy = 0, 1
            elif self.direction == "down":
                dx, dy = 0, -1
            elif self.direction == "left":
                dx, dy = 1, 0
            else:  # right
                dx, dy = -1, 0
        
        # Lưu hướng đẩy
        self.hit_direction_vector = (dx, dy)
        
        # Tính vị trí đích sau khi đẩy
        self.hit_start_x = self.x
        self.hit_start_y = self.y
        self.hit_target_x = self.x + dx * self.hit_knockback_distance
        self.hit_target_y = self.y + dy * self.hit_knockback_distance
        
        # Giới hạn trong map
        from config import MAP_WIDTH, MAP_HEIGHT
        self.hit_target_x = max(0, min(self.hit_target_x, MAP_WIDTH - self.width))
        self.hit_target_y = max(0, min(self.hit_target_y, MAP_HEIGHT - self.height))
        
        # Tốc độ đẩy (px/ms)
        self.hit_knockback_speed = self.hit_knockback_distance / self.hit_duration

    # Cập nhật trạng thái hit (gọi mỗi frame khi đang hit)
    def update_hit(self, map_width, map_height):
        if not self.is_hit:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.hit_start_time
        
        # Kết thúc hit
        if elapsed >= self.hit_duration:
            self.is_hit = False
            self.hit_direction_vector = (0, 0)
            return
        
        # Cập nhật animation hit
        self.hit_animations[self.direction].update()
        
        # Nội suy vị trí đẩy lùi (ease-out: nhanh đầu, chậm cuối)
        progress = elapsed / self.hit_duration
        eased_progress = 1 - (1 - progress) ** 2
        
        new_x = self.hit_start_x + (self.hit_target_x - self.hit_start_x) * eased_progress
        new_y = self.hit_start_y + (self.hit_target_y - self.hit_start_y) * eased_progress
        
        # Áp dụng vị trí mới (giới hạn map)
        self.x = max(0, min(new_x, map_width - self.width))
        self.y = max(0, min(new_y, map_height - self.height))
        self.rect.x = self.x
        self.rect.y = self.y

    # Cập nhật ghost mode (bất tử tạm thời)
    def update_ghost_mode(self):
        if not self.ghost_mode:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Hết thời gian ghost mode
        if current_time - self.ghost_start_time >= self.ghost_duration:
            self.ghost_mode = False
            print("👻 Hết ghost mode! Trở lại bình thường.")
            return
        
        # Nhấp nháy trong 0.5s cuối (tần số 10Hz)
        remaining = self.ghost_duration - (current_time - self.ghost_start_time)
        if remaining < 500:
            self.ghost_flicker = (current_time // 100) % 2 == 0
        else:
            self.ghost_flicker = False

    # Xử lý input từ bàn phím và chuột
    def handle_input(self, events):
        # Khi đang hit: chỉ cho phép dash để thoát
        if self.is_hit:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Chuột phải
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_dash_time >= self.dash_cooldown:
                        self.is_hit = False  # Dash phá vỡ trạng thái hit
                        self.start_dash()
            return
        
        keys = pygame.key.get_pressed()
        
        # Toggle run: nhấn shift 1 lần để bật/tắt
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if not self.shift_just_pressed:
                self.run_mode = not self.run_mode
                self.shift_just_pressed = True
        else:
            self.shift_just_pressed = False
        
        # Dash: chuột phải
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_dash_time >= self.dash_cooldown:
                    self.start_dash()
        
        # Nếu đang dash, không xử lý di chuyển
        if self.is_dashing:
            return
        
        # Di chuyển WASD (chỉ khi không tấn công)
        if not self.is_attacking:
            dx_raw = (keys[pygame.K_d] - keys[pygame.K_a])  # Phải - Trái
            dy_raw = (keys[pygame.K_s] - keys[pygame.K_w])  # Xuống - Lên

            if dx_raw != 0 or dy_raw != 0:
                # Chuẩn hóa vector di chuyển
                length = max((dx_raw**2 + dy_raw**2) ** 0.5, 0.1)
                
                if self.run_mode:
                    self.dx = (dx_raw / length) * RUN_SPEED
                    self.dy = (dy_raw / length) * RUN_SPEED
                    self.is_running = True
                else:
                    self.dx = (dx_raw / length) * PLAYER_SPEED
                    self.dy = (dy_raw / length) * PLAYER_SPEED
                    self.is_running = False

                # Cập nhật hướng
                if dx_raw != 0:
                    self.direction = "right" if dx_raw > 0 else "left"
                else:
                    self.direction = "down" if dy_raw > 0 else "up"
            else:
                # Đứng yên
                self.dx = 0
                self.dy = 0
                self.is_running = False

        # Tấn công: chuột trái (không attack khi dash hoặc hit)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.is_attacking and not self.is_dashing and not self.is_hit:
                    self.start_attack()
    
    # Phát âm thanh tấn công luân phiên 4 file
    def play_next_attack_sound(self):
        self.attack_sounds[self.current_attack_sound_index].play()
        self.current_attack_sound_index += 1
        if self.current_attack_sound_index >= len(self.attack_sounds):
            self.current_attack_sound_index = 0

    # Bắt đầu dash
    def start_dash(self):
        self.is_dashing = True
        self.is_attacking = False
        self.is_hit = False  # Dash ngắt trạng thái hit
        self.dash_start_time = pygame.time.get_ticks()
        self.last_dash_time = self.dash_start_time
        self.dash_direction = self.direction
        
        self.dash_animations[self.direction].reset()
        self.image = self.dash_animations[self.direction].current_frame
        
        try:
            self.dash_sound.play()
        except:
            pass
        
        self.dash_start_x = self.x
        self.dash_start_y = self.y
        
        # Tính vị trí đích dash
        dash_vec = self.get_dash_vector()
        self.dash_target_x = self.x + dash_vec[0] * self.dash_distance
        self.dash_target_y = self.y + dash_vec[1] * self.dash_distance
        
        self.create_dash_effect()
    
    # Vector đơn vị cho hướng dash
    def get_dash_vector(self):
        vectors = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        return vectors.get(self.dash_direction, (0, 1))
    
    # Tạo hiệu ứng dash (placeholder cho particle system)
    def create_dash_effect(self):
        pass
    
    # Cập nhật dash: nội suy vị trí và kiểm tra kết thúc
    def update_dash(self, map_width, map_height):
        if not self.is_dashing:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.dash_start_time
        progress = min(1.0, elapsed / self.dash_duration)
        
        # Ease-out: nhanh đầu, chậm cuối
        eased_progress = 1 - (1 - progress) ** 3
        
        new_x = self.dash_start_x + (self.dash_target_x - self.dash_start_x) * eased_progress
        new_y = self.dash_start_y + (self.dash_target_y - self.dash_start_y) * eased_progress
        
        # Giới hạn trong map
        self.x = max(0, min(new_x, map_width - self.width))
        self.y = max(0, min(new_y, map_height - self.height))
        self.rect.x = self.x
        self.rect.y = self.y
        
        self.dash_animations[self.dash_direction].update()
        
        # Kết thúc dash
        if progress >= 1.0:
            self.is_dashing = False
            self.reset_sprite_size()
    
    # Reset kích thước sprite sau dash
    def reset_sprite_size(self):
        pass

    # Bắt đầu tấn công
    def start_attack(self):
        self.is_attacking = True
        self.attack_start_time = pygame.time.get_ticks()
        self.sound_played_for_this_attack = False
        self.has_dealt_damage = False
        
        # Reset animation phù hợp với trạng thái di chuyển
        if self.is_running:
            self.attack_run_animations[self.direction].reset()
        elif self.dx != 0 or self.dy != 0:
            self.attack_walk_animations[self.direction].reset()
        else:
            self.attack_idle_animations[self.direction].reset()
        
        self.create_attack_hitbox()

    # Tạo hitbox cho đòn tấn công (thay đổi theo hướng)
    def create_attack_hitbox(self):
        hitbox_width_vertical = 80
        hitbox_height_vertical = 30
        hitbox_width_horizontal = 30
        hitbox_height_horizontal = 80
        
        # Cấu hình offset cho từng hướng
        offset_config = {
            "up":    {"offset_x": 0,  "offset_y": -25, "width": hitbox_width_vertical,   "height": hitbox_height_vertical},
            "down":  {"offset_x": 0,  "offset_y": 45,  "width": hitbox_width_vertical,   "height": hitbox_height_vertical},
            "left":  {"offset_x": -35, "offset_y": 5,  "width": hitbox_width_horizontal, "height": hitbox_height_horizontal},
            "right": {"offset_x": 40,  "offset_y": 5,  "width": hitbox_width_horizontal, "height": hitbox_height_horizontal}
        }
        
        config = offset_config[self.direction]
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        hitbox_x = center_x + config["offset_x"] - config["width"] // 2
        hitbox_y = center_y + config["offset_y"] - config["height"] // 2
        
        self.attack_hitbox = pygame.Rect(hitbox_x, hitbox_y, config["width"], config["height"])
    
    # Gây sát thương lên enemy trong vùng attack_hitbox
    def deal_damage_to_enemies(self):
        if not self.is_attacking or self.attack_hitbox is None:
            return
        
        current_time = pygame.time.get_ticks()
        # Kiểm tra cooldown giữa các lần gây sát thương
        if current_time - self.last_damage_time < self.damage_cooldown:
            return
        
        if self.enemies is None:
            return
        
        for enemy in self.enemies:
            if hasattr(enemy, 'is_dead') and enemy.is_dead:
                continue
            
            # Enemy có hitbox tròn
            if hasattr(enemy, 'get_hitbox'):
                enemy_hx, enemy_hy, enemy_hr = enemy.get_hitbox()
                enemy_hitbox_rect = pygame.Rect(enemy_hx - enemy_hr, enemy_hy - enemy_hr, enemy_hr * 2, enemy_hr * 2)
                
                if self.attack_hitbox.colliderect(enemy_hitbox_rect):
                    if hasattr(enemy, 'take_damage'):
                        enemy.take_damage(self.damage)
                        self.last_damage_time = current_time
                        print(f"⚔️ Player gây {self.damage} sát thương lên {enemy.__class__.__name__}!")
                        
                        # Hiệu ứng hit tại điểm va chạm
                        intersection = self.attack_hitbox.clip(enemy_hitbox_rect)
                        self.hit_effect_manager.spawn(intersection.centerx, intersection.centery)
                        break
            # Enemy dùng rect
            else:
                if hasattr(enemy, 'rect'):
                    if self.attack_hitbox.colliderect(enemy.rect):
                        if hasattr(enemy, 'take_damage'):
                            enemy.take_damage(self.damage)
                            self.last_damage_time = current_time
                            print(f"⚔️ Player gây {self.damage} sát thương lên {enemy.__class__.__name__}!")
                            self.hit_effect_manager.spawn(enemy.rect.centerx, enemy.rect.centery)
                            break

    # Gán danh sách enemy từ game
    def set_enemies(self, enemies):
        self.enemies = enemies

    # Nhận sát thương từ enemy
    def take_damage(self, damage, knockback_direction=None):
        if self.is_dead:
            return
        
        # Ghost mode: miễn sát thương
        if self.ghost_mode:
            print("🛡️ Player đang ghost mode - miễn sát thương!")
            return
        
        self.trigger_hit(damage, knockback_direction)

    # Cập nhật trạng thái tấn công
    def update_attack(self):
        if self.is_dashing or self.is_hit:
            return
            
        if self.is_attacking:
            current_time = pygame.time.get_ticks()
            
            # Phát âm thanh 1 lần khi bắt đầu attack
            if not self.sound_played_for_this_attack:
                self.play_next_attack_sound()
                self.sound_played_for_this_attack = True
            
            # Cập nhật animation phù hợp
            if self.is_running:
                self.attack_run_animations[self.direction].update()
            elif self.dx != 0 or self.dy != 0:
                self.attack_walk_animations[self.direction].update()
            else:
                self.attack_idle_animations[self.direction].update()
            
            # Gây sát thương sau 100ms
            attack_progress = current_time - self.attack_start_time
            if not self.has_dealt_damage and attack_progress > 100:
                self.has_dealt_damage = True
                self.deal_damage_to_enemies()
            
            # Kết thúc attack
            if current_time - self.attack_start_time >= self.attack_duration:
                self.is_attacking = False
                self.attack_hitbox = None
                self.has_dealt_damage = False

    # Giữ lại để tương thích (không dùng)
    def update_running_state(self):
        pass

    # Di chuyển nhân vật (có giới hạn map)
    def move(self, dx, dy, map_width, map_height):
        if self.is_dashing or self.is_hit:
            return
            
        # Giảm tốc khi đang tấn công
        if self.is_attacking:
            speed_multiplier = 0.3 if self.is_running else 0.1
        else:
            speed_multiplier = 1.0
            
        current_dx = dx * speed_multiplier
        current_dy = dy * speed_multiplier
        
        new_x = self.x + current_dx
        new_y = self.y + current_dy
        
        # Giới hạn trong map
        if 0 <= new_x <= map_width - self.width:
            self.x = new_x
        if 0 <= new_y <= map_height - self.height:
            self.y = new_y
            
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Cập nhật hitbox tấn công theo vị trí mới
        if self.is_attacking:
            self.create_attack_hitbox()

    # Update chính — gọi mỗi frame
    def update(self, map_width, map_height, events):
        # Cập nhật ghost mode
        self.update_ghost_mode()

        # Xử lý input
        self.handle_input(events)
        
        # Cập nhật dash
        self.update_dash(map_width, map_height)
        
        # Đang dash: chỉ cập nhật animation dash
        if self.is_dashing:
            self.dash_animations[self.dash_direction].update()
            self.image = self.dash_animations[self.dash_direction].current_frame
            return
        
        # Cập nhật hit
        self.update_hit(map_width, map_height)
        
        # Đang hit: chỉ cập nhật animation hit
        if self.is_hit:
            self.image = self.hit_animations[self.direction].current_frame
            self.hit_effect_manager.update()
            return
        
        # Trạng thái bình thường
        self.update_running_state()
        self.update_attack()
        self.move(self.dx, self.dy, map_width, map_height)
        self.hit_effect_manager.update()

        # Chọn animation phù hợp
        if self.is_attacking:
            if self.is_running:
                self.image = self.attack_run_animations[self.direction].current_frame
            elif self.dx != 0 or self.dy != 0:
                self.image = self.attack_walk_animations[self.direction].current_frame
            else:
                self.image = self.attack_idle_animations[self.direction].current_frame
        elif self.dx == 0 and self.dy == 0:
            self.idle_animations[self.direction].update()
            self.image = self.idle_animations[self.direction].current_frame
        else:
            if self.is_running:
                self.run_animations[self.direction].update()
                self.image = self.run_animations[self.direction].current_frame
            else:
                self.walk_animations[self.direction].update()
                self.image = self.walk_animations[self.direction].current_frame
    
    # Vẽ nhân vật + debug
    def draw(self, screen, camera):
        # Vẽ dash với sprite size đặc biệt
        if self.is_dashing:
            dash_width, dash_height = self.dash_sprite_sizes.get(self.dash_direction, (self.width, self.height))
            
            # Offset để canh chỉnh sprite dash
            dash_sprite_offset = {
                "left":  {"offset_x": 5,   "offset_y": 30},
                "right": {"offset_x": -70, "offset_y": 30},
                "up":    {"offset_x": 30,  "offset_y": 0},
                "down":  {"offset_x": 30,  "offset_y": -50}
            }
            
            offset = dash_sprite_offset.get(self.dash_direction, {"offset_x": 0, "offset_y": 0})
            
            if self.dash_direction in ["left", "right"]:
                offset_x = (self.width - dash_width) // 2
                screen_x = self.x - camera.x + offset_x + offset["offset_x"]
                screen_y = self.y - camera.y + offset["offset_y"]
            else:
                offset_y = (self.height - dash_height) // 2
                screen_x = self.x - camera.x + offset["offset_x"]
                screen_y = self.y - camera.y + offset_y + offset["offset_y"]
            
            screen.blit(self.image, (screen_x, screen_y))
            
            # Debug hitbox dash
            if DEBUG_MODE:
                current_time = pygame.time.get_ticks()
                elapsed = current_time - self.dash_start_time
                progress = min(1.0, elapsed / self.dash_duration)
                
                start_hitbox_x = self.dash_start_x + self.hitbox_offset_x
                start_hitbox_y = self.dash_start_y + self.hitbox_offset_y
                target_hitbox_x = self.dash_target_x + self.hitbox_offset_x
                target_hitbox_y = self.dash_target_y + self.hitbox_offset_y
                
                current_hitbox_x = start_hitbox_x + (target_hitbox_x - start_hitbox_x) * progress
                current_hitbox_y = start_hitbox_y + (target_hitbox_y - start_hitbox_y) * progress
                
                # Hitbox xanh (vị trí thực)
                green_hitbox_x = self.x + self.hitbox_offset_x - camera.x
                green_hitbox_y = self.y + self.hitbox_offset_y - camera.y
                pygame.draw.rect(screen, (0, 255, 0), (green_hitbox_x, green_hitbox_y, self.hitbox_width, self.hitbox_height), 2)
                
                # Hitbox vàng (nội suy)
                pygame.draw.rect(screen, (255, 255, 0), (current_hitbox_x - camera.x, current_hitbox_y - camera.y, self.hitbox_width, self.hitbox_height), 2)
                
                # Đường từ start đến target
                start_screen_x = start_hitbox_x - camera.x
                start_screen_y = start_hitbox_y - camera.y
                target_screen_x = target_hitbox_x - camera.x
                target_screen_y = target_hitbox_y - camera.y
                pygame.draw.line(screen, (255, 0, 255), (start_screen_x, start_screen_y), (target_screen_x, target_screen_y), 1)
        else:
            # Vẽ sprite thường
            screen_x = self.x - camera.x
            screen_y = self.y - camera.y
            
            # Ghost mode: vẽ với alpha mờ
            if self.ghost_mode and not self.is_dead:
                ghost_image = self.image.copy()
                
                current_time = pygame.time.get_ticks()
                elapsed = current_time - self.ghost_start_time
                remaining = self.ghost_duration - elapsed
                
                # Nhấp nháy trong 0.5s cuối
                if self.ghost_flicker:
                    alpha = 80 if (current_time // 100) % 2 == 0 else 150
                else:
                    alpha = 100
                
                ghost_image.set_alpha(alpha)
                screen.blit(ghost_image, (screen_x, screen_y))
                
                # Debug: hiển thị thời gian ghost còn lại
                if self.debug:
                    remaining_sec = max(0, remaining / 1000)
                    font = pygame.font.SysFont("Arial", 16)
                    ghost_text = font.render(f"🛡️ {remaining_sec:.1f}s", True, (200, 200, 255))
                    screen.blit(ghost_text, (screen_x, screen_y - 30))
            else:
                screen.blit(self.image, (screen_x, screen_y))
            
            # Debug hitbox
            if DEBUG_MODE:
                # Attack hitbox (đỏ)
                if self.is_attacking and self.attack_hitbox:
                    hitbox_screen_x = self.attack_hitbox.x - camera.x
                    hitbox_screen_y = self.attack_hitbox.y - camera.y
                    pygame.draw.rect(screen, (255, 0, 0), (hitbox_screen_x, hitbox_screen_y, self.attack_hitbox.width, self.attack_hitbox.height), 2)
                
                # Hitbox thường (xanh lá)
                pygame.draw.rect(screen, (0, 255, 0), (screen_x + self.hitbox_offset_x, screen_y + self.hitbox_offset_y, self.hitbox_width, self.hitbox_height), 2)

        # Vẽ hit effects (vết chém) lên trên cùng
        self.hit_effect_manager.draw(screen, camera)

    # Trả về hitbox của nhân vật
    def get_rect(self):
        return pygame.Rect(
            self.x + self.hitbox_offset_x, 
            self.y + self.hitbox_offset_y, 
            self.hitbox_width, 
            self.hitbox_height
        )
    
    # Trả về hitbox tấn công (None nếu không đang tấn công)
    def get_attack_hitbox(self):
        return self.attack_hitbox if self.is_attacking else None
    
    # Trạng thái dash
    def is_dashing_state(self):
        return self.is_dashing
    
    # Thời gian hồi dash còn lại (ms)
    def get_dash_cooldown_remaining(self):
        if self.is_dashing:
            return 0
        current_time = pygame.time.get_ticks()
        remaining = self.dash_cooldown - (current_time - self.last_dash_time)
        return max(0, remaining)
    
    # Trạng thái hit
    def is_hit_state(self):
        return self.is_hit
    
    # Thời gian hit còn lại (ms)
    def get_hit_remaining(self):
        if not self.is_hit:
            return 0
        current_time = pygame.time.get_ticks()
        remaining = self.hit_duration - (current_time - self.hit_start_time)
        return max(0, remaining)