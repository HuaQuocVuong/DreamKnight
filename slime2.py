import pygame
import os
import math
from config import PLAYER_SPEED, RUN_SPEED
from slime2_animation import Slime2AnimationLoader

# ================================================================================================
# CLASS SLIME2 — Kẻ địch Slime 2 (tốc độ trung bình, luôn đuổi theo player)
# ================================================================================================

class Slime2(pygame.sprite.Sprite):

    # ------------------------------------------------------------------
    # KHỞI TẠO
    # ------------------------------------------------------------------

    def __init__(self, x, y, scale_factor=2.0):
        """
        Khởi tạo Slime2 với animation, AI, máu, âm thanh
        x, y: vị trí spawn
        scale_factor: hệ số phóng to sprite (mặc định 2.0)
        """
        super().__init__()

        # Vị trí hiện tại & vị trí spawn (home) — dùng cho AI chase/return
        self.x      = float(x)
        self.y      = float(y)
        self.home_x = float(x)
        self.home_y = float(y)

        # Tải tất cả animation (idle, walk, run, attack, hit, death) từ loader
        all_anims = Slime2AnimationLoader.load_all(scale_factor)
        self.idle_anims   = all_anims["idle"]
        self.walk_anims   = all_anims["walk"]
        self.run_anims    = all_anims["run"]
        self.attack_anims = all_anims["attack"]
        self.hit_anims    = all_anims["hit"]
        self.death_anims  = all_anims["death"]

        # Trạng thái hiện tại
        self.direction    = "down"       # Hướng nhìn: up/down/left/right
        self.state        = "idle"       # Trạng thái: idle/walk/run/attack/hit/death
        self.is_attacking = False        # Cờ đang tấn công (dùng cho va chạm)

        # Vận tốc di chuyển (pixel/frame)
        self.speed = 0.0
        self.dx    = 0.0  # Vận tốc trục X
        self.dy    = 0.0  # Vận tốc trục Y

        # Hệ số tốc độ — Slime2 nhanh hơn Slime1 nhưng chậm hơn Slime3
        self.run_speed_multiplier  = 0.45  # Tốc độ chạy = RUN_SPEED * 0.45
        self.walk_speed_multiplier = 0.35  # Tốc độ đi bộ = PLAYER_SPEED * 0.35

        # Tham số hành vi AI
        self.walk_duration   = 1200    # Sau 1.2s đi bộ → tự động chuyển sang chạy
        self.attack_range    = 45      # Phạm vi kích hoạt tấn công (px)
        self.attack_duration = 600     # Thời gian animation tấn công (ms)

        # Biến theo dõi thời gian cho state machine
        self.walk_start_time    = 0    # Thời điểm bắt đầu đi bộ
        self.is_running         = False
        self.attack_start_time  = 0    # Thời điểm bắt đầu tấn công
        self.attack_sound_index = 0    # Luân phiên Attack1.mp3 / Attack2.mp3

        # Chỉ số máu và sát thương
        self.health         = 200      # Máu hiện tại (thấp hơn Slime3)
        self.contact_damage = 20       # Sát thương khi player chạm vào
        self.attack_damage  = 40       # Sát thương khi tấn công (có thể điều chỉnh dễ dàng)
        self.max_health     = 200      # Máu tối đa

        # Thời gian cho trạng thái hit (bị thương) & death (chết)
        self.hit_start_time       = 0
        self.hit_duration         = 300   # 300ms animation bị thương
        self.death_start_time     = 0
        self.death_frame_duration = 85    # 85ms mỗi frame chết
        self.death_frames_count   = 6     # 6 frame animation chết
        self.death_duration = self.death_frame_duration * self.death_frames_count  # Tổng 510ms

        # Cờ trạng thái đặc biệt
        self.is_dead       = False        # Đang chạy animation chết
        self.fully_dead    = False        # Animation chết xong → có thể xóa khỏi game
        self.is_invincible = False        # Bất tử tạm thời sau khi bị đánh
        self.invincible_duration   = 500  # Thời gian bất tử 500ms
        self.invincible_start_time = 0

        # Tham chiếu player — dùng cho AI tính toán đuổi theo
        self.player = None

        # Hình ảnh & hitbox ban đầu — lấy frame đầu tiên của idle down
        start_frame = self.idle_anims["down"].current_frame
        self.image  = start_frame
        self.rect   = self.image.get_rect(center=(self.x, self.y))
        self.width  = self.image.get_width()
        self.height = self.image.get_height()
        self.body_radius = 20  # Bán kính hitbox tròn để kiểm tra va chạm
        
        # Cờ debug — bật/tắt vẽ hitbox, thanh máu, phạm vi tấn công
        #self.debug = True
        self.debug = False

        # Load âm thanh (tấn công, bị thương, chết)
        self.attack_sounds = []  # Danh sách 2 âm thanh tấn công
        self.hit_sound     = None
        self.death_sound   = None
        self._load_sounds()

    # ------------------------------------------------------------------
    # ÂM THANH
    # ------------------------------------------------------------------

    def _load_sounds(self):
        """Tải âm thanh từ thư mục 03_sounds/slime1 (Attack1, Attack2, hit0, Death)"""
        sound_path = os.path.join("03_sounds", "slime1")
        try:
            # 2 âm thanh tấn công để luân phiên
            for i in range(1, 3):
                path = os.path.join(sound_path, f"Attack{i}.mp3")
                self.attack_sounds.append(pygame.mixer.Sound(path))
            # Âm thanh bị thương & chết (slime1 dùng hit0.mp3 thay vì hit.mp3)
            self.hit_sound   = pygame.mixer.Sound(os.path.join(sound_path, "hit0.mp3"))
            self.death_sound = pygame.mixer.Sound(os.path.join(sound_path, "Death.mp3"))
        except Exception as e:
            print(f"[Slime1] Lỗi load âm thanh: {e}")

    # ------------------------------------------------------------------
    # API CÔNG KHAI
    # ------------------------------------------------------------------

    def set_player(self, player):
        """Gán tham chiếu player cho AI đuổi theo"""
        self.player = player

    # Nhận sát thương từ player — trả về True nếu thành công, False nếu đang chết/bất tử
    def take_damage(self, damage) -> bool:
        if self.is_dead or self.is_invincible:
            return False

        self.health -= damage
        print(f"[Slime2] Nhận {damage} sát thương! Máu còn: {self.health}/{self.max_health}")

        if self.health <= 0:
            self.health = 0
            self.die()          # Máu hết → chết
        else:
            self._start_hit()   # Còn máu → bị thương + bất tử

        return True

    # Kích hoạt trạng thái chết: dừng di chuyển, phát âm thanh, chạy animation death
    def die(self):
        if self.is_dead:
            return
        self.is_dead        = True
        self.state          = "death"
        self.death_start_time = pygame.time.get_ticks()  # Lưu thời điểm bắt đầu chết
        self.dx = self.dy   = 0      # Dừng mọi di chuyển
        self.is_attacking   = False  # Hủy tấn công nếu đang
        if self.death_sound:
            self.death_sound.play()
        if self.direction in self.death_anims:
            self.death_anims[self.direction].reset()

    # Trả về hitbox tròn (center_x, center_y, radius) để kiểm tra va chạm
    def get_hitbox(self):
        #return (self.x + self.width // 2, self.y + self.height // 2, self.body_radius)
        return (self.rect.centerx, self.rect.centery, self.body_radius)

    # ------------------------------------------------------------------
    # UPDATE CHÍNH — Gọi mỗi frame từ game loop
    # ------------------------------------------------------------------

    def update(self, delta_time, map_width, map_height):
        """
        Cập nhật toàn bộ logic mỗi frame:
        - Xử lý state machine (death → hit → attack → chase)
        - Tính toán AI đuổi theo player
        - Cập nhật vị trí và animation
        """
        if self.player is None:
            return

        current_time = pygame.time.get_ticks()
        self._update_invincible(current_time)  # Kiểm tra hết thời gian bất tử

        # --- Trạng thái chết: chạy animation, kiểm tra kết thúc ---
        if self.state == "death":
            self._update_animation(delta_time)
            if current_time - self.death_start_time >= self.death_duration:
                self.fully_dead = True  # Đánh dấu có thể xóa khỏi game
            return

        # --- Trạng thái bị thương: dừng di chuyển, chờ hết hit_duration ---
        if self.state == "hit":
            if current_time - self.hit_start_time >= self.hit_duration:
                # Hết thời gian bị thương → về idle hoặc walk
                self.state = "idle" if not self.is_running else "walk"
            else:
                self.dx = self.dy = 0  # Đứng yên khi bị thương
                self._update_animation(delta_time)
                return

        # --- Trạng thái tấn công: dừng di chuyển, chờ animation kết thúc ---
        if self.state == "attack":
            if current_time - self.attack_start_time >= self.attack_duration:
                self._end_attack()  # Kết thúc tấn công → gây sát thương
            else:
                self.dx = self.dy = 0  # Đứng yên khi tấn công
                self._update_animation(delta_time)
                return

        # --- Tính toán khoảng cách giữa các đối tượng ---
        px, py           = self._player_center()   # Tâm player
        home_cx, home_cy = self._home_center()     # Tâm vị trí spawn
        slime_cx         = self.x + self.width  // 2   # Tâm slime
        slime_cy         = self.y + self.height // 2

        dist_player_to_home = math.hypot(px - home_cx,   py - home_cy)  # Khoảng cách player → home
        dist_to_player      = math.hypot(slime_cx - px,  slime_cy - py) # Khoảng cách slime → player

        # Cập nhật hướng nhìn về phía player (cho animation đúng hướng)
        self._update_direction(px, py)

        # Trong phạm vi tấn công → kích hoạt attack
        if dist_to_player <= self.attack_range and self.state != "attack":
            self._start_attack(current_time)
            return

        # Cập nhật trạng thái AI: idle → walk → run
        self._update_state_by_zone(dist_player_to_home, current_time)

        # Thực hiện hành vi theo trạng thái
        if self.state in ("walk", "run"):
            self._handle_chase(px, py)  # Đuổi theo player
        elif self.state == "idle":
            self.dx = self.dy = 0       # Đứng yên

        # Áp dụng di chuyển + cập nhật animation
        self._apply_movement(map_width, map_height)
        self._update_animation(delta_time)

    # ------------------------------------------------------------------
    # INTERNAL — AI / MOVEMENT
    # ------------------------------------------------------------------

    # Tọa độ trung tâm player (dùng để tính hướng và khoảng cách)
    def _player_center(self):
        return (
            self.player.x + self.player.width  // 2,
            self.player.y + self.player.height // 2,
        )

    # Tọa độ trung tâm vị trí spawn
    def _home_center(self):
        return (
            self.home_x + self.width  // 2,
            self.home_y + self.height // 2,
        )

    # Cập nhật hướng nhìn (direction) dựa vào góc giữa slime và player
    def _update_direction(self, px, py):
        angle = math.atan2(py - (self.y + self.height // 2),
                           px - (self.x + self.width  // 2))
        # Góc ≈ 0 → phải, ≈ π → trái, π/4~3π/4 → xuống, còn lại → lên
        if abs(angle) < math.pi / 4:
            self.direction = "right"
        elif abs(angle - math.pi) < math.pi / 4 or abs(angle + math.pi) < math.pi / 4:
            self.direction = "left"
        elif math.pi / 4 <= angle <= 3 * math.pi / 4:
            self.direction = "down"
        else:
            self.direction = "up"

    # Cập nhật trạng thái AI: idle → walk (phát hiện player), walk → run (sau 1.2s)
    def _update_state_by_zone(self, dist_player_to_home, current_time):
        # Luôn chase player, không return home
        if self.state == "idle":
            self.state           = "walk"
            self.walk_start_time = current_time
            self.is_running      = False
        elif self.state == "walk":
            if current_time - self.walk_start_time >= self.walk_duration:
                self.state       = "run"
                self.is_running  = True

    # Đuổi theo player — dừng nếu trong phạm vi tấn công hoặc quá sát (≤5px)
    def _handle_chase(self, target_x, target_y):
        dx = target_x - (self.x + self.width  // 2)
        dy = target_y - (self.y + self.height // 2)
        dist = math.hypot(dx, dy)

        # Đã đến đủ gần → dừng
        if dist <= self.attack_range or dist <= 5:
            self.dx = self.dy = 0
            if self.state == "run":
                self.state = "walk"  # Giảm tốc khi đến gần
            return

        # Chọn tốc độ dựa trên trạng thái (run nhanh hơn walk)
        if self.state == "run":
            speed = RUN_SPEED * self.run_speed_multiplier      # 0.45 lần tốc độ chạy
        else:
            speed = PLAYER_SPEED * self.walk_speed_multiplier  # 0.35 lần tốc độ đi bộ
        
        # Chuẩn hóa vector hướng và nhân với tốc độ
        self.dx = (dx / dist) * speed
        self.dy = (dy / dist) * speed

    # Áp dụng di chuyển với giới hạn bản đồ
    def _apply_movement(self, map_width, map_height):
        new_x = self.x + self.dx
        new_y = self.y + self.dy
        # Giới hạn không cho ra ngoài bản đồ
        if 0 <= new_x <= map_width  - self.width:
            self.x = new_x
        if 0 <= new_y <= map_height - self.height:
            self.y = new_y
        self.rect.x = self.x
        self.rect.y = self.y

    # ------------------------------------------------------------------
    # INTERNAL — TRẠNG THÁI (hit, attack, invincible)
    # ------------------------------------------------------------------

    # Bắt đầu trạng thái bị thương: dừng di chuyển, bật bất tử, phát âm thanh
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

    # Bắt đầu tấn công: dừng di chuyển, phát âm thanh, reset animation
    def _start_attack(self, current_time):
        self.state              = "attack"
        self.is_attacking       = True
        self.attack_start_time  = current_time
        self.dx = self.dy       = 0
        if self.direction in self.attack_anims:
            self.attack_anims[self.direction].reset()
        # Phát âm thanh tấn công (luân phiên 2 file)
        if self.attack_sounds:
            self.attack_sounds[self.attack_sound_index].play()
            self.attack_sound_index = (self.attack_sound_index + 1) % len(self.attack_sounds)
        print(f"[Slime2] Bắt đầu tấn công (dist <= {self.attack_range}px)")

    # Kết thúc tấn công: gây sát thương nếu player còn trong phạm vi
    def _end_attack(self):
        self.state        = "idle" if not self.is_running else "run"
        self.is_attacking = False
        if self.direction in self.attack_anims:
            self.attack_anims[self.direction].reset()
        # Gây sát thương nếu player trong phạm vi attack_range * 1.3
        if self.player and not self.player.is_dead:
            import math
            slime_cx = self.x + self.width // 2
            slime_cy = self.y + self.height // 2
            px = self.player.x + self.player.width // 2
            py = self.player.y + self.player.height // 2
            if math.hypot(slime_cx - px, slime_cy - py) <= self.attack_range * 1.3:
                # Sử dụng self.attack_damage thay vì hardcode 40
                self.player.take_damage(self.attack_damage)

    # Tự động tắt trạng thái bất tử sau 500ms
    def _update_invincible(self, current_time):
        if self.is_invincible:
            if current_time - self.invincible_start_time >= self.invincible_duration:
                self.is_invincible = False

    # ------------------------------------------------------------------
    # INTERNAL — ANIMATION
    # ------------------------------------------------------------------

    def _update_animation(self, delta_time):
        """
        Cập nhật animation hiện tại:
        - Chọn animation theo state + direction
        - Xử lý hiệu ứng nhấp nháy khi bất tử
        - Đồng bộ rect với kích thước frame mới
        """
        anim_map = {
            "idle":        self.idle_anims,
            "walk":        self.walk_anims,
            "run":         self.run_anims,
            "attack":      self.attack_anims,
            "hit":         self.hit_anims,
            "death":       self.death_anims,
        }
        anim_dict = anim_map.get(self.state, self.idle_anims)
        anim      = anim_dict.get(self.direction) \
                    or anim_dict.get("down") \
                    or (next(iter(anim_dict.values())) if anim_dict else None)

        if not anim:
            return

        anim.update()  # Tiến tới frame tiếp theo
        self.image = anim.current_frame

        # Hiệu ứng nhấp nháy khi bất tử (alpha dao động 128-255)
        if self.is_invincible and not self.is_dead:
            alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.015))
            self.image.set_alpha(max(128, alpha))
        else:
            self.image.set_alpha(255)  # Bình thường: hiển thị đầy đủ

        # Cập nhật rect giữ nguyên tâm
        old_center      = self.rect.center
        self.rect       = self.image.get_rect()
        self.rect.center = old_center
        self.width      = self.image.get_width()
        self.height     = self.image.get_height()
        self.body_radius = 20

    # ------------------------------------------------------------------
    # VẼ — Render slime lên màn hình (có debug nếu bật)
    # ------------------------------------------------------------------

    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        screen.blit(self.image, (screen_x, screen_y))

        # Chỉ vẽ debug nếu bật cờ
        if not self.debug:
            return

        cx = int(self.x + self.width  // 2 - camera.x)
        cy = int(self.y + self.height // 2 - camera.y)

        # Thanh máu (nền đỏ, fill xanh lá)
        bar_w, bar_h = 40, 6
        bar_x = int(screen_x + (self.width - bar_w) // 2)
        bar_y = int(screen_y - 15)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (0, 255, 0),
                         (bar_x, bar_y, int(bar_w * self.health / self.max_health), bar_h))

        # Hitbox (tím) + phạm vi tấn công (cam)
        pygame.draw.circle(screen, (128, 0, 128), (cx, cy), self.body_radius, 2)
        pygame.draw.circle(screen, (255, 165, 0),  (cx, cy), self.attack_range, 2)

        # Vị trí home: vàng = chase_radius, đỏ = leave_radius, trắng = tâm
        hcx = int(self.home_x + self.width  // 2 - camera.x)
        hcy = int(self.home_y + self.height // 2 - camera.y)
        pygame.draw.circle(screen, (255, 255, 0), (hcx, hcy), self.home_chase_radius, 2)
        pygame.draw.circle(screen, (255, 0,   0), (hcx, hcy), self.home_leave_radius, 2)
        pygame.draw.rect(screen,   (255, 255, 255), (hcx - 5, hcy - 5, 10, 10), 2)
        pygame.draw.line(screen,   (200, 200, 200), (cx, cy), (hcx, hcy), 1)

        # Text debug: HP, State, Dist home
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