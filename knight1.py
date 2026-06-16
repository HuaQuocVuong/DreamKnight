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
    load_hit_frames  # THÊM MỚI: Import hit frames
)


#================================================================================================
# Lớp Player1 kế thừa từ pygame.sprite.Sprite để sử dụng hệ thống sprite của Pygame
# Lớp Player1 - Đại diện cho nhân vật chính (hiệp sĩ) trong game.
# Quản lý:
# - Các trạng thái: đứng yên (idle), đi bộ (walk), chạy (run), tấn công (attack), dash (lướt), hit (dính đòn).
# - Animation riêng cho từng trạng thái và từng hướng (lên, xuống, trái, phải).
# - Di chuyển mượt với vector chuẩn hóa, di chuyển = nhấn giữ shift trái
# - Tấn công bằng chuột trái, tạo hitbox tấn công và phát âm thanh luân phiên.
# - Dash bằng chuột phải, lướt nhanh về phía trước với animation và kích thước sprite riêng
# - Dính đòn (hit): nhân vật bị đánh trúng, hiển thị animation hit và bị đẩy lùi
# - Gây sát thương lên kẻ địch khi tấn công
# - Giới hạn trong bản đồ, cập nhật camera, vẽ với debug hitbox.
#================================================================================================

class Player1(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # KHỞI TẠO CÁC BỘ ANIMATION
        self.idle_animations = {
            "up": Animation(load_idle_frames("up"), frame_duration=500),
            "down": Animation(load_idle_frames("down"), frame_duration=200), 
            "left": Animation(load_idle_frames("left"), frame_duration=200),
            "right": Animation(load_idle_frames("right"), frame_duration=500),
        }
        
        self.walk_animations = {
            "up": Animation(load_walk_frames("up")),
            "down": Animation(load_walk_frames("down")), 
            "left": Animation(load_walk_frames("left")),
            "right": Animation(load_walk_frames("right")),
        }
        
        self.run_animations = {
            "up": Animation(load_run_frames("up"), frame_duration=80),
            "down": Animation(load_run_frames("down"), frame_duration=80), 
            "left": Animation(load_run_frames("left"), frame_duration=80),
            "right": Animation(load_run_frames("right"), frame_duration=80),
        }
        
        self.attack_idle_animations = {
            "up": Animation(load_attack_idle_frames("up"), frame_duration=60),
            "down": Animation(load_attack_idle_frames("down"), frame_duration=60), 
            "left": Animation(load_attack_idle_frames("left"), frame_duration=60),
            "right": Animation(load_attack_idle_frames("right"), frame_duration=60),
        }
        
        # Animation tấn công khi đi bộ
        self.attack_walk_animations = {
            "up": Animation(load_attack_walk_frames("up"), frame_duration=60),
            "down": Animation(load_attack_walk_frames("down"), frame_duration=60), 
            "left": Animation(load_attack_walk_frames("left"), frame_duration=60),
            "right": Animation(load_attack_walk_frames("right"), frame_duration=60),
        }
        
        self.attack_run_animations = {
            "up": Animation(load_attack_run_frames("up"), frame_duration=50),
            "down": Animation(load_attack_run_frames("down"), frame_duration=50), 
            "left": Animation(load_attack_run_frames("left"), frame_duration=50),
            "right": Animation(load_attack_run_frames("right"), frame_duration=50),
        }
        
        # DASH ANIMATION
        self.dash_animations = {
            "up": Animation(load_dash_frames("up"), frame_duration=40),
            "down": Animation(load_dash_frames("down"), frame_duration=40),
            "left": Animation(load_dash_frames("left"), frame_duration=40),
            "right": Animation(load_dash_frames("right"), frame_duration=40),
        }

        # ===== THÊM MỚI: HIT ANIMATION =====
        # Animation khi nhân vật bị dính đòn
        self.hit_animations = {
            "up": Animation(load_hit_frames("up"), frame_duration=100),
            "down": Animation(load_hit_frames("down"), frame_duration=100),
            "left": Animation(load_hit_frames("left"), frame_duration=100),
            "right": Animation(load_hit_frames("right"), frame_duration=100),
        }

        # KHỞI TẠO ÂM THANH
        pygame.mixer.init()
        self.attack_sound_1 = pygame.mixer.Sound("03_sounds/attack/Sword1.mp3")
        self.attack_sound_2 = pygame.mixer.Sound("03_sounds/attack/Sword2.mp3")
        self.attack_sound_3 = pygame.mixer.Sound("03_sounds/attack/Sword3.mp3")
        self.attack_sound_4 = pygame.mixer.Sound("03_sounds/attack/Sword4.mp3")
        
        self.dash_sound = pygame.mixer.Sound("03_sounds/dash/dash03.mp3")
        
        # ===== THÊM MỚI: Âm thanh khi bị đánh =====
        self.hit_sound = pygame.mixer.Sound("03_sounds/Hk Stun 01.mp3")  # Tạo file âm thanh này

        self.attack_sounds = [
            self.attack_sound_1,
            self.attack_sound_2,
            self.attack_sound_3,
            self.attack_sound_4,
        ]
        
        self.current_attack_sound_index = 0

        # Đăng ký tất cả sound vào SoundManager
        for s in self.attack_sounds:
            sound_manager.register_sound(s)
        sound_manager.register_sound(self.dash_sound)
        sound_manager.register_sound(self.hit_sound)  # THÊM MỚI

        # BIẾN TRẠNG THÁI CỦA PLAYER
        self.direction = "down"
        self.is_running = False
        self.is_attacking = False
        self.attack_start_time = 0
        self.attack_duration = 300
        self.sound_played_for_this_attack = False  
        
        # ===== THÊM MỚI: TRẠNG THÁI HIT =====
        self.is_hit = False             # Đang trong trạng thái bị dính đòn
        self.hit_start_time = 0         # Thời điểm bắt đầu bị đòn
        self.hit_duration = 300         # Thời gian dính đòn (ms)
        self.hit_knockback_distance = 30  # Khoảng cách bị đẩy lùi (pixels)
        self.hit_knockback_speed = 0    # Tốc độ đẩy lùi (tính từ distance/duration)
        self.hit_start_x = 0            # Vị trí bắt đầu bị đẩy
        self.hit_start_y = 0
        self.hit_target_x = 0           # Vị trí đích sau khi bị đẩy
        self.hit_target_y = 0
        self.hit_direction_vector = (0, 0)  # Hướng bị đẩy
        
        # BIẾN TOGGLE RUN
        self.run_mode = False
        self.shift_just_pressed = False
        
        # DASH VARIABLES
        self.is_dashing = False
        self.dash_start_time = 0
        self.dash_duration = 150
        self.dash_distance = 100
        self.dash_start_x = 0
        self.dash_start_y = 0
        self.dash_target_x = 0
        self.dash_target_y = 0
        self.dash_cooldown = 500
        self.last_dash_time = 0
        self.dash_direction = "down"
        
        # Kích thước sprite dash
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

        self.hitbox_width = 30
        self.hitbox_height = 50
        self.hitbox_offset_x = 45
        self.hitbox_offset_y = 40

        self.dx = 0
        self.dy = 0
        
        self.debug = DEBUG_MODE
        self.attack_hitbox = None

        # HỆ THỐNG SÁT THƯƠNG
        self.health = 100
        self.max_health = 100
        self.gold = 0
        self.is_dead = False
        
        # GHOST MODE
        self.ghost_mode = False
        self.ghost_start_time = 0
        self.ghost_duration = 1500
        self.ghost_used = False
        self.ghost_alpha = 80

        self.damage = 15
        self.attack_range = 60
        self.attack_damage_level = 0
        self.attack_speed_level = 0
        self.dash_upgrade_level = 0
        self.range_upgrade_level = 0
        self.has_dealt_damage = False
        self.damage_cooldown = 400
        self.last_damage_time = 0
        self.enemies = None
        
        # HIT EFFECT MANAGER
        self.hit_effect_manager = HitEffectManager()

    # ===== THÊM MỚI: HÀM KÍCH HOẠT HIT =====
    def trigger_hit(self, damage, knockback_direction=None):
        """
        Kích hoạt trạng thái dính đòn cho nhân vật
        
        Args:
            damage: Sát thương nhận vào
            knockback_direction: Hướng đẩy lùi (tuple (dx, dy)) hoặc None (tự động tính từ enemy)
        """
        if self.is_dead or self.is_dashing:
            return
        
        # Trừ máu
        self.health = max(0, self.health - damage)
        print(f"💥 Player nhận {damage} sát thương! Máu còn: {self.health}/{self.max_health}")
        
        # Phát âm thanh hit
        try:
            self.hit_sound.play()
        except:
            pass
        
        # Kích hoạt ghost mode nếu HP <= 20%
        if self.health <= self.max_health * 0.2 and not self.ghost_used:
            self.ghost_mode = True
            self.ghost_used = True
            self.ghost_start_time = pygame.time.get_ticks()
            print("⚠️ HP thấp! Ghost mode 2 giây!")
        
        # Kiểm tra chết
        if self.health <= 0:
            self.is_dead = True
            print("💀 Player đã chết!")
            return
        
        # Kích hoạt hit animation
        self.is_hit = True
        self.hit_start_time = pygame.time.get_ticks()
        self.hit_animations[self.direction].reset()
        
        # Tạo hiệu ứng hit
        self.hit_effect_manager.spawn(self.x + self.width//2, self.y + self.height//2)
        
        # Xử lý knockback (đẩy lùi)
        if knockback_direction:
            # Sử dụng hướng đẩy được chỉ định
            dx, dy = knockback_direction
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length
            else:
                dx, dy = 0, 0
        else:
            # Tự động đẩy lùi theo hướng ngược với hướng nhân vật đang đối mặt
            # Mặc định đẩy lùi về phía sau
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
        
        # Giới hạn target trong map
        from config import MAP_WIDTH, MAP_HEIGHT
        self.hit_target_x = max(0, min(self.hit_target_x, MAP_WIDTH - self.width))
        self.hit_target_y = max(0, min(self.hit_target_y, MAP_HEIGHT - self.height))
        
        # Tính tốc độ đẩy (pixels/ms)
        self.hit_knockback_speed = self.hit_knockback_distance / self.hit_duration

    # ===== THÊM MỚI: UPDATE HIT =====
    def update_hit(self, map_width, map_height):
        """Cập nhật trạng thái hit (dính đòn) của nhân vật"""
        if not self.is_hit:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.hit_start_time
        
        # Kiểm tra kết thúc hit
        if elapsed >= self.hit_duration:
            self.is_hit = False
            self.hit_direction_vector = (0, 0)
            return
        
        # Cập nhật animation hit
        self.hit_animations[self.direction].update()
        
        # Nội suy vị trí bị đẩy lùi (ease-out)
        progress = elapsed / self.hit_duration
        # Sử dụng easing function: bắt đầu nhanh, kết thúc chậm
        eased_progress = 1 - (1 - progress) ** 2
        
        # Tính vị trí hiện tại
        new_x = self.hit_start_x + (self.hit_target_x - self.hit_start_x) * eased_progress
        new_y = self.hit_start_y + (self.hit_target_y - self.hit_start_y) * eased_progress
        
        # Áp dụng vị trí mới
        self.x = max(0, min(new_x, map_width - self.width))
        self.y = max(0, min(new_y, map_height - self.height))
        self.rect.x = self.x
        self.rect.y = self.y

    def handle_input(self, events):
        """Xử lý input từ bàn phím và chuột"""
        # ===== QUAN TRỌNG: Nếu đang hit, vẫn cho phép dash để thoát hit =====
        # Nếu đang hit, chỉ cho phép dash để phá vỡ trạng thái hit
        if self.is_hit:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Chuột phải
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_dash_time >= self.dash_cooldown:
                        self.is_hit = False  # Thoát khỏi trạng thái hit khi dash
                        self.start_dash()
            return  # Không xử lý input di chuyển khi đang hit
        
        keys = pygame.key.get_pressed()
        
        # XỬ LÝ TOGGLE RUN
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if not self.shift_just_pressed:
                self.run_mode = not self.run_mode
                self.shift_just_pressed = True
        else:
            self.shift_just_pressed = False
        
        # XỬ LÝ DASH
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_dash_time >= self.dash_cooldown:
                    self.start_dash()
        
        # Nếu đang dash, không xử lý input di chuyển
        if self.is_dashing:
            return
        
        if not self.is_attacking:
            dx_raw = (keys[pygame.K_d] - keys[pygame.K_a])
            dy_raw = (keys[pygame.K_s] - keys[pygame.K_w])

            if dx_raw != 0 or dy_raw != 0:
                length = max((dx_raw**2 + dy_raw**2) ** 0.5, 0.1)
                
                if self.run_mode:
                    self.dx = (dx_raw / length) * RUN_SPEED
                    self.dy = (dy_raw / length) * RUN_SPEED
                    self.is_running = True
                else:
                    self.dx = (dx_raw / length) * PLAYER_SPEED
                    self.dy = (dy_raw / length) * PLAYER_SPEED
                    self.is_running = False

                if dx_raw != 0:
                    self.direction = "right" if dx_raw > 0 else "left"
                else:
                    self.direction = "down" if dy_raw > 0 else "up"
            else:
                self.dx = 0
                self.dy = 0
                self.is_running = False

        # Xử lý tấn công
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.is_attacking and not self.is_dashing and not self.is_hit:  # Không attack khi đang hit
                    self.start_attack()
    
    def play_next_attack_sound(self):
        """Phát âm thanh tấn công luân phiên"""
        self.attack_sounds[self.current_attack_sound_index].play()
        self.current_attack_sound_index += 1
        if self.current_attack_sound_index >= len(self.attack_sounds):
            self.current_attack_sound_index = 0

    def start_dash(self):
        """Bắt đầu dash - lướt nhanh về phía trước"""
        self.is_dashing = True
        self.is_attacking = False
        self.is_hit = False  # Dash sẽ ngắt trạng thái hit
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
        
        dash_vec = self.get_dash_vector()
        self.dash_target_x = self.x + dash_vec[0] * self.dash_distance
        self.dash_target_y = self.y + dash_vec[1] * self.dash_distance
        
        self.create_dash_effect()
    
    def get_dash_vector(self):
        """Lấy vector đơn vị cho hướng dash"""
        vectors = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        return vectors.get(self.dash_direction, (0, 1))
    
    def create_dash_effect(self):
        """Tạo hiệu ứng dash - có thể mở rộng để thêm particle system"""
        pass
    
    def update_dash(self, map_width, map_height):
        """Cập nhật dash: di chuyển nội suy và kiểm tra kết thúc"""
        if not self.is_dashing:
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.dash_start_time
        progress = min(1.0, elapsed / self.dash_duration)
        
        eased_progress = 1 - (1 - progress) ** 3
        
        new_x = self.dash_start_x + (self.dash_target_x - self.dash_start_x) * eased_progress
        new_y = self.dash_start_y + (self.dash_target_y - self.dash_start_y) * eased_progress
        
        self.x = max(0, min(new_x, map_width - self.width))
        self.y = max(0, min(new_y, map_height - self.height))
        self.rect.x = self.x
        self.rect.y = self.y
        
        self.dash_animations[self.dash_direction].update()
        
        if progress >= 1.0:
            self.is_dashing = False
            self.reset_sprite_size()
    
    def reset_sprite_size(self):
        """Reset kích thước sprite về bình thường sau dash"""
        pass

    def start_attack(self):
        """Bắt đầu tấn công"""
        self.is_attacking = True
        self.attack_start_time = pygame.time.get_ticks()
        self.sound_played_for_this_attack = False
        self.has_dealt_damage = False
        
        if self.is_running:
            self.attack_run_animations[self.direction].reset()
        elif self.dx != 0 or self.dy != 0:
            self.attack_walk_animations[self.direction].reset()
        else:
            self.attack_idle_animations[self.direction].reset()
        
        self.create_attack_hitbox()

    def create_attack_hitbox(self):
        """Tạo hitbox cho đòn tấn công"""
        hitbox_width_vertical = 80
        hitbox_height_vertical = 30
        hitbox_width_horizontal = 30
        hitbox_height_horizontal = 80
        
        offset_config = {
            "up": {
                "offset_x": 0,
                "offset_y": -25,
                "width": hitbox_width_vertical,
                "height": hitbox_height_vertical
            },
            "down": {
                "offset_x": 0,
                "offset_y": 45,
                "width": hitbox_width_vertical,
                "height": hitbox_height_vertical
            },
            "left": {
                "offset_x": -35,
                "offset_y": 5,
                "width": hitbox_width_horizontal,
                "height": hitbox_height_horizontal
            },
            "right": {
                "offset_x": 40,
                "offset_y": 5,
                "width": hitbox_width_horizontal,
                "height": hitbox_height_horizontal
            }
        }
        
        config = offset_config[self.direction]
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        hitbox_x = center_x + config["offset_x"] - config["width"] // 2
        hitbox_y = center_y + config["offset_y"] - config["height"] // 2
        
        self.attack_hitbox = pygame.Rect(
            hitbox_x,
            hitbox_y,
            config["width"],
            config["height"]
        )
    
    def deal_damage_to_enemies(self):
        """Gây sát thương lên tất cả kẻ địch trong vùng attack_hitbox"""
        if not self.is_attacking or self.attack_hitbox is None:
            return
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time < self.damage_cooldown:
            return
        
        if self.enemies is None:
            return
        
        for enemy in self.enemies:
            if hasattr(enemy, 'is_dead') and enemy.is_dead:
                continue
            
            if hasattr(enemy, 'get_hitbox'):
                enemy_hx, enemy_hy, enemy_hr = enemy.get_hitbox()
                enemy_hitbox_rect = pygame.Rect(
                    enemy_hx - enemy_hr, 
                    enemy_hy - enemy_hr, 
                    enemy_hr * 2, 
                    enemy_hr * 2
                )
                
                if self.attack_hitbox.colliderect(enemy_hitbox_rect):
                    if hasattr(enemy, 'take_damage'):
                        enemy.take_damage(self.damage)
                        self.last_damage_time = current_time
                        print(f"⚔️ Player gây {self.damage} sát thương lên {enemy.__class__.__name__}!")
                        
                        intersection = self.attack_hitbox.clip(enemy_hitbox_rect)
                        self.hit_effect_manager.spawn(intersection.centerx, intersection.centery)
                        break
            else:
                if hasattr(enemy, 'rect'):
                    if self.attack_hitbox.colliderect(enemy.rect):
                        if hasattr(enemy, 'take_damage'):
                            enemy.take_damage(self.damage)
                            self.last_damage_time = current_time
                            print(f"⚔️ Player gây {self.damage} sát thương lên {enemy.__class__.__name__}!")
                            self.hit_effect_manager.spawn(enemy.rect.centerx, enemy.rect.centery)
                            break

    def set_enemies(self, enemies):
        """Gán danh sách enemy từ game chính"""
        self.enemies = enemies

    def take_damage(self, damage, knockback_direction=None):
        """
        Nhận sát thương từ enemy
        
        Args:
            damage: Sát thương nhận vào
            knockback_direction: Hướng đẩy lùi (từ enemy đến player)
        """
        if self.is_dead:
            return
        
        # Nếu đang ghost mode thì không nhận damage
        if self.ghost_mode:
            current_time = pygame.time.get_ticks()
            if current_time - self.ghost_start_time < self.ghost_duration:
                print("🛡️ Player đang ghost mode - miễn sát thương!")
                return
            else:
                self.ghost_mode = False
        
        # Gọi hàm trigger_hit để xử lý hit
        self.trigger_hit(damage, knockback_direction)

    def update_attack(self):
        """Cập nhật trạng thái tấn công"""
        if self.is_dashing or self.is_hit:  # Không xử lý attack khi đang dash hoặc hit
            return
            
        if self.is_attacking:
            current_time = pygame.time.get_ticks()
            
            if not self.sound_played_for_this_attack:
                self.play_next_attack_sound()
                self.sound_played_for_this_attack = True
            
            if self.is_running:
                self.attack_run_animations[self.direction].update()
            elif self.dx != 0 or self.dy != 0:
                self.attack_walk_animations[self.direction].update()
            else:
                self.attack_idle_animations[self.direction].update()
            
            attack_progress = current_time - self.attack_start_time
            if not self.has_dealt_damage and attack_progress > 100:
                self.has_dealt_damage = True
                self.deal_damage_to_enemies()
            
            if current_time - self.attack_start_time >= self.attack_duration:
                self.is_attacking = False
                self.attack_hitbox = None
                self.has_dealt_damage = False

    def update_running_state(self):
        """Cập nhật trạng thái chạy (giữ lại để tương thích)"""
        pass

    def move(self, dx, dy, map_width, map_height):
        """Di chuyển nhân vật"""
        if self.is_dashing or self.is_hit:  # Không di chuyển bằng input khi đang dash hoặc hit
            return
            
        if self.is_attacking:
            speed_multiplier = 0.3 if self.is_running else 0.1
        else:
            speed_multiplier = 1.0
            
        current_dx = dx * speed_multiplier
        current_dy = dy * speed_multiplier
        
        new_x = self.x + current_dx
        new_y = self.y + current_dy
        
        if 0 <= new_x <= map_width - self.width:
            self.x = new_x
        if 0 <= new_y <= map_height - self.height:
            self.y = new_y
            
        self.rect.x = self.x
        self.rect.y = self.y
        
        if self.is_attacking:
            self.create_attack_hitbox()

    def update(self, map_width, map_height, events):
        """Cập nhật toàn bộ trạng thái nhân vật mỗi frame"""

        if self.ghost_mode and not self.is_dead:
            current_time = pygame.time.get_ticks()
            if current_time - self.ghost_start_time >= self.ghost_duration:
                self.ghost_mode = False
                print("👻 Hết ghost mode! Trở lại bình thường.")

        # Xử lý input
        self.handle_input(events)
        
        # Cập nhật dash
        self.update_dash(map_width, map_height)
        
        # Nếu đang dash, chỉ cập nhật animation và thoát
        if self.is_dashing:
            self.dash_animations[self.dash_direction].update()
            self.image = self.dash_animations[self.dash_direction].current_frame
            return
        
        # ===== THÊM MỚI: Cập nhật hit =====
        self.update_hit(map_width, map_height)
        
        # Nếu đang hit, chỉ cập nhật animation hit và thoát
        if self.is_hit:
            self.image = self.hit_animations[self.direction].current_frame
            self.hit_effect_manager.update()
            return
        
        # Phần còn lại cho state bình thường
        self.update_running_state()
        self.update_attack()
        self.move(self.dx, self.dy, map_width, map_height)
        self.hit_effect_manager.update()

        # Chọn animation bình thường
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
    
    def draw(self, screen, camera):
        """Vẽ nhân vật lên màn hình"""
        # ===== VẼ DASH VỚI KÍCH THƯỚC SPRITE ĐẶC BIỆT =====
        if self.is_dashing:
            # Lấy kích thước dash sprite
            dash_width, dash_height = self.dash_sprite_sizes.get(self.dash_direction, (self.width, self.height))
            
            # ===== OFFSET ĐỂ CANH CHỈNH ANIMATION DASH =====
            # Điều chỉnh các giá trị này để sprite dash khớp với vị trí nhân vật
            dash_sprite_offset = {
                "left": {"offset_x": 5, "offset_y": 30},   # Left: dịch XUỐNG 30px
                "right": {"offset_x": -70, "offset_y": 30}, # Right: dịch XUỐNG 30px
                "up": {"offset_x": 30, "offset_y": 0},     # Up: dịch SANG PHẢI 30px
                "down": {"offset_x": 30, "offset_y": -50}   # Down: dịch SANG PHẢI 30px
            }
            
            offset = dash_sprite_offset.get(self.dash_direction, {"offset_x": 0, "offset_y": 0})
            
            # Tính vị trí vẽ sprite dash
            if self.dash_direction in ["left", "right"]:
                offset_x = (self.width - dash_width) // 2
                screen_x = self.x - camera.x + offset_x + offset["offset_x"]
                screen_y = self.y - camera.y + offset["offset_y"]
            else:
                offset_y = (self.height - dash_height) // 2
                screen_x = self.x - camera.x + offset["offset_x"]
                screen_y = self.y - camera.y + offset_y + offset["offset_y"]
            
            # Vẽ sprite dash
            screen.blit(self.image, (screen_x, screen_y))
            
            # ===== VẼ HITBOX DASH (DEBUG) =====
            if DEBUG_MODE:
                # Tính tiến độ dash
                current_time = pygame.time.get_ticks()
                elapsed = current_time - self.dash_start_time
                progress = min(1.0, elapsed / self.dash_duration)
                
                # Hitbox bắt đầu
                start_hitbox_x = self.dash_start_x + self.hitbox_offset_x
                start_hitbox_y = self.dash_start_y + self.hitbox_offset_y
                
                # Hitbox đích
                target_hitbox_x = self.dash_target_x + self.hitbox_offset_x
                target_hitbox_y = self.dash_target_y + self.hitbox_offset_y
                
                # Nội suy vị trí hitbox hiện tại
                current_hitbox_x = start_hitbox_x + (target_hitbox_x - start_hitbox_x) * progress
                current_hitbox_y = start_hitbox_y + (target_hitbox_y - start_hitbox_y) * progress
                
                # Vẽ hitbox xanh (hitbox thường)
                green_hitbox_x = self.x + self.hitbox_offset_x - camera.x
                green_hitbox_y = self.y + self.hitbox_offset_y - camera.y
                pygame.draw.rect(screen, (0, 255, 0), 
                            (green_hitbox_x, green_hitbox_y, 
                                self.hitbox_width, self.hitbox_height), 2)
                
                # Vẽ hitbox vàng (hitbox dash nội suy)
                pygame.draw.rect(screen, (255, 255, 0), 
                            (current_hitbox_x - camera.x, 
                                current_hitbox_y - camera.y, 
                                self.hitbox_width, 
                                self.hitbox_height), 2)
                
                # Vẽ đường kẻ từ start đến target
                start_screen_x = start_hitbox_x - camera.x
                start_screen_y = start_hitbox_y - camera.y
                target_screen_x = target_hitbox_x - camera.x
                target_screen_y = target_hitbox_y - camera.y
                pygame.draw.line(screen, (255, 0, 255), 
                            (start_screen_x, start_screen_y), 
                            (target_screen_x, target_screen_y), 1)
        else:
            # ===== KHÔNG DASH: Vẽ sprite nhân vật =====
            screen_x = self.x - camera.x
            screen_y = self.y - camera.y
            
            # Xử lý ghost mode (mờ dần)
            if self.ghost_mode and not self.is_dead:
                # Tạo bản sao với alpha
                ghost_image = self.image.copy()
                ghost_image.set_alpha(self.ghost_alpha)  # Độ mờ
                screen.blit(ghost_image, (screen_x, screen_y))
                
                # Hiển thị thời gian ghost còn lại (debug)
                if self.debug:
                    current_time = pygame.time.get_ticks()
                    remaining = max(0, (self.ghost_start_time + self.ghost_duration - current_time) // 1000)
                    font = pygame.font.SysFont("Arial", 16)
                    ghost_text = font.render(f"👻 {remaining}s", True, (200, 200, 255))
                    screen.blit(ghost_text, (screen_x, screen_y - 30))
            else:
                # Vẽ bình thường
                screen.blit(self.image, (screen_x, screen_y))
            
            # ===== VẼ HITBOX (DEBUG) =====
            if DEBUG_MODE:
                # Vẽ attack hitbox nếu đang tấn công
                if self.is_attacking and self.attack_hitbox:
                    hitbox_screen_x = self.attack_hitbox.x - camera.x
                    hitbox_screen_y = self.attack_hitbox.y - camera.y
                    pygame.draw.rect(screen, (255, 0, 0), 
                                (hitbox_screen_x, hitbox_screen_y, 
                                    self.attack_hitbox.width, self.attack_hitbox.height), 2)
                
                # Vẽ hitbox thường của nhân vật
                pygame.draw.rect(screen, (0, 255, 0), 
                            (screen_x + self.hitbox_offset_x, 
                            screen_y + self.hitbox_offset_y, 
                            self.hitbox_width, 
                            self.hitbox_height), 2)

        # VẼ HIT EFFECTS (luôn vẽ sau sprite để hiện lên trên)
        self.hit_effect_manager.draw(screen, camera)

    def get_rect(self):
        """Trả về hitbox của nhân vật"""
        return pygame.Rect(
            self.x + self.hitbox_offset_x, 
            self.y + self.hitbox_offset_y, 
            self.hitbox_width, 
            self.hitbox_height
        )
    
    def get_attack_hitbox(self):
        """Trả về hitbox tấn công"""
        return self.attack_hitbox if self.is_attacking else None
    
    def is_dashing_state(self):
        """Trả về trạng thái dash hiện tại"""
        return self.is_dashing
    
    def get_dash_cooldown_remaining(self):
        """Lấy thời gian còn lại của cooldown dash (ms)"""
        if self.is_dashing:
            return 0
        current_time = pygame.time.get_ticks()
        remaining = self.dash_cooldown - (current_time - self.last_dash_time)
        return max(0, remaining)
    
    # ===== THÊM MỚI: Hàm kiểm tra trạng thái hit =====
    def is_hit_state(self):
        """Trả về trạng thái hit hiện tại"""
        return self.is_hit
    
    def get_hit_remaining(self):
        """Lấy thời gian còn lại của trạng thái hit (ms)"""
        if not self.is_hit:
            return 0
        current_time = pygame.time.get_ticks()
        remaining = self.hit_duration - (current_time - self.hit_start_time)
        return max(0, remaining)