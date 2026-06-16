import pygame
import os
import math
from config import PLAYER_SPEED, RUN_SPEED
from knight1_animation import Animation, AnimationManager
#================================================================================================
# CẤU HÌNH CHO SLIME2 TARGET

#================================================================================================
SLIME2_ANIMATION_CONFIGS = {
    "idle": {
        "folder": "slime2_idle",
        "directions": {
            "up":    {"prefix": "slime2_idle_up", "frames": 6},
            "down":  {"prefix": "slime2_idle_down", "frames": 6},
            "left":  {"prefix": "slime2_idle_left", "frames": 6},
            "right": {"prefix": "slime2_idle_right", "frames": 6}
        }
    },
    "walk": {
        "folder": "slime2_walk",
        "directions": {
            "up":    {"prefix": "slime2_walk_up", "frames": 8},
            "down":  {"prefix": "slime2_walk_down", "frames": 8},
            "left":  {"prefix": "slime2_walk_left", "frames": 8},
            "right": {"prefix": "slime2_walk_right", "frames": 8}
        }
    },
    "run": {
        "folder": "slime2_run",
        "directions": {
            "up":    {"prefix": "slime2_run_up", "frames": 8},
            "down":  {"prefix": "slime2_run_down", "frames": 8},
            "left":  {"prefix": "slime2_run_left", "frames": 8},
            "right": {"prefix": "slime2_run_right", "frames": 8}
        }
    },
    "attack": {
        "folder": "slime2_attack",
        "directions": {
            "up":    {"prefix": "slime2_attack_up", "frames": 11},
            "down":  {"prefix": "slime2_attack_down", "frames": 11},
            "left":  {"prefix": "slime2_attack_left", "frames": 11},
            "right": {"prefix": "slime2_attack_right", "frames": 11}
        }
    },
    "hit": {
        "folder": "slime2_hurt",  # Cần tạo thư mục slime2_hit với các frame
        "directions": {
            "up":    {"prefix": "slime2_hurt_up", "frames": 4},
            "down":  {"prefix": "slime2_hurt_down", "frames": 4},
            "left":  {"prefix": "slime2_hurt_left", "frames": 4},
            "right": {"prefix": "slime2_hurt_right", "frames": 4}
        }
    },
    "death": {
        "folder": "slime2_die",  # Cần tạo thư mục slime2_death với các frame
        "directions": {
            "up":    {"prefix": "slime2_die_up", "frames": 6},
            "down":  {"prefix": "slime2_die_down", "frames": 6},
            "left":  {"prefix": "slime2_die_left", "frames": 6},
            "right": {"prefix": "slime2_die_right", "frames": 6}
        }
    }
}


