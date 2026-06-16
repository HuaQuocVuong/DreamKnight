import math
import random

import pygame

from test01 import Test01
from plant1 import Plant1
from plant2 import Plant2
from plant3 import Plant3
from slime1 import Slime1
from slime2 import Slime2
from slime3 import Slime3
from gold_drop import GoldDrop
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT

# ============================================================
#  CẤU HÌNH WAVE SYSTEM
# ============================================================

# WAVE_ORDER: Xác định thứ tự các đợt quái sẽ xuất hiện
# Mỗi đợt sẽ spawn một loại quái khác nhau theo thứ tự này
WAVE_ORDER = [
    "slime1",    # Đợt 1: Slime cấp 1 (yếu nhất)
    "slime2",    # Đợt 2: Slime cấp 2 (trung bình)
    "slime3",    # Đợt 3: Slime cấp 3 (mạnh nhất)
    "plant1",    # Đợt 4: Plant cấp 1
    "plant2",    # Đợt 5: Plant cấp 2
    "plant3",    # Đợt 6: Plant cấp 3 (mạnh nhất)
]

# ENEMIES_PER_WAVE: Số lượng quái sẽ spawn trong mỗi đợt
ENEMIES_PER_WAVE = 9

# ENEMIES_PER_BATCH: Số quái spawn mỗi lần (batch)
ENEMIES_PER_BATCH = 3  # Spawn 3 con mỗi lần

# SPAWN_INTERVAL: Thời gian (giây) giữa mỗi lần spawn batch
# Sau khi 3 con bị tiêu diệt, đợi 2 giây rồi spawn 3 con tiếp theo
SPAWN_INTERVAL = 2.0

# SPAWN_OFFSET: Khoảng cách (px) spawn quái ngoài rìa camera
SPAWN_OFFSET = 80

# GOLD_VALUES: Ánh xạ tên quái -> số vàng rơi khi quái chết
GOLD_VALUES = {
    "slime1": 10,  # Slime cấp 1 rơi 10 vàng
    "slime2": 20,  # Slime cấp 2 rơi 20 vàng
    "slime3": 30,  # Slime cấp 3 rơi 30 vàng
    "plant1": 15,  # Plant cấp 1 rơi 15 vàng
    "plant2": 25,  # Plant cấp 2 rơi 25 vàng
    "plant3": 35,  # Plant cấp 3 rơi 35 vàng
}

# ENEMY_CLASSES: Ánh xạ tên quái -> Class tương ứng
ENEMY_CLASSES = {
    "slime1": Slime1, "slime2": Slime2, "slime3": Slime3,
    "plant1": Plant1, "plant2": Plant2, "plant3": Plant3,
}

# DEFAULT_SCALE: Tỉ lệ scale mặc định cho tất cả quái
DEFAULT_SCALE = 2.0

