import pygame
import os
import math
from config import PLAYER_SPEED, RUN_SPEED
from plant1_animation import Plant1AnimationLoader

# ================================================================================================
# CLASS PLANT1 — Kẻ địch Plant
# ================================================================================================

class Plant1(pygame.sprite.Sprite):

    # ------------------------------------------------------------------
    # KHỞI TẠO
    # ------------------------------------------------------------------

    def __init__(self, x, y, scale_factor=2.0):
        super().__init__()

        # Vị trí & vị trí nhà
        self.x      = float(x)
        self.y      = float(y)
        self.home_x = float(x)
        self.home_y = float(y)

        # Tải toàn bộ animation qua loader
        all_anims = Plant1AnimationLoader.load_all(scale_factor)
        self.idle_anims   = all_anims["idle"]
        self.walk_anims   = all_anims["walk"]
        self.run_anims    = all_anims["run"]
        self.attack_anims = all_anims["attack"]
        self.hit_anims    = all_anims["hit"]
        self.death_anims  = all_anims["death"]

        # Trạng thái
        self.direction   = "down"
        self.state       = "idle"
        self.is_attacking = False

        # Di chuyển
        self.speed = 0.0
        self.dx    = 0.0
        self.dy    = 0.0

        
        self.home_chase_radius = 250
        self.home_leave_radius = 450
        self.walk_duration     = 1200   # ms trước khi chuyển sang run
        self.attack_range      = 45
        self.attack_duration   = 600    # ms cho animation tấn công

        self.walk_start_time      = 0
        self.is_running           = False
        self.attack_start_time    = 0
        self.attack_sound_index   = 0

        # Máu
        self.health     = 500
        self.contact_damage = 15         # Sát thương khi chạm vào player
        self.max_health = 500

        # Thời gian trạng thái
        self.hit_start_time       = 0
        self.hit_duration         = 300
        self.death_start_time     = 0
        self.death_frame_duration = 85
        self.death_frames_count   = 10
        self.death_duration = self.death_frame_duration * self.death_frames_count  # 340 ms

        # Cờ trạng thái
        self.is_dead       = False
        self.fully_dead    = False
        self.is_invincible = False
        self.invincible_duration   = 500
        self.invincible_start_time = 0

        # Tham chiếu player
        self.player = None

        # Hình ảnh & rect ban đầu
        start_frame = self.idle_anims["down"].current_frame
        self.image  = start_frame
        self.rect   = self.image.get_rect(center=(self.x, self.y))
        self.width  = self.image.get_width()
        self.height = self.image.get_height()
        self.body_radius = 20
        
        # Debug
        self.debug = False

        # Âm thanh
        self.attack_sounds = []
        self.hit_sound     = None
        self.death_sound   = None
        self._load_sounds()

    # ------------------------------------------------------------------
    # ÂM THANH
    # ------------------------------------------------------------------

    def _load_sounds(self):
        sound_path = os.path.join("03_sounds", "slime3")
        try:
            for i in range(1, 3):
                path = os.path.join(sound_path, f"Attack{i}.mp3")
                if os.path.exists(path):
                    self.attack_sounds.append(pygame.mixer.Sound(path))
            hit_path = os.path.join(sound_path, "hit.mp3")
            if os.path.exists(hit_path):
                self.hit_sound = pygame.mixer.Sound(hit_path)
            death_path = os.path.join(sound_path, "Death.mp3")
            if os.path.exists(death_path):
                self.death_sound = pygame.mixer.Sound(death_path)
        except Exception as e:
            print(f"[Plant1] Lỗi load âm thanh: {e}")

    # ------------------------------------------------------------------
    # API CÔNG KHAI
    # ------------------------------------------------------------------

    def set_player(self, player):
        self.player = player

    def take_damage(self, damage) -> bool:
        if self.is_dead or self.is_invincible:
            return False

        self.health -= damage
        print(f"[Plant1] Nhận {damage} sát thương! Máu còn: {self.health}/{self.max_health}")

        if self.health <= 0:
            self.health = 0
            self.die()
        else:
            self._start_hit()

        return True

    def die(self):
        if self.is_dead:
            return
        self.is_dead        = True
        self.state          = "death"
        self.death_start_time = pygame.time.get_ticks()
        self.dx = self.dy   = 0
        self.is_attacking   = False
        if self.death_sound:
            self.death_sound.play()
        if self.direction in self.death_anims:
            self.death_anims[self.direction].reset()

    def get_hitbox(self):
        return (self.rect.centerx, self.rect.centery, self.body_radius)

    # ------------------------------------------------------------------
    # UPDATE CHÍNH
    # ------------------------------------------------------------------

    def update(self, delta_time, map_width, map_height):
        if self.player is None:
            return

        current_time = pygame.time.get_ticks()
        self._update_invincible(current_time)

        # --- Chết ---
        if self.state == "death":
            self._update_animation(delta_time)
            if current_time - self.death_start_time >= self.death_duration:
                self.fully_dead = True
            return

        # --- Bị thương ---
        if self.state == "hit":
            if current_time - self.hit_start_time >= self.hit_duration:
                self.state = "idle" if not self.is_running else "walk"
            else:
                self.dx = self.dy = 0
                self._update_animation(delta_time)
                return

        # --- Đang tấn công ---
        if self.state == "attack":
            if current_time - self.attack_start_time >= self.attack_duration:
                self._end_attack()
            else:
                self.dx = self.dy = 0
                self._update_animation(delta_time)
                return

        # --- Tính khoảng cách ---
        px, py           = self._player_center()
        home_cx, home_cy = self._home_center()
        plant_cx         = self.x + self.width  // 2
        plant_cy         = self.y + self.height // 2

        dist_player_to_home = math.hypot(px - home_cx,   py - home_cy)
        dist_to_player      = math.hypot(plant_cx - px,  plant_cy - py)

        # Cập nhật hướng nhìn về phía player
        self._update_direction(px, py)

        # Kích hoạt tấn công
        if dist_to_player <= self.attack_range and self.state not in ("attack", "return_home"):
            self._start_attack(current_time)
            return

        # Cập nhật trạng thái AI theo vùng
        self._update_state_by_zone(dist_player_to_home, current_time)

        # Xử lý về nhà
        if self.state == "return_home":
            self._handle_return_home(home_cx, home_cy)
        elif self.state in ("walk", "run"):
            self._handle_chase(px, py)
        elif self.state == "idle":
            self.dx = self.dy = 0

        # Cập nhật vị trí
        self._apply_movement(map_width, map_height)
        self._update_animation(delta_time)

    # ------------------------------------------------------------------
    # INTERNAL — AI / MOVEMENT
    # ------------------------------------------------------------------

    def _player_center(self):
        return (
            self.player.x + self.player.width  // 2,
            self.player.y + self.player.height // 2,
        )

    def _home_center(self):
        return (
            self.home_x + self.width  // 2,
            self.home_y + self.height // 2,
        )

    def _update_direction(self, px, py):
        angle = math.atan2(py - (self.y + self.height // 2),
                           px - (self.x + self.width  // 2))
        if abs(angle) < math.pi / 4:
            self.direction = "right"
        elif abs(angle - math.pi) < math.pi / 4 or abs(angle + math.pi) < math.pi / 4:
            self.direction = "left"
        elif math.pi / 4 <= angle <= 3 * math.pi / 4:
            self.direction = "down"
        else:
            self.direction = "up"

    def _update_state_by_zone(self, dist_player_to_home, current_time):
        if dist_player_to_home <= self.home_chase_radius:
            if self.state == "idle":
                self.state          = "walk"
                self.walk_start_time = current_time
                self.is_running     = False
                print("[Plant1] Phát hiện player — bắt đầu đuổi")
            elif self.state == "walk":
                if current_time - self.walk_start_time >= self.walk_duration:
                    self.state      = "run"
                    self.is_running = True
                    print("[Plant1] Chuyển sang chạy!")
            elif self.state == "return_home":
                self.state          = "walk"
                self.walk_start_time = current_time
                self.is_running     = False
        elif dist_player_to_home > self.home_leave_radius:
            if self.state not in ("return_home", "idle", "attack"):
                self.state      = "return_home"
                self.is_running = False
                print("[Plant1] Player ra khỏi vùng — quay về nhà")

    def _handle_return_home(self, home_cx, home_cy):
        dx = home_cx - (self.x + self.width  // 2)
        dy = home_cy - (self.y + self.height // 2)
        dist = math.hypot(dx, dy)

        if dist < 10:
            self.state = "idle"
            self.dx = self.dy = 0
            self.x, self.y    = self.home_x, self.home_y
            self.rect.x, self.rect.y = self.x, self.y
            print("[Plant1] Đã về nhà!")
        else:
            speed    = PLAYER_SPEED * 0.5
            self.dx  = (dx / dist) * speed
            self.dy  = (dy / dist) * speed
            self.direction = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) \
                             else ("down" if dy > 0 else "up")

    def _handle_chase(self, target_x, target_y):
        dx = target_x - (self.x + self.width  // 2)
        dy = target_y - (self.y + self.height // 2)
        dist = math.hypot(dx, dy)

        if dist <= self.attack_range or dist <= 5:
            self.dx = self.dy = 0
            if self.state == "run":
                self.state = "walk"
            return

        speed   = RUN_SPEED * 0.6 if self.state == "run" else PLAYER_SPEED * 0.4
        self.dx = (dx / dist) * speed
        self.dy = (dy / dist) * speed

    def _apply_movement(self, map_width, map_height):
        new_x = self.x + self.dx
        new_y = self.y + self.dy
        if 0 <= new_x <= map_width  - self.width:
            self.x = new_x
        if 0 <= new_y <= map_height - self.height:
            self.y = new_y
        self.rect.x = self.x
        self.rect.y = self.y

    # ------------------------------------------------------------------
    # INTERNAL — TRẠNG THÁI
    # ------------------------------------------------------------------

    def _start_hit(self):
        self.state          = "hit"
        self.hit_start_time = pygame.time.get_ticks()
        self.dx = self.dy   = 0
        self.is_invincible  = True
        self.invincible_start_time = self.hit_start_time
        if self.hit_sound:
            self.hit_sound.play()
        if self.direction in self.hit_anims:
            self.hit_anims[self.direction].reset()

    def _start_attack(self, current_time):
        self.state              = "attack"
        self.is_attacking       = True
        self.attack_start_time  = current_time
        self.dx = self.dy       = 0
        if self.direction in self.attack_anims:
            self.attack_anims[self.direction].reset()
        if self.attack_sounds:
            self.attack_sounds[self.attack_sound_index].play()
            self.attack_sound_index = (self.attack_sound_index + 1) % len(self.attack_sounds)
        print(f"[Plant1] Bắt đầu tấn công (dist <= {self.attack_range}px)")

    def _end_attack(self):
        self.state        = "idle" if not self.is_running else "run"
        self.is_attacking = False
        if self.direction in self.attack_anims:
            self.attack_anims[self.direction].reset()
        if self.player and not self.player.is_dead:
            import math
            plant_cx = self.x + self.width // 2
            plant_cy = self.y + self.height // 2
            px = self.player.x + self.player.width // 2
            py = self.player.y + self.player.height // 2
            if math.hypot(plant_cx - px, plant_cy - py) <= self.attack_range * 1.3:
                self.player.take_damage(10)

    def _update_invincible(self, current_time):
        if self.is_invincible:
            if current_time - self.invincible_start_time >= self.invincible_duration:
                self.is_invincible = False

    # ------------------------------------------------------------------
    # INTERNAL — ANIMATION
    # ------------------------------------------------------------------

    def _update_animation(self, delta_time):
        anim_map = {
            "idle":        self.idle_anims,
            "walk":        self.walk_anims,
            "run":         self.run_anims,
            "attack":      self.attack_anims,
            "hit":         self.hit_anims,
            "death":       self.death_anims,
            "return_home": self.walk_anims,
        }
        anim_dict = anim_map.get(self.state, self.idle_anims)
        anim      = anim_dict.get(self.direction) \
                    or anim_dict.get("down") \
                    or (next(iter(anim_dict.values())) if anim_dict else None)

        if not anim:
            return

        anim.update()
        self.image = anim.current_frame

        # Nhấp nháy khi bất tử
        if self.is_invincible and not self.is_dead:
            alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.015))
            self.image.set_alpha(max(128, alpha))
        else:
            self.image.set_alpha(255)

        old_center      = self.rect.center
        self.rect       = self.image.get_rect()
        self.rect.center = old_center
        self.width      = self.image.get_width()
        self.height     = self.image.get_height()
        self.body_radius = 20

    # ------------------------------------------------------------------
    # VẼ
    # ------------------------------------------------------------------

    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        screen.blit(self.image, (screen_x, screen_y))

        if not self.debug:
            return

        cx = int(self.x + self.width  // 2 - camera.x)
        cy = int(self.y + self.height // 2 - camera.y)

        # Thanh máu
        bar_w, bar_h = 40, 6
        bar_x = int(screen_x + (self.width - bar_w) // 2)
        bar_y = int(screen_y - 15)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (0, 255, 0),
                         (bar_x, bar_y, int(bar_w * self.health / self.max_health), bar_h))

        pygame.draw.circle(screen, (34, 139, 34), (cx, cy), self.body_radius, 2)
        pygame.draw.circle(screen, (255, 165, 0),  (cx, cy), self.attack_range, 2)

        hcx = int(self.home_x + self.width  // 2 - camera.x)
        hcy = int(self.home_y + self.height // 2 - camera.y)
        pygame.draw.circle(screen, (255, 255, 0), (hcx, hcy), self.home_chase_radius, 2)
        pygame.draw.circle(screen, (255, 0,   0), (hcx, hcy), self.home_leave_radius, 2)
        pygame.draw.rect(screen,   (255, 255, 255), (hcx - 5, hcy - 5, 10, 10), 2)
        pygame.draw.line(screen,   (200, 200, 200), (cx, cy), (hcx, hcy), 1)

        font = pygame.font.Font(None, 20)
        dist_home = math.hypot(
            (self.home_x + self.width  // 2) - (self.x + self.width  // 2),
            (self.home_y + self.height // 2) - (self.y + self.height // 2),
        )
        for i, text in enumerate([
            f"HP: {self.health}/{self.max_health}",
            f"State: {self.state}",
            f"Dist home: {dist_home:.0f}",
        ]):
            surf = font.render(text, True, (255, 255, 0))
            screen.blit(surf, (screen_x, screen_y - 65 + i * 20))