# Lớp Slime2 - kẻ địch slime
class Slime2(pygame.sprite.Sprite):
    
    def __init__(self, x, y, scale_factor=2.0):
        super().__init__()
        
        # VỊ TRÍ VÀ HITBOX CƠ BẢN 
        self.x = float(x)
        self.y = float(y)
        self.home_x = float(x)    # lưu vị trí nhà để quay về
        self.home_y = float(y)
        
        # Khởi tạo các dictionary chứa Animation
        self.idle_anims = {}
        self.walk_anims = {}
        self.run_anims = {}
        self.attack_anims = {}
        self.hit_anims = {}
        self.death_anims = {}
        
        # Load tất cả animation
        self._load_all_animations(scale_factor)
        
        # TRẠNG THÁI HIỆN TẠI 
        self.direction = "down"              
        self.state = "idle"                
        self.is_attacking = False
        
        # THÔNG SỐ DI CHUYỂN 
        self.speed = 0.0
        self.dx = 0.0
        self.dy = 0.0
        
        # PARAMETERS (có thể điều chỉnh cho slime)
        self.home_chase_radius = 250         # vùng phát hiện cố định (rộng hơn plant một chút)
        self.home_leave_radius = 450         # vùng rời cố định
        self.walk_duration = 1200            # thời gian đi bộ trước khi chạy (ms) - lâu hơn plant
        self.attack_range = 45               # khoảng cách để kích hoạt animation tấn công (gần hơn plant)
        self.attack_duration = 600           # thời gian thực hiện animation tấn công (ms) - lâu hơn plant

        self.walk_start_time = 0
        self.is_running = False
        self.attack_start_time = 0            # thời điểm bắt đầu tấn công
        
        # THÔNG SỐ CHO BỊ THƯƠNG VÀ CHẾT
        self.health = 500                # máu của slime
        self.max_health = 500 
        self.contact_damage = 15         # Sát thương khi chạm thân vào player
        self.hit_start_time = 0
        self.hit_duration = 300               # thời gian animation bị thương (ms)
        self.death_start_time = 0
        self.death_frame_duration = 85   # khớp với frame_duration trong load_anim_type("death")
        self.death_frames_count = 6      # khớp với "frames": 6 trong SLIME2_ANIMATION_CONFIGS
        self.death_duration = self.death_frame_duration * self.death_frames_count  # = 510ms
        self.is_dead = False                  # trạng thái đã chết
        self.fully_dead = False  # ← thêm dòng này
        self.is_invincible = False            # trạng thái bất tử (sau khi bị đánh)
        self.invincible_duration = 500        # thời gian bất tử (ms)
        self.invincible_start_time = 0
        
        # Lưu player reference
        self.player = None
        
        # HITBOX
        self.body_radius = 20
        
        # HÌNH ẢNH VÀ RECT 
        if "down" in self.idle_anims:
            self.image = self.idle_anims["down"].current_frame
        else:
            # Fallback: tạo surface trắng nếu không có animation
            self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
            self.image.fill((128, 0, 128))  # màu tím cho slime
            
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.body_radius = max(self.width, self.height) // 2
        
        # Debug
        self.debug = True

        # LOAD ÂM THANH  ← THÊM TỪ ĐÂY
        self.attack_sounds = []
        self.hit_sound = None
        self.death_sound = None
        self.attack_sound_index = 0
        self._load_sounds()
        
    # Load tất cả các frame animation từ thư mục assets/slime_target/slime2
    def _load_all_animations(self, scale_factor):
        base_path = os.path.join("assets", "resource_slime1_2_3", "slime_2")
        
        # Kiểm tra thư mục tồn tại
        if not os.path.exists(base_path):
            print(f"Thư mục không tồn tại: {base_path}")
            return
            
        def load_anim_type(anim_type, frame_duration=90):
            anims = {}
            config = SLIME2_ANIMATION_CONFIGS.get(anim_type)
            if not config:
                return anims
            folder = config["folder"]
            for direction, dir_cfg in config["directions"].items():
                prefix = dir_cfg["prefix"]
                frame_count = dir_cfg["frames"]
                frames = []
                for i in range(1, frame_count + 1):
                    filename = f"{prefix}{i}.png"
                    filepath = os.path.join(base_path, folder, filename)
                    try:
                        if os.path.exists(filepath):
                            img = pygame.image.load(filepath).convert_alpha()
                            if scale_factor != 1.0:
                                new_size = (int(img.get_width() * scale_factor),
                                           int(img.get_height() * scale_factor))
                                img = pygame.transform.scale(img, new_size)
                            frames.append(img)
                        else:
                            # Tạo frame giả
                            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
                            surf.fill((128, 0, 128))  # Màu tím cho slime
                            frames.append(surf)
                    except Exception as e:
                        # Tạo frame giả
                        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
                        surf.fill((128, 0, 128))
                        frames.append(surf)
                if frames:
                    anims[direction] = Animation(frames, frame_duration)
                    print(f"Loaded {len(frames)} frames for {anim_type} {direction}")
            return anims
        
        self.idle_anims = load_anim_type("idle", frame_duration=200)
        self.walk_anims = load_anim_type("walk", frame_duration=100)
        self.run_anims = load_anim_type("run", frame_duration=90)
        self.attack_anims = load_anim_type("attack", frame_duration=70)
        self.hit_anims = load_anim_type("hit", frame_duration=75)
        self.death_anims = load_anim_type("death", frame_duration=85)
        
        # Nếu không load được animation hit, tạo animation mặc định
        if not self.hit_anims:
            print("Tạo animation hit mặc định cho slime2")
            default_frames = [pygame.Surface((64, 64), pygame.SRCALPHA)]
            default_frames[0].fill((255, 0, 0))  # màu đỏ cho bị thương
            self.hit_anims["down"] = Animation(default_frames, 75)
            self.hit_anims["up"] = Animation(default_frames, 75)
            self.hit_anims["left"] = Animation(default_frames, 75)
            self.hit_anims["right"] = Animation(default_frames, 75)
        
        # Nếu không load được animation death, tạo animation mặc định
        if not self.death_anims:
            print("Tạo animation death mặc định cho slime2")
            default_frames = [pygame.Surface((64, 64), pygame.SRCALPHA)]
            default_frames[0].fill((64, 0, 64))  # màu tím đậm cho chết
            self.death_anims["down"] = Animation(default_frames, 85)
            self.death_anims["up"] = Animation(default_frames, 85)
            self.death_anims["left"] = Animation(default_frames, 85)
            self.death_anims["right"] = Animation(default_frames, 85)
        
        # Nếu không load được animation nào, tạo animation mặc định
        if not self.idle_anims:
            print("Tạo animation mặc định cho slime2")
            default_frames = [pygame.Surface((64, 64), pygame.SRCALPHA)]
            default_frames[0].fill((128, 0, 128))
            self.idle_anims["down"] = Animation(default_frames, 200)
            self.idle_anims["up"] = Animation(default_frames, 200)
            self.idle_anims["left"] = Animation(default_frames, 200)
            self.idle_anims["right"] = Animation(default_frames, 200)

    def _load_sounds(self):
        sound_path = os.path.join("03_sounds", "slime2")
        for i in range(1, 4):
            path = os.path.join(sound_path, f"Attack{i}.mp3")
            self.attack_sounds.append(pygame.mixer.Sound(path))
        self.hit_sound = pygame.mixer.Sound(os.path.join(sound_path, "hit.mp3"))
        self.death_sound = pygame.mixer.Sound(os.path.join(sound_path, "Death.mp3"))

    
    # Gán tham chiếu đến player
    def set_player(self, player):
        self.player = player

    # Phương thức nhận sát thương
    def take_damage(self, damage):
        if self.is_dead:
            return False
        
        if self.is_invincible:
            return False
        
        # Trừ máu
        self.health -= damage
        print(f"Slime2 nhận {damage} sát thương! Máu còn: {self.health}/{self.max_health}")
        
        if self.health <= 0:
            # Slime chết
            self.health = 0
            self.die()
            return True
        else:
            # Slime bị thương
            self.state = "hit"
            self.hit_start_time = pygame.time.get_ticks()
            if self.hit_sound:   
                self.hit_sound.play()

            self.hit_start_time = pygame.time.get_ticks()
            
            # Bật trạng thái bất tử
            self.is_invincible = True
            self.invincible_start_time = pygame.time.get_ticks()
            
            # Dừng di chuyển khi bị đánh
            self.dx = 0
            self.dy = 0
            
            # Reset animation hit
            if self.direction in self.hit_anims:
                self.hit_anims[self.direction].reset()
            
            return True
    
    # Phương thức xử lý khi chết
    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.state = "death"
            self.death_start_time = pygame.time.get_ticks()
            if self.death_sound:   
                self.death_sound.play()
            self.dx = 0
            self.dy = 0
            self.is_attacking = False
        
            
            if self.direction in self.death_anims:
                self.death_anims[self.direction].reset() 

    # Cập nhật trạng thái bất tử
    def _update_invincible(self, current_time):
        if self.is_invincible:
            if current_time - self.invincible_start_time >= self.invincible_duration:
                self.is_invincible = False
            
    # Cập nhật trạng thái, di chuyển
    def update(self, delta_time, map_width, map_height):
        if self.player is None:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Cập nhật trạng thái bất tử
        self._update_invincible(current_time)
        
        # XỬ LÝ TRẠNG THÁI CHẾT
        if self.state == "death":
            self._update_animation(delta_time)
            if current_time - self.death_start_time >= self.death_duration:
                self.fully_dead = True  # ← đổi từ self.kill()
            self.dx = 0
            self.dy = 0
            return
                    
        
        # XỬ LÝ TRẠNG THÁI BỊ THƯƠNG
        if self.state == "hit":
            # Kiểm tra nếu đã hết thời gian animation hit
            if current_time - self.hit_start_time >= self.hit_duration:
                # Quay lại trạng thái trước đó (idle hoặc walk)
                self.state = "idle" if not self.is_running else "walk"
                print("Slime2 hết trạng thái bị thương")
            else:
                # Đang trong animation bị thương, không di chuyển
                self.dx = 0
                self.dy = 0
                self._update_animation(delta_time)
                return
        
        # XỬ LÝ TRẠNG THÁI TẤN CÔNG
        if self.state == "attack":
            # Kiểm tra nếu đã hết thời gian tấn công
            if current_time - self.attack_start_time >= self.attack_duration:
                self.state = "idle" if self.is_running == False else "run"
                self.is_attacking = False
                # Reset animation tấn công
                if self.direction in self.attack_anims:
                    self.attack_anims[self.direction].reset()
                print("Kết thúc animation tấn công của Slime2")
                # GÂY SÁT THƯƠNG LÊN PLAYER khi animation tấn công kết thúc
                if self.player and not self.player.is_dead:
                    slime_cx = self.x + self.width // 2
                    slime_cy = self.y + self.height // 2
                    px = self.player.x + self.player.width // 2
                    py = self.player.y + self.player.height // 2
                    if math.hypot(slime_cx - px, slime_cy - py) <= self.attack_range * 1.2:
                        self.player.health = max(0, self.player.health - self.contact_damage)
                        print(f"Slime2 đánh player! Máu player còn: {self.player.health}/{self.player.max_health}")
                        if self.player.health <= 0:
                            self.player.is_dead = True
            else:

                # Đang trong animation tấn công, không di chuyển
                self.dx = 0
                self.dy = 0
                self._update_animation(delta_time)
                return
        
        # QUAN TRỌNG: Tính khoảng cách từ PLAYER đến HOME (vị trí nhà cố định)
        px = self.player.x + self.player.width // 2
        py = self.player.y + self.player.height // 2
        
        home_center_x = self.home_x + self.width // 2
        home_center_y = self.home_y + self.height // 2
        
        # Khoảng cách từ player đến nhà
        dist_player_to_home = math.hypot(px - home_center_x, py - home_center_y)
        
        # Tính khoảng cách từ slime đến player
        slime_center_x = self.x + self.width // 2
        slime_center_y = self.y + self.height // 2
        dist_to_player = math.hypot(slime_center_x - px, slime_center_y - py)
        
        # Cập nhật hướng nhìn về phía player
        if self.player:
            angle = math.atan2(py - (self.y + self.height // 2), 
                              px - (self.x + self.width // 2))
            if abs(angle) < math.pi/4:
                self.direction = "right"
            elif abs(angle - math.pi) < math.pi/4:
                self.direction = "left"
            elif angle > math.pi/4 and angle < 3*math.pi/4:
                self.direction = "down"
            else:
                self.direction = "up"
        
        # KIỂM TRA KÍCH HOẠT TẤN CÔNG
        # Nếu player trong tầm tấn công và không đang tấn công
        if dist_to_player <= self.attack_range and self.state != "attack" and self.state != "return_home":
            self.state = "attack"
            self.is_attacking = True
            self.attack_start_time = current_time
            self.dx = 0
            self.dy = 0
            
            # Reset animation tấn công để chạy từ đầu
            if self.direction in self.attack_anims:
                self.attack_anims[self.direction].reset()
            if self.attack_sounds:   
                self.attack_sounds[self.attack_sound_index].play()
                self.attack_sound_index = (self.attack_sound_index + 1) % len(self.attack_sounds)
            
            print(f"Slime2 phát hiện player trong tầm {self.attack_range}px - Bắt đầu tấn công!")
            return
        
        # XỬ LÝ TRẠNG THÁI DỰA TRÊN HITBOX CỐ ĐỊNH
        # Kiểm tra player có ở trong vùng chase_range CỐ ĐỊNH không
        if dist_player_to_home <= self.home_chase_radius:
            # Player đang ở trong vùng đuổi theo (cố định tại nhà)
            if self.state == "idle":
                self.state = "walk"
                self.walk_start_time = current_time
                self.is_running = False
                print(f"Slime2 phát hiện player trong vùng {self.home_chase_radius}px - Bắt đầu đuổi")
            elif self.state == "walk":
                if current_time - self.walk_start_time >= self.walk_duration:
                    self.state = "run"
                    self.is_running = True
                    print("Slime2 chuyển sang chạy!")
            elif self.state == "return_home":
                # Đang quay về nhưng player lại vào vùng -> đuổi tiếp
                self.state = "walk"
                self.walk_start_time = current_time
                self.is_running = False
                print("Player quay lại vùng - Slime2 tiếp tục đuổi")
                
        elif dist_player_to_home > self.home_leave_radius:
            # Player ra khỏi vùng leave_range CỐ ĐỊNH -> quay về nhà
            if self.state != "return_home" and self.state != "idle" and self.state != "attack":
                self.state = "return_home"
                self.is_running = False
                print(f"Player ra khỏi vùng {self.home_leave_radius}px - Slime2 QUAY VỀ NHÀ")
        
        # XỬ LÝ TRẠNG THÁI "return_home" (quay về vị trí nhà)
        if self.state == "return_home":
            # Tính vector từ vị trí hiện tại về HOME
            dx_home = home_center_x - (self.x + self.width // 2)
            dy_home = home_center_y - (self.y + self.height // 2)
            dist_to_home = math.hypot(dx_home, dy_home)
            
            if dist_to_home < 10:
                # Đã về đến nhà
                self.state = "idle"
                self.dx = 0
                self.dy = 0
                # Đặt chính xác về vị trí home
                self.x = self.home_x
                self.y = self.home_y
                self.rect.x = self.x
                self.rect.y = self.y
                print("Slime2 đã về đến NHÀ!")
            else:
                # Di chuyển về nhà với tốc độ walk
                if dist_to_home > 0:
                    length = max(abs(dx_home), abs(dy_home), 0.1)
                    speed = PLAYER_SPEED * 0.5  # Tốc độ về nhà (chậm hơn plant)
                    self.dx = (dx_home / length) * speed
                    self.dy = (dy_home / length) * speed
                    
                    # Cập nhật hướng
                    if abs(dx_home) > abs(dy_home):
                        self.direction = "right" if dx_home > 0 else "left"
                    else:
                        self.direction = "down" if dy_home > 0 else "up"
        
        # XỬ LÝ ĐUỔI THEO (khi đang walk hoặc run)
        if self.state in ("walk", "run"):
            # Tính vector từ Slime đến Player
            target_x = self.player.x + self.player.width // 2
            target_y = self.player.y + self.player.height // 2
            dx_target = target_x - (self.x + self.width // 2)
            dy_target = target_y - (self.y + self.height // 2)
            distance = math.hypot(dx_target, dy_target)
            
            # Nếu đến gần player, dừng lại để tấn công (sẽ được xử lý ở đầu frame tiếp theo)
            if distance <= self.attack_range:
                self.dx = 0
                self.dy = 0
            elif distance > 5:  # Chỉ di chuyển nếu còn xa
                length = max(distance, 0.1)
                if self.state == "run":
                    speed = RUN_SPEED * 0.6  # Slime2 chạy chậm hơn plant
                else:
                    speed = PLAYER_SPEED * 0.4  # Slime2 đi chậm hơn plant
                self.dx = (dx_target / length) * speed
                self.dy = (dy_target / length) * speed
            else:
                self.dx = 0
                self.dy = 0
                if self.state == "run":
                    self.state = "walk"  # Chuyển sang walk khi đến gần
        
        # Dừng lại khi idle
        if self.state == "idle":
            self.dx = 0
            self.dy = 0
        
        # CẬP NHẬT VỊ TRÍ (có giới hạn map)
        new_x = self.x + self.dx
        new_y = self.y + self.dy
        if 0 <= new_x <= map_width - self.width:
            self.x = new_x
        if 0 <= new_y <= map_height - self.height:
            self.y = new_y
        self.rect.x = self.x
        self.rect.y = self.y
        
        # CẬP NHẬT ANIMATION
        self._update_animation(delta_time)

    # Chọn và cập nhật animation
    def _update_animation(self, delta_time):
        # Chọn dictionary animation
        if self.state == "idle":
            anim_dict = self.idle_anims
        elif self.state == "walk":
            anim_dict = self.walk_anims
        elif self.state == "run":
            anim_dict = self.run_anims
        elif self.state == "attack":
            anim_dict = self.attack_anims
        elif self.state == "hit":
            anim_dict = self.hit_anims
        elif self.state == "death":
            anim_dict = self.death_anims
        else:
            anim_dict = self.walk_anims if self.state == "return_home" else self.idle_anims
        
        # Lấy animation theo hướng
        anim = anim_dict.get(self.direction)
        if not anim and "down" in anim_dict:
            anim = anim_dict["down"]
        elif not anim and anim_dict:
            anim = list(anim_dict.values())[0]
            
        if anim:
            anim.update()
            self.image = anim.current_frame
            
            # Tạo hiệu ứng nhấp nháy khi bất tử (bị thương)
            if self.is_invincible and not self.is_dead:
                # Nhấp nháy bằng cách thay đổi độ alpha
                alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.015))
                if alpha < 128:
                    alpha = 128
                self.image.set_alpha(alpha)
            else:
                self.image.set_alpha(255)
            
            # Cập nhật rect giữ nguyên tâm
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
            self.width = self.image.get_width()
            self.height = self.image.get_height()
            self.body_radius = max(self.width, self.height) // 2
    
    # Vẽ Slime2 và hitbox
    def draw(self, screen, camera):
        #if self.is_dead:
        #    return
        
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        screen.blit(self.image, (screen_x, screen_y))
        
        if self.debug:
            # HITBOX DI ĐỘNG (thân slime) - màu tím
            center_x = self.x + self.width // 2 - camera.x
            center_y = self.y + self.height // 2 - camera.y
            
            # Hiển thị thanh máu
            bar_width = 40
            bar_height = 6
            bar_x = screen_x + (self.width - bar_width) // 2
            bar_y = screen_y - 15
            
            # Màu nền thanh máu (đỏ)
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # Màu máu hiện tại (xanh lá)
            health_percent = self.health / self.max_health
            current_bar_width = int(bar_width * health_percent)
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, current_bar_width, bar_height))
            
            pygame.draw.circle(screen, (128, 0, 128), (center_x, center_y), self.body_radius, 2)
            
            # Vùng tấn công (màu cam)
            pygame.draw.circle(screen, (255, 165, 0), (center_x, center_y), self.attack_range, 2)
            
            # HITBOX CỐ ĐỊNH TẠI VỊ TRÍ NHÀ
            home_center_x = self.home_x + self.width // 2 - camera.x
            home_center_y = self.home_y + self.height // 2 - camera.y
            
            # Hitbox 2: Vùng đuổi theo (màu vàng) - CỐ ĐỊNH
            pygame.draw.circle(screen, (255, 255, 0), (home_center_x, home_center_y), self.home_chase_radius, 2)
            
            # Hitbox 3: Vùng rời (màu đỏ) - CỐ ĐỊNH
            pygame.draw.circle(screen, (255, 0, 0), (home_center_x, home_center_y), self.home_leave_radius, 2)
            
            # Vẽ điểm nhà (hình vuông trắng)
            pygame.draw.rect(screen, (255, 255, 255), 
                            (home_center_x - 5, home_center_y - 5, 10, 10), 2)
            
            # Vẽ đường từ slime đến nhà
            pygame.draw.line(screen, (200, 200, 200), 
                            (center_x, center_y), 
                            (home_center_x, home_center_y), 1)
            
            # HIỂN THỊ THÔNG TIN DEBUG
            font = pygame.font.Font(None, 20)
            dist_to_home = math.hypot(
                (self.home_x + self.width//2) - (self.x + self.width//2),
                (self.home_y + self.height//2) - (self.y + self.height//2)
            )
            dist_text = font.render(f"Dist to home: {dist_to_home:.0f}", True, (255, 255, 255))
            screen.blit(dist_text, (screen_x, screen_y - 25))
            
            state_text = font.render(f"State: {self.state}", True, (255, 255, 0))
            screen.blit(state_text, (screen_x, screen_y - 45))
            
            # Hiển thị máu
            health_text = font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255))
            screen.blit(health_text, (screen_x, screen_y - 65))
    
    # Trả về hitbox thân (hình tròn)
    def get_hitbox(self):
        return (self.x + self.width//2, self.y + self.height//2, self.body_radius)