class EnemyManager:
    """
    Lớp quản lý toàn bộ hệ thống quái vật trong game.
    Chịu trách nhiệm:
    - Spawn quái theo wave (mỗi lần 3 con)
    - Cập nhật AI và vị trí quái
    - Xử lý va chạm giữa các quái
    - Xử lý va chạm với đòn tấn công của player
    - Quản lý vàng rơi từ quái chết
    """
    
    def __init__(self, player):
        """
        Khởi tạo EnemyManager
        
        Args:
            player: Instance của player để biết vị trí và tương tác
        """
        # Lưu tham chiếu đến player để spawn quái xung quanh player
        self.player = player
        
        # Danh sách các vàng rơi trên map (chưa được nhặt)
        self.gold_drops = []
        
        # Danh sách quái đang sống trên map
        self.enemies = []

        # Quản lý wave hiện tại
        self.current_wave = 0          # Chỉ số wave hiện tại (0-based)
        self.wave_name_current = ""    # Tên wave hiện tại (ví dụ: "slime1")
        self.remaining_to_spawn = 0    # Số quái còn cần spawn trong wave này
        self.spawn_timer = 0.0         # Bộ đếm thời gian để spawn quái
        
        # Trạng thái spawn batch
        self.is_spawning = False       # Đang trong quá trình spawn batch
        self.batch_size = ENEMIES_PER_BATCH  # Số quái mỗi batch

        # Tham số điều chỉnh va chạm giữa các quái
        self.collision_strength = 0.3  # Lực đẩy (0.1 = rất nhẹ, 0.5 = vừa)
        self.min_separation = 5.0      # Khoảng cách tối thiểu giữa các quái

        # Bắt đầu spawn wave đầu tiên ngay khi khởi tạo
        self._start_wave(self.current_wave)

    # ------------------------------------------------------------------
    # XỬ LÝ VA CHẠM GIỮA CÁC ENEMY - CẢI TIẾN
    # ------------------------------------------------------------------

    def _handle_enemy_collisions(self):
        """
        Kiểm tra và xử lý va chạm giữa các enemy - phiên bản mềm mại
        
        Nguyên lý hoạt động:
        1. Duyệt qua tất cả cặp enemy
        2. Tính khoảng cách giữa 2 enemy
        3. Nếu khoảng cách < khoảng cách mong muốn -> đẩy ra xa
        4. Sử dụng lực đẩy mềm để tránh enemy bị bay lung tung
        """
        
        # Lặp lại 2 lần để ổn định vị trí sau khi đẩy
        # Giúp enemy không bị chồng lên nhau sau khi đẩy
        for _ in range(2):
            # Duyệt tất cả cặp enemy (i, j) với i < j để tránh trùng lặp
            for i in range(len(self.enemies)):
                for j in range(i + 1, len(self.enemies)):
                    enemy1 = self.enemies[i]
                    enemy2 = self.enemies[j]
                    
                    # Bỏ qua nếu enemy đã chết
                    if enemy1.is_dead or enemy2.is_dead:
                        continue
                    
                    # Lấy hitbox của 2 enemy
                    try:
                        # Lấy tâm (cx, cy) và bán kính của hitbox
                        cx1, cy1, radius1 = enemy1.get_hitbox()
                        cx2, cy2, radius2 = enemy2.get_hitbox()
                    except AttributeError:
                        # Fallback: Nếu enemy không có get_hitbox(), dùng rect để tính
                        # Tạo rect từ vị trí và kích thước của enemy
                        rect1 = pygame.Rect(enemy1.x, enemy1.y, enemy1.width, enemy1.height)
                        rect2 = pygame.Rect(enemy2.x, enemy2.y, enemy2.width, enemy2.height)
                        
                        # Nếu không va chạm rect, bỏ qua
                        if not rect1.colliderect(rect2):
                            continue
                        
                        # Tính tâm từ rect
                        cx1 = enemy1.x + enemy1.width / 2
                        cy1 = enemy1.y + enemy1.height / 2
                        cx2 = enemy2.x + enemy2.width / 2
                        cy2 = enemy2.y + enemy2.height / 2
                        
                        # Bán kính = 1/2 kích thước lớn nhất
                        radius1 = max(enemy1.width, enemy1.height) / 2
                        radius2 = max(enemy2.width, enemy2.height) / 2
                    
                    # Tính khoảng cách giữa 2 tâm
                    dx = cx2 - cx1
                    dy = cy2 - cy1
                    distance = math.hypot(dx, dy)  # distance = sqrt(dx^2 + dy^2)
                    
                    # Khoảng cách mong muốn = tổng bán kính + khoảng cách an toàn
                    desired_distance = radius1 + radius2 + self.min_separation
                    
                    # Chỉ xử lý khi khoảng cách nhỏ hơn desired_distance
                    # và distance > 0 để tránh chia cho 0
                    if distance < desired_distance and distance > 0.001:
                        # Tính overlap: phần chồng lên nhau
                        # Chia 2 vì cả 2 enemy sẽ được đẩy
                        overlap = (desired_distance - distance) / 2
                        
                        # Chuẩn hóa vector (dx, dy) để có vector đơn vị
                        dx /= distance
                        dy /= distance
                        
                        # ĐẨY MỀM: chỉ đẩy một phần của overlap
                        # collision_strength càng nhỏ đẩy càng nhẹ
                        push_amount = overlap * self.collision_strength
                        
                        # Giới hạn đẩy tối đa để tránh enemy bay xa đột ngột
                        max_push = 3.0
                        push_amount = min(push_amount, max_push)
                        
                        # Đẩy enemy ra xa nhau theo hướng ngược lại
                        # enemy1 bị đẩy về hướng ngược với enemy2
                        enemy1.x -= dx * push_amount
                        enemy1.y -= dy * push_amount
                        enemy2.x += dx * push_amount
                        enemy2.y += dy * push_amount
                        
                        # Giới hạn enemy trong map để không bị bay ra ngoài
                        self._clamp_enemy_to_map(enemy1)
                        self._clamp_enemy_to_map(enemy2)

    def _clamp_enemy_to_map(self, enemy):
        """
        Giới hạn enemy trong map để không bị bay ra ngoài
        
        Args:
            enemy: Enemy cần giới hạn
        """
        MARGIN = 10  # Khoảng cách lề an toàn từ rìa map
        # Giới hạn x trong [MARGIN, MAP_WIDTH - width - MARGIN]
        enemy.x = max(MARGIN, min(enemy.x, MAP_WIDTH - enemy.width - MARGIN))
        # Giới hạn y trong [MARGIN, MAP_HEIGHT - height - MARGIN]
        enemy.y = max(MARGIN, min(enemy.y, MAP_HEIGHT - enemy.height - MARGIN))

    # ------------------------------------------------------------------
    # PHƯƠNG PHÁP ALTERNATIVE: DÙNG LỰC ĐẨY DỰA TRÊN KHỐI LƯỢNG
    # ------------------------------------------------------------------

    def _handle_enemy_collisions_advanced(self):
        """
        Phiên bản nâng cao: đẩy dựa trên tốc độ và khối lượng (không sử dụng)
        
        Phương pháp này tính lực đẩy dựa trên:
        - Khoảng cách giữa 2 enemy
        - Tỉ lệ overlap so với kích thước
        - Không sử dụng trong code hiện tại nhưng có thể thay thế
        """
        
        # Lưu vị trí cũ để tính toán (dự phòng)
        positions = []
        for enemy in self.enemies:
            positions.append((enemy.x, enemy.y))
        
        # Xử lý va chạm
        for _ in range(2):
            for i in range(len(self.enemies)):
                for j in range(i + 1, len(self.enemies)):
                    enemy1 = self.enemies[i]
                    enemy2 = self.enemies[j]
                    
                    if enemy1.is_dead or enemy2.is_dead:
                        continue
                    
                    # Tính khoảng cách giữa 2 enemy
                    dx = (enemy1.x + enemy1.width/2) - (enemy2.x + enemy2.width/2)
                    dy = (enemy1.y + enemy1.height/2) - (enemy2.y + enemy2.height/2)
                    distance = math.hypot(dx, dy)
                    
                    # Khoảng cách tối thiểu = trung bình kích thước
                    min_distance = (max(enemy1.width, enemy1.height) + 
                                   max(enemy2.width, enemy2.height)) / 2
                    
                    # Nếu va chạm
                    if distance < min_distance and distance > 0.001:
                        # Tính lực đẩy tỉ lệ nghịch với khoảng cách
                        # Càng gần thì lực đẩy càng mạnh
                        force = (min_distance - distance) / min_distance
                        force = min(force, 0.5)  # Giới hạn lực tối đa
                        
                        # Chuẩn hóa vector
                        dx /= distance
                        dy /= distance
                        
                        # Áp dụng lực đẩy
                        push_x = dx * force * 0.5
                        push_y = dy * force * 0.5
                        
                        # Đẩy 2 enemy ra xa
                        enemy1.x += push_x
                        enemy1.y += push_y
                        enemy2.x -= push_x
                        enemy2.y -= push_y
                        
                        # Giới hạn trong map
                        self._clamp_enemy_to_map(enemy1)
                        self._clamp_enemy_to_map(enemy2)

    # ------------------------------------------------------------------
    # Update mỗi frame
    # ------------------------------------------------------------------

    def update(self, dt, map_width, map_height):
        """
        Cập nhật trạng thái của toàn bộ hệ thống quái vật
        
        Thứ tự xử lý:
        1. Kiểm tra và spawn batch quái mới nếu cần
        2. Cập nhật AI và vị trí của từng quái
        3. Xử lý va chạm giữa các quái
        4. Xử lý va chạm với đòn tấn công của player
        5. Xóa quái đã chết và tạo vàng rơi
        6. Chuyển sang wave tiếp theo nếu hết quái
        
        Args:
            dt: Delta time (thời gian giữa 2 frame)
            map_width: Chiều rộng map
            map_height: Chiều cao map
        """
        
        # ===== BƯỚC 1: SPAWN QUÁI THEO BATCH =====
        # Chỉ spawn khi còn quái cần spawn và số enemy hiện tại == 0
        # Điều này đảm bảo chỉ spawn batch mới khi đã đánh hết batch cũ
        if self.remaining_to_spawn > 0 and len(self.enemies) == 0:
            # Tăng bộ đếm thời gian
            self.spawn_timer += dt
            
            # Nếu đã đủ thời gian spawn (SPAWN_INTERVAL)
            if self.spawn_timer >= SPAWN_INTERVAL:
                # Reset timer
                self.spawn_timer = 0.0
                
                # Xác định số lượng quái sẽ spawn trong batch này
                # Lấy số nhỏ hơn giữa ENEMIES_PER_BATCH và remaining_to_spawn
                batch_count = min(ENEMIES_PER_BATCH, self.remaining_to_spawn)
                
                # Spawn batch quái
                for _ in range(batch_count):
                    self._spawn_one_enemy()
                    self.remaining_to_spawn -= 1
                
                print(f"[Wave {self.wave_number}] Spawn {batch_count} con {self.wave_name_current}, còn {self.remaining_to_spawn} con")

        # ===== BƯỚC 2: CẬP NHẬT QUÁI =====
        # Gọi update cho từng quái để di chuyển và xử lý AI
        for e in self.enemies:
            e.update(dt, map_width, map_height)

        # ===== BƯỚC 3: XỬ LÝ VA CHẠM QUÁI-QUÁI =====
        # Sau khi quái di chuyển, kiểm tra và xử lý va chạm
        self._handle_enemy_collisions()
        
        # ===== BƯỚC 4: XỬ LÝ TẤN CÔNG =====
        # Kiểm tra xem đòn tấn công của player có trúng quái nào không
        self._check_player_attack_collision()
        
        # ===== BƯỚC 5: XÓA QUÁI CHẾT =====
        # Xóa quái đã chết khỏi danh sách và tạo vàng rơi
        self._remove_dead()

        # ===== BƯỚC 6: CHUYỂN WAVE =====
        # Nếu đã spawn hết quái trong wave và không còn quái nào trên map
        if self.remaining_to_spawn == 0 and len(self.enemies) == 0:
            # Reset timer để chuẩn bị cho wave mới
            self.spawn_timer = 0.0
            
            # Chuyển sang wave tiếp theo
            next_wave = self.current_wave + 1
            # Kiểm tra còn wave không
            if next_wave < len(WAVE_ORDER):
                self.current_wave = next_wave
                self._start_wave(self.current_wave)
                print(f"[Wave] Chuyển sang đợt {self.wave_number}: {self.wave_name}")
            else:
                # Đã hoàn thành tất cả wave
                print("[Wave] Đã hoàn thành tất cả các đợt!")

        # ===== BƯỚC 7: CẬP NHẬT VÀNG =====
        # Loại bỏ vàng đã được nhặt
        self.gold_drops = [g for g in self.gold_drops if not g.collected]
        # Cập nhật vàng rơi (di chuyển đến player khi gần)
        for gold in self.gold_drops:
            gold.update(self.player)

    # ------------------------------------------------------------------
    # Các phương thức quản lý wave và spawn
    # ------------------------------------------------------------------

    def _start_wave(self, wave_index):
        """
        Bắt đầu một wave mới
        
        Args:
            wave_index: Chỉ số wave trong WAVE_ORDER
        """
        wave_name = WAVE_ORDER[wave_index]
        print(f"[Wave {wave_index + 1}] Bắt đầu đợt: {wave_name} x{ENEMIES_PER_WAVE} (mỗi lần {ENEMIES_PER_BATCH} con)")
        
        # Thiết lập thông tin wave
        self.wave_name_current = wave_name
        # Số quái cần spawn = ENEMIES_PER_WAVE
        self.remaining_to_spawn = ENEMIES_PER_WAVE
        # Reset timer spawn
        self.spawn_timer = 0.0
        
        # Spawn batch đầu tiên ngay lập tức
        batch_count = min(ENEMIES_PER_BATCH, self.remaining_to_spawn)
        for _ in range(batch_count):
            self._spawn_one_enemy()
            self.remaining_to_spawn -= 1
        print(f"[Wave {self.wave_number}] Spawn {batch_count} con {self.wave_name_current}, còn {self.remaining_to_spawn} con")

    def _spawn_one_enemy(self):
        """
        Spawn 1 con quái ở rìa ngoài tầm nhìn của player
        
        Quái sẽ spawn ở 1 trong 4 hướng: trên, dưới, trái, phải
        Vị trí spawn cách rìa camera SPAWN_OFFSET px để không xuất hiện đột ngột
        """
        # Lấy class của quái cần spawn từ wave hiện tại
        cls = ENEMY_CLASSES[self.wave_name_current]
        
        # Tính vị trí camera dựa trên vị trí player
        # Camera sẽ focus vào player nên góc trên trái camera = player - nửa màn hình
        cam_x = self.player.x - SCREEN_WIDTH // 2
        cam_y = self.player.y - SCREEN_HEIGHT // 2
        
        # Chọn ngẫu nhiên 1 trong 4 cạnh để spawn
        side = random.choice(["top", "bottom", "left", "right"])

        # Tính tọa độ spawn dựa trên cạnh được chọn
        if side == "top":
            # Spawn ở trên màn hình
            x = random.uniform(cam_x - SPAWN_OFFSET, cam_x + SCREEN_WIDTH + SPAWN_OFFSET)
            y = cam_y - SPAWN_OFFSET
        elif side == "bottom":
            # Spawn ở dưới màn hình
            x = random.uniform(cam_x - SPAWN_OFFSET, cam_x + SCREEN_WIDTH + SPAWN_OFFSET)
            y = cam_y + SCREEN_HEIGHT + SPAWN_OFFSET
        elif side == "left":
            # Spawn ở bên trái màn hình
            x = cam_x - SPAWN_OFFSET
            y = random.uniform(cam_y - SPAWN_OFFSET, cam_y + SCREEN_HEIGHT + SPAWN_OFFSET)
        else:  # right
            # Spawn ở bên phải màn hình
            x = cam_x + SCREEN_WIDTH + SPAWN_OFFSET
            y = random.uniform(cam_y - SPAWN_OFFSET, cam_y + SCREEN_HEIGHT + SPAWN_OFFSET)

        # Giới hạn spawn trong map, không spawn quá sát rìa
        MARGIN = 200  # Khoảng cách an toàn từ rìa map
        x = max(MARGIN, min(x, MAP_WIDTH - MARGIN))
        y = max(MARGIN, min(y, MAP_HEIGHT - MARGIN))

        # Tạo instance của quái
        e = cls(x, y, scale_factor=DEFAULT_SCALE)
        # Truyền player vào để quái biết mục tiêu
        e.set_player(self.player)
        # Thêm vào danh sách quái
        self.enemies.append(e)
        # Đồng bộ danh sách quái với player
        self._sync_enemies()

    def _sync_enemies(self):
        """
        Đồng bộ danh sách enemy cho player
        
        Player cần biết danh sách enemy để xử lý va chạm và tấn công
        """
        self.player.set_enemies(self.enemies)

    # ------------------------------------------------------------------
    # Xử lý tấn công và vàng rơi
    # ------------------------------------------------------------------

    def _check_player_attack_collision(self):
        """
        Kiểm tra va chạm giữa đòn tấn công của player và enemy
        
        Nguyên lý:
        1. Lấy hitbox đòn tấn công của player
        2. Duyệt qua từng enemy
        3. Kiểm tra xem hitbox có chạm vào enemy không
        4. Nếu có, gọi enemy.take_damage()
        """
        # Lấy hitbox đòn tấn công (có thể là None nếu không tấn công)
        attack_hitbox = self.player.get_attack_hitbox()
        if not attack_hitbox:
            return
        
        # Duyệt từng enemy
        for enemy in self.enemies:
            if enemy.is_dead:
                continue
            
            try:
                # Lấy hitbox của enemy (tâm và bán kính)
                cx, cy, radius = enemy.get_hitbox()
                
                # Tìm điểm gần nhất trên attack_hitbox đến tâm enemy
                closest_x = max(attack_hitbox.left, min(cx, attack_hitbox.right))
                closest_y = max(attack_hitbox.top, min(cy, attack_hitbox.bottom))
                
                # Tính khoảng cách từ điểm gần nhất đến tâm enemy
                dx = closest_x - cx
                dy = closest_y - cy
                
                # Nếu khoảng cách < bán kính => va chạm
                if dx * dx + dy * dy < radius * radius:
                    # Gây sát thương cho enemy
                    enemy.take_damage(self.player.damage)
                    
            except AttributeError:
                # Fallback: Dùng rect collision nếu enemy không có get_hitbox()
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                if attack_hitbox.colliderect(enemy_rect):
                    enemy.take_damage(self.player.damage)

    # Xóa quái đã chết khỏi danh sách và tạo vàng rơi
    # Quái chết sẽ:
    # 1. Tạo GoldDrop tại vị trí quái
    # 2. Bị xóa khỏi danh sách enemies
    def _remove_dead(self):
        alive = []      # Danh sách quái còn sống
        changed = False # Có quái nào bị xóa không
        
        for e in self.enemies:
            if e.fully_dead:
                # Quái đã chết hoàn toàn (animation chết đã xong)
                
                # Lấy số vàng quái này rơi
                gold_value = self._get_gold_value(e)
                
                # Vị trí quái chết (tâm)
                cx = e.x + e.width // 2
                cy = e.y + e.height // 2
                
                # Tạo vàng rơi
                self.gold_drops.append(GoldDrop(cx, cy, value=gold_value))
                changed = True
            else:
                # Quái vẫn sống, giữ lại
                alive.append(e)
        
        # Nếu có quái bị xóa, cập nhật danh sách
        if changed:
            self.enemies = alive
            self._sync_enemies()

    # Trả về giá trị vàng dựa theo class của quái
    def _get_gold_value(self, enemy):
        
        # Tạo mapping ngược: class -> tên
        class_to_name = {v: k for k, v in ENEMY_CLASSES.items()}
        # Lấy tên quái từ class
        name = class_to_name.get(type(enemy), "slime1")
        # Trả về giá trị vàng tương ứng
        return GOLD_VALUES.get(name, 5)

    # ------------------------------------------------------------------
    # Thuộc tính tiện ích
    # ------------------------------------------------------------------

    # Số đợt hiện tại (bắt đầu từ 1)
    @property
    def wave_number(self):
        return self.current_wave + 1

    # Tên loại quái đang spawn trong đợt này
    @property
    def wave_name(self):
        return WAVE_ORDER[self.current_wave]

    # ------------------------------------------------------------------
    # Vẽ
    # ------------------------------------------------------------------
    
    # Vẽ toàn bộ quái và vàng rơi lên surface
    # surface: Surface để vẽ lên
    # camera: Camera để chuyển đổi tọa độ thế giới sang màn hình
    def draw(self, surface, camera):
        # Vẽ từng quái
        for e in self.enemies:
            e.draw(surface, camera)
        # Vẽ từng vàng rơi
        for gold in self.gold_drops:
            gold.draw(surface, camera)