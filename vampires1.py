import pygame
import os
import math
from config import PLAYER_SPEED, RUN_SPEED
from vampires1_animation import Vampires1AnimationLoader

# CLASS VAMPIRES1 — Kẻ địch vampires1
# Mô tả: Class quản lý quái vật Vampires1 với đầy đủ animation, AI đuổi theo, tấn công và nhận sát thương
class Vampires1(pygame.sprite.Sprite):

    # KHỞI TẠO — Thiết lập các thuộc tính ban đầu cho quái vật
    def __init__(self, x, y, scale_factor=2.0):
        super().__init__()

        # Vị trí hiện tại & vị trí nhà (spawn point)
        self.x      = float(x)
        self.y      = float(y)
        self.home_x = float(x)  # Vị trí gốc - hiện không dùng do quái luôn đuổi theo player
        self.home_y = float(y)  

        # Tải toàn bộ animation qua loader — mỗi trạng thái có 4 hướng (up/down/left/right)
        all_anims = Vampires1AnimationLoader.load_all(scale_factor)
        self.idle_anims   = all_anims["idle"]   # Animation đứng yên
        self.walk_anims   = all_anims["walk"]   # Animation đi bộ (tốc độ chậm)
        self.run_anims    = all_anims["run"]    # Animation chạy (tốc độ nhanh)
        self.attack_anims = all_anims["attack"] # Animation tấn công
        self.hit_anims    = all_anims["hit"]    # Animation bị thương
        self.death_anims  = all_anims["death"]  # Animation chết

        # Trạng thái hiện tại của quái
        self.direction   = "down"   # Hướng nhìn: up/down/left/right
        self.state       = "idle"   # Trạng thái: idle/walk/run/attack/hit/death

        self.is_attacking = False   # Cờ đang tấn công — để hệ thống khác kiểm tra va chạm

        # Hệ thống di chuyển
        self.speed = 0.0    # Tốc độ tổng (không dùng trực tiếp, tham khảo)
        self.dx    = 0.0    # Vận tốc theo trục X (pixel/frame)
        self.dy    = 0.0    # Vận tốc theo trục Y (pixel/frame)

        # Hệ số nhân tốc độ — điều chỉnh tốc độ quái so với PLAYER_SPEED/RUN_SPEED
        self.run_speed_multiplier = 0.4    # Tốc độ chạy = RUN_SPEED * 0.4
        self.walk_speed_multiplier = 0.3   # Tốc độ đi bộ = PLAYER_SPEED * 0.3

         # Thời gian chuyển đổi trạng thái (miligiây)
        self.walk_duration     = 1200   # Sau 1.2s đi bộ sẽ chuyển sang chạy
        self.attack_range      = 45     # Phạm vi kích hoạt tấn công (pixel)     
        self.attack_duration   = 700    # Thời gian animation tấn công kéo dài

       # Biến theo dõi thời gian các trạng thái
        self.walk_start_time      = 0       # Thời điểm bắt đầu đi bộ
        self.is_running           = False   # Cờ đang ở trạng thái chạy
        self.attack_start_time    = 0       # Thời điểm bắt đầu tấn công
        self.attack_sound_index   = 0       # Chỉ số âm thanh tấn công (luân phiên Attack1/Attack2)

        # Hệ thống máu và sát thương
        self.health     = 500       # Máu hiện tại
        self.contact_damage = 40    # Sát thương khi player chạm vào quái
        self.max_health = 500       # Máu tối đa

        # Thời gian cho trạng thái bị thương và chết
        self.hit_start_time       = 0       # Thời điểm bắt đầu bị thương
        self.hit_duration         = 300     # Thời gian animation hit (ms)
        self.death_start_time     = 0       # Thời điểm bắt đầu chết
        self.death_frame_duration = 85      # Thời gian mỗi frame animation chết
        self.death_frames_count   = 6       # Số frame trong animation chết

        # Tổng thời gian chết = Thời gian mỗi frame animation chết * Số frame trong animation chết
        self.death_duration = self.death_frame_duration * self.death_frames_count 

        # Cờ trạng thái đặc biệt
        self.is_dead       = False  # Đã chết (đang chạy animation chết)
        self.fully_dead    = False  # Hoàn toàn chết (animation kết thúc, có thể xóa khỏi game)
        self.is_invincible = False  # Bất tử tạm thời sau khi bị đánh
        self.invincible_duration = 500    # Thời gian bất tử (ms)
        self.invincible_start_time = 0    # Thời điểm bắt đầu bất tử

        # Tham chiếu player
        self.player = None

        # Hình ảnh & rect ban đầu — lấy từ animation idle hướng down
        start_frame = self.idle_anims["down"].current_frame
        self.image  = start_frame
        self.rect   = self.image.get_rect(center=(self.x, self.y))
        self.width  = self.image.get_width()    # Chiều rộng sprite
        self.height = self.image.get_height()   # Chiều cao sprite
        
        self.body_radius = 20    # Bán kính hitbox hình tròn (dùng kiểm tra va chạm)
        
        # Cờ debug — True/False hiển thị thông tin debug (hitbox, thanh máu,...)
        #self.debug = True
        self.debug = False

         # Âm thanh — tấn công, bị thương, chết
        self.attack_sounds = []     # Danh sách âm thanh tấn công (2 file: Attack1.mp3, Attack2.mp3)
        self.hit_sound     = None   # Âm thanh khi bị đánh
        self.death_sound   = None   # Âm thanh khi chết
        self._load_sounds()         # Tải tất cả âm thanh

    # ÂM THANH — Tải các file âm thanh cho quái vật
    def _load_sounds(self):
        sound_path = os.path.join("03_sounds", "slime3")
        try:
            # Tải 2 âm thanh tấn công (Attack1.mp3, Attack2.mp3) để luân phiên
            for i in range(1, 3):
                path = os.path.join(sound_path, f"Attack{i}.mp3")
                self.attack_sounds.append(pygame.mixer.Sound(path))

            # Tải âm thanh bị thương và chết=
            self.hit_sound   = pygame.mixer.Sound(os.path.join(sound_path, "hit.mp3"))
            self.death_sound = pygame.mixer.Sound(os.path.join(sound_path, "Death.mp3"))
        except Exception as e:
            print(f"[Vampires1] Lỗi load âm thanh: {e}")


    # API CÔNG KHAI — Các phương thức được gọi từ bên ngoài (main game loop)

    #Gán tham chiếu đến player để AI có thể theo dõi và tấn công
    def set_player(self, player):
        self.player = player

    # Nhận sát thương từ player, trả về True nếu nhận sát thương thành công
    # Nếu đã chết hoặc đang bất tử: bỏ qua
    # Nếu máu <= 0: kích hoạt trạng thái chết
    # Nếu còn máu: kích hoạt trạng thái bị thương + bất tử tạm thời
    def take_damage(self, damage) -> bool:
        if self.is_dead or self.is_invincible:
            return False

        self.health -= damage
        print(f"[Vampires1] Nhận {damage} sát thương! Máu còn: {self.health}/{self.max_health}")

        if self.health <= 0:
            self.health = 0
            self.die()
        else:
            self._start_hit()

        return True

    # Xử lý khi quái vật chết:
    # - Đặt cờ chết.
    # - Chuyển sang animation death.
    # - Dừng mọi di chuyển và tấn công.
    # - Phát âm thanh chết.
    def die(self):
        if self.is_dead:
            return
        self.is_dead        = True
        self.state          = "death"
        self.death_start_time = pygame.time.get_ticks() # Lưu thời điểm bắt đầu để tính khi nào kết thúc
        self.dx = self.dy   = 0     # Dừng di chuyển
        self.is_attacking   = False # Hủy tấn công

        if self.death_sound:
            self.death_sound.play()
        if self.direction in self.death_anims:
            self.death_anims[self.direction].reset()    # Reset animation về frame đầu

    # Lấy thông tin hitbox hình tròn: (center_x, center_y, radius) 
    # Dùng để kiểm tra va chạm với player và các object khác
    def get_hitbox(self):
    
        return (self.rect.centerx, self.rect.centery, self.body_radius)

    # UPDATE CHÍNH — Được gọi mỗi frame từ game loop.

    # Cập nhật trạng thái và vị trí của quái mỗi frame
    # - Tham số:
    # + delta_time: thời gian giữa các frame (ms) - dùng để đồng bộ animation.
    # + map_width, map_height: kích thước bản đồ để giới hạn di chuyển.
    def update(self, delta_time, map_width, map_height):
        if self.player is None:
            return  # Chưa có player, không làm gì

        current_time = pygame.time.get_ticks()
        self._update_invincible(current_time)   # Kiểm tra hết thời gian bất tử.

        # Trạng thái chết: chạy animation chết và kiểm tra kết thúc. 
        if self.state == "death":
            self._update_animation(delta_time)
            if current_time - self.death_start_time >= self.death_duration:
                self.fully_dead = True
            return

        # Trạng thái bị thương: dừng di chuyển, chạy animation hit.
        if self.state == "hit":
            if current_time - self.hit_start_time >= self.hit_duration:
                # Hết thời gian hit: chuyển về idle hoặc walk tùy trạng thái trước đó.
                self.state = "idle" if not self.is_running else "walk"
            else:
                self.dx = self.dy = 0   # Dừng di chuyển khi đang bị thương.
                self._update_animation(delta_time)
                return

        # Trạng thái tấn công: dừng di chuyển, chạy animation attack.
        if self.state == "attack":
            if current_time - self.attack_start_time >= self.attack_duration:
                self._end_attack()  # Kết thúc tấn công và gây sát thương.
            else:
                self.dx = self.dy = 0   # Dừng di chuyển khi đang tấn công
                self._update_animation(delta_time)
                return

        # Tính khoảng cách đến player để quyết định hành vi.
        px, py           = self._player_center()
        slime_cx         = self.x + self.width  // 2    # Tâm X của quái
        slime_cy         = self.y + self.height // 2    # Tâm Y của quái
        dist_to_player   = math.hypot(slime_cx - px,  slime_cy - py)    # Khoảng cách Euclid

        # Cập nhật hướng nhìn về phía player (dùng cho animation)
        self._update_direction(px, py)

        # Kích hoạt tấn công nếu player trong phạm vi attack_range
        if dist_to_player <= self.attack_range and self.state != "attack":
            self._start_attack(current_time)
            return

        # Bỏ cơ chế về nhà - luôn đuổi theo player
        # Khi ở idle và phát hiện player: chuyển sang walk
        if self.state == "idle":
            self.state = "walk"
            self.walk_start_time = current_time
            self.is_running = False
        elif self.state == "walk":
            # Tăng tốc độ di chuyển sang chạy
            if current_time - self.walk_start_time >= self.walk_duration:
                self.state = "run"
                self.is_running = True

        # Đuổi theo player (cả walk và run đều dùng chung logic đuổi)
        if self.state in ("walk", "run"):
            self._handle_chase(px, py)

        # Áp dụng di chuyển và cập nhật animation
        self._apply_movement(map_width, map_height)
        self._update_animation(delta_time)

    # INTERNAL — AI / MOVEMENT — Xử lý logic di chuyển và đuổi bắt

    #Lấy tọa độ trung tâm của player (dùng để tính hướng và khoảng cách)
    def _player_center(self):
        return (
            self.player.x + self.player.width  // 2,
            self.player.y + self.player.height // 2,
        )

    """
    Cập nhật hướng nhìn (direction) dựa vào vị trí player
    Tính góc giữa quái và player, quy về 4 hướng chính:
    - Góc gần 0: hướng phải (right)
    - Góc gần π: hướng trái (left)
    - Góc π/4 đến 3π/4: hướng xuống (down)
    - Còn lại: hướng lên (up) 
    """
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
    
    """
    Xử lý đuổi theo player:
    - Tính vector hướng từ quái đến player
    - Nếu đã đến gần (<= attack_range hoặc <= 5px): dừng lại
    - Nếu đang chạy: dùng RUN_SPEED, đang đi bộ: dùng PLAYER_SPEED (có hệ số)
    - Chuẩn hóa vector và nhân với tốc độ tương ứng 
    """
    def _handle_chase(self, target_x, target_y):
        dx = target_x - (self.x + self.width  // 2)
        dy = target_y - (self.y + self.height // 2)
        dist = math.hypot(dx, dy)

        # Dừng lại nếu đã đến gần player (trong phạm vi tấn công hoặc quá sát)
        if dist <= self.attack_range or dist <= 5:
            self.dx = self.dy = 0
            if self.state == "run":
                self.state = "walk" # Giảm tốc khi đến gần
            return

        # Tính tốc độ dựa trên trạng thái (run nhanh hơn walk)
        if self.state == "run":
            speed = RUN_SPEED * self.run_speed_multiplier
        else:
            speed = PLAYER_SPEED * self.walk_speed_multiplier
        
        # Di chuyển về phía player
        self.dx = (dx / dist) * speed
        self.dy = (dy / dist) * speed

    """
    Áp dụng di chuyển với giới hạn bản đồ:
    - Cập nhật vị trí X, Y với dx, dy
    - Giới hạn không cho ra ngoài bản đồ (0 đến map_width/height)
    - Cập nhật lại rect để đồng bộ với vị trí mới
    """
    def _apply_movement(self, map_width, map_height):
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        # Giới hạn di chuyển trong phạm vi bản đồ
        if 0 <= new_x <= map_width  - self.width:
            self.x = new_x
        if 0 <= new_y <= map_height - self.height:
            self.y = new_y
        self.rect.x = self.x
        self.rect.y = self.y

    
    # INTERNAL — TRẠNG THÁI — Xử lý chuyển đổi giữa các trạng thái

    """
    Bắt đầu trạng thái bị thương:
    - Chuyển state sang 'hit'
    - Dừng di chuyển
    - Kích hoạt bất tử tạm thời (invincible) để tránh bị đánh liên tục
    - Phát âm thanh bị thương
    - Reset animation hit
    """
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

    """
    Bắt đầu trạng thái tấn công:
    - Chuyển state sang 'attack', bật cờ is_attacking
    - Dừng di chuyển
    - Reset animation attack
    - Phát âm thanh tấn công (luân phiên giữa 2 file)
    """
    def _start_attack(self, current_time):
        self.state              = "attack"
        self.is_attacking       = True
        self.attack_start_time  = current_time
        self.dx = self.dy       = 0
        if self.direction in self.attack_anims:
            self.attack_anims[self.direction].reset()
        if self.attack_sounds:
            self.attack_sounds[self.attack_sound_index].play()
            self.attack_sound_index = (self.attack_sound_index + 1) % len(self.attack_sounds)   # Luân phiên âm thanh
        print(f"[Vampires1] Bắt đầu tấn công (dist <= {self.attack_range}px)")


    """
    Kết thúc trạng thái tấn công:
    - Chuyển về idle hoặc run (tùy trạng thái trước đó)
    - Tắt cờ is_attacking
    - Kiểm tra player có trong phạm vi tấn công không để gây sát thương
    - Phạm vi gây sát thương = attack_range * 1.3 (rộng hơn phạm vi kích hoạt)
    """
    def _end_attack(self):
        """Kết thúc trạng thái tấn công"""
        self.state        = "idle" if not self.is_running else "run"
        self.is_attacking = False
        if self.direction in self.attack_anims:
            self.attack_anims[self.direction].reset()
        # Gây sát thương cho player
        if self.player and not self.player.is_dead:
            import math
            vampires1_cx = self.x + self.width // 2
            vampires1_cy = self.y + self.height // 2
            px = self.player.x + self.player.width // 2
            py = self.player.y + self.player.height // 2
            if math.hypot(vampires1_cx - px, vampires1_cy - py) <= self.attack_range * 1.3:
                self.player.take_damage(10)
    
    # Cập nhật trạng thái bất tử: tự động tắt sau invincible_duration (500ms)
    # Bất tử giúp quái không bị đánh liên tục, tạo khoảng nghỉ giữa các lần nhận sát thương
    def _update_invincible(self, current_time):
        if self.is_invincible:
            if current_time - self.invincible_start_time >= self.invincible_duration:
                self.is_invincible = False

   
    # INTERNAL — ANIMATION — Cập nhật và quản lý animation

    """
    Cập nhật animation hiện tại dựa trên state và direction:
    - Chọn animation phù hợp từ anim_map
    - Cập nhật frame animation
    - Xử lý hiệu ứng nhấp nháy khi bất tử (thay đổi alpha)
    - Đồng bộ rect với kích thước frame mới
    - Cập nhật body_radius cho hitbox
    """
    def _update_animation(self, delta_time):
        # Map trạng thái -> dictionary animation tương ứng
        anim_map = {
            "idle":        self.idle_anims,
            "walk":        self.walk_anims,
            "run":         self.run_anims,
            "attack":      self.attack_anims,
            "hit":         self.hit_anims,
            "death":       self.death_anims,
        }
        # Lấy animation theo state và direction, fallback về 'down' hoặc animation đầu tiên
        anim_dict = anim_map.get(self.state, self.idle_anims)
        anim      = anim_dict.get(self.direction) \
                    or anim_dict.get("down") \
                    or (next(iter(anim_dict.values())) if anim_dict else None)

        if not anim:
            return  # Không có animation, bỏ qua

        anim.update()   # Tiến tới frame tiếp theo
        self.image = anim.current_frame

        # Hiệu ứng nhấp nháy khi bất tử: thay đổi độ trong suốt (alpha) theo thời gian
        # Dùng hàm sin để tạo hiệu ứng nhấp nháy mượt mà
        if self.is_invincible and not self.is_dead:
            alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.015))
            self.image.set_alpha(max(128, alpha))   
            self.image.set_alpha(max(128, alpha))   # Alpha dao động 128-255
        else:
            self.image.set_alpha(255)   # Bình thường: hiển thị đầy đủ


        # Cập nhật rect để khớp với frame animation mới (kích thước có thể thay đổi)
        old_center = self.rect.center   # Giữ tâm cũ
        self.rect = self.image.get_rect()
        self.rect.center = old_center   # Gán lại tâm cũ
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.body_radius = 20   # Giữ bán kính hitbox cố định


    # VẼ — Render quái vật lên màn hình (Dành để debug)

    # Vẽ quái lên màn hình với tọa độ đã điều chỉnh theo camera
    # Nếu bật debug: vẽ thêm thanh máu, hitbox, phạm vi tấn công và thông tin trạng thái
    def draw(self, screen, camera):
        # Tính tọa độ trên màn hình (trừ đi vị trí camera)
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        screen.blit(self.image, (screen_x, screen_y))

        # Chỉ vẽ debug nếu cờ debug được bật
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

        # Vẽ gồm: 
        # hitbox (hình tròn tím) 
        # Phạm vi tấn công (hình tròn cam)
        pygame.draw.circle(screen, (128, 0, 128), (cx, cy), self.body_radius, 2)    # Hitbox
        pygame.draw.circle(screen, (255, 165, 0),  (cx, cy), self.attack_range, 2)  # Phạm vi tấn công

        # Vẽ thông tin debug: máu và trạng thái hiện tại
        font = pygame.font.Font(None, 20)
        for i, text in enumerate([
            f"HP: {self.health}/{self.max_health}",
            f"State: {self.state}",
        ]):
            surf = font.render(text, True, (255, 255, 0))   # Text màu vàng
            screen.blit(surf, (screen_x, screen_y - 45 + i * 20))   # Vẽ phía trên quái