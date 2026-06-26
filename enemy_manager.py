import math
import random
import pygame

from plant1 import Plant1
from plant2 import Plant2
from plant3 import Plant3

from slime1 import Slime1
from slime2 import Slime2
from slime3 import Slime3

from vampires1 import Vampires1

from gold_drop import GoldDrop
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT

# ================================================================================================
# CẤU HÌNH WAVE SYSTEM
# ================================================================================================

# Thứ tự các đợt quái sẽ xuất hiện
WAVE_ORDER = [
    "slime1",    # Đợt 1: Slime cấp 1 (yếu nhất)
    "slime2",    # Đợt 2: Slime cấp 2 (trung bình)
    "slime3",    # Đợt 3: Slime cấp 3 (mạnh nhất)
    "plant1",    # Đợt 4: Plant cấp 1
    "plant2",    # Đợt 5: Plant cấp 2
    "plant3",    # Đợt 6: Plant cấp 3 (mạnh nhất)
    "vampire",   # Đợt 7: Vampire (boss)
]

# Số lượng quái mỗi đợt
ENEMIES_PER_WAVE = 15

# Số quái spawn mỗi batch
ENEMIES_PER_BATCH = 3

# Thời gian giữa các batch (giây)
SPAWN_INTERVAL = 2.0

# Khoảng cách spawn ngoài rìa camera (px)
SPAWN_OFFSET = 80

# Số vàng rơi tương ứng với từng loại quái
GOLD_VALUES = {
    "slime1": 20,
    "slime2": 40,
    "slime3": 80,
    "plant1": 40,
    "plant2": 80,
    "plant3": 160,
    "vampire": 200,
}

# Ánh xạ tên quái → Class
ENEMY_CLASSES = {
    "slime1": Slime1, "slime2": Slime2, "slime3": Slime3,
    "plant1": Plant1, "plant2": Plant2, "plant3": Plant3,
    "vampire": Vampires1,
}

# Tỉ lệ scale mặc định cho tất cả quái
DEFAULT_SCALE = 2.0


# ================================================================================================
# CLASS ENEMYMANAGER — Quản lý toàn bộ hệ thống quái vật
# Chịu trách nhiệm: spawn wave, cập nhật AI, va chạm, vàng rơi
# ================================================================================================

class EnemyManager:
    def __init__(self, player):
        # Tham chiếu player để spawn quái xung quanh
        self.player = player
        
        # Danh sách vàng rơi chưa nhặt
        self.gold_drops = []
        
        # Danh sách quái đang sống
        self.enemies = []

        # Quản lý wave
        self.current_wave = 0           # Chỉ số wave hiện tại (0-based)
        self.wave_name_current = ""     # Tên wave hiện tại
        self.remaining_to_spawn = 0     # Số quái còn cần spawn
        self.spawn_timer = 0.0          # Bộ đếm thời gian spawn batch
        self.all_waves_completed = False  # Đã hoàn thành tất cả wave

        # Tham số va chạm giữa các quái
        self.collision_strength = 0.3   # Lực đẩy (0.1 = nhẹ, 0.5 = vừa)
        self.min_separation = 5.0       # Khoảng cách tối thiểu giữa các quái

        # Bắt đầu wave đầu tiên
        self._start_wave(self.current_wave)

    # ------------------------------------------------------------------
    # XỬ LÝ VA CHẠM GIỮA CÁC ENEMY
    # ------------------------------------------------------------------

    # Kiểm tra và đẩy các quái ra xa nhau nếu chồng lấn
    def _handle_enemy_collisions(self):
        # Lặp 2 lần để ổn định vị trí sau đẩy
        for _ in range(2):
            for i in range(len(self.enemies)):
                for j in range(i + 1, len(self.enemies)):
                    enemy1 = self.enemies[i]
                    enemy2 = self.enemies[j]
                    
                    if enemy1.is_dead or enemy2.is_dead:
                        continue
                    
                    try:
                        # Lấy hitbox tròn (cx, cy, radius)
                        cx1, cy1, radius1 = enemy1.get_hitbox()
                        cx2, cy2, radius2 = enemy2.get_hitbox()
                    except AttributeError:
                        # Fallback: dùng rect nếu không có get_hitbox()
                        rect1 = pygame.Rect(enemy1.x, enemy1.y, enemy1.width, enemy1.height)
                        rect2 = pygame.Rect(enemy2.x, enemy2.y, enemy2.width, enemy2.height)
                        
                        if not rect1.colliderect(rect2):
                            continue
                        
                        cx1 = enemy1.x + enemy1.width / 2
                        cy1 = enemy1.y + enemy1.height / 2
                        cx2 = enemy2.x + enemy2.width / 2
                        cy2 = enemy2.y + enemy2.height / 2
                        
                        radius1 = max(enemy1.width, enemy1.height) / 2
                        radius2 = max(enemy2.width, enemy2.height) / 2
                    
                    # Vector giữa 2 tâm
                    dx = cx2 - cx1
                    dy = cy2 - cy1
                    distance = math.hypot(dx, dy)
                    
                    # Khoảng cách mong muốn
                    desired_distance = radius1 + radius2 + self.min_separation
                    
                    if distance < desired_distance and distance > 0.001:
                        # Phần chồng lấn / 2 (mỗi enemy bị đẩy 1 nửa)
                        overlap = (desired_distance - distance) / 2
                        
                        # Chuẩn hóa vector
                        dx /= distance
                        dy /= distance
                        
                        # Đẩy mềm (chỉ đẩy 1 phần overlap)
                        push_amount = overlap * self.collision_strength
                        push_amount = min(push_amount, 3.0)  # Giới hạn đẩy tối đa
                        
                        # Đẩy ngược hướng nhau
                        enemy1.x -= dx * push_amount
                        enemy1.y -= dy * push_amount
                        enemy2.x += dx * push_amount
                        enemy2.y += dy * push_amount
                        
                        # Giới hạn trong map
                        self._clamp_enemy_to_map(enemy1)
                        self._clamp_enemy_to_map(enemy2)

    # Giới hạn enemy trong map
    def _clamp_enemy_to_map(self, enemy):
        MARGIN = 10
        enemy.x = max(MARGIN, min(enemy.x, MAP_WIDTH - enemy.width - MARGIN))
        enemy.y = max(MARGIN, min(enemy.y, MAP_HEIGHT - enemy.height - MARGIN))

    # ------------------------------------------------------------------
    # UPDATE MỖI FRAME
    # ------------------------------------------------------------------

    def update(self, dt, map_width, map_height):
        # 1. Spawn batch mới nếu hết quái trên map và còn quái cần spawn
        if self.remaining_to_spawn > 0 and len(self.enemies) == 0:
            self.spawn_timer += dt
            
            if self.spawn_timer >= SPAWN_INTERVAL:
                self.spawn_timer = 0.0
                
                batch_count = min(ENEMIES_PER_BATCH, self.remaining_to_spawn)
                for _ in range(batch_count):
                    self._spawn_one_enemy()
                    self.remaining_to_spawn -= 1
                
                print(f"[Wave {self.wave_number}] Spawn {batch_count} con {self.wave_name_current}, còn {self.remaining_to_spawn} con")

        # 2. Cập nhật AI từng quái
        for e in self.enemies:
            e.update(dt, map_width, map_height)

        # 3. Xử lý va chạm quái-quái
        self._handle_enemy_collisions()
        
        # 4. Kiểm tra đòn tấn công của player
        self._check_player_attack_collision()
        
        # 5. Xóa quái chết + tạo vàng rơi
        self._remove_dead()

        # 6. Chuyển wave nếu hết quái
        if self.remaining_to_spawn == 0 and len(self.enemies) == 0:
            self.spawn_timer = 0.0
            
            next_wave = self.current_wave + 1
            if next_wave < len(WAVE_ORDER):
                self.current_wave = next_wave
                self._start_wave(self.current_wave)
                print(f"[Wave] Chuyển sang đợt {self.wave_number}: {self.wave_name}")
            else:
                self.all_waves_completed = True
                print("[Wave] Đã hoàn thành tất cả các đợt!")

        # 7. Cập nhật vàng rơi (xóa vàng đã nhặt, cập nhật vị trí)
        self.gold_drops = [g for g in self.gold_drops if not g.collected]
        for gold in self.gold_drops:
            gold.update(self.player)

    # ------------------------------------------------------------------
    # QUẢN LÝ WAVE & SPAWN
    # ------------------------------------------------------------------

    # Bắt đầu wave mới
    def _start_wave(self, wave_index):
        wave_name = WAVE_ORDER[wave_index]
        print(f"[Wave {wave_index + 1}] Bắt đầu đợt: {wave_name} x{ENEMIES_PER_WAVE} (mỗi lần {ENEMIES_PER_BATCH} con)")
        
        self.wave_name_current = wave_name
        self.remaining_to_spawn = ENEMIES_PER_WAVE
        self.spawn_timer = 0.0
        
        # Spawn batch đầu tiên ngay lập tức
        batch_count = min(ENEMIES_PER_BATCH, self.remaining_to_spawn)
        for _ in range(batch_count):
            self._spawn_one_enemy()
            self.remaining_to_spawn -= 1
        print(f"[Wave {self.wave_number}] Spawn {batch_count} con {self.wave_name_current}, còn {self.remaining_to_spawn} con")

    # Spawn 1 quái ở rìa ngoài camera (trên/dưới/trái/phải ngẫu nhiên)
    def _spawn_one_enemy(self):
        cls = ENEMY_CLASSES[self.wave_name_current]
        
        # Vị trí camera dựa trên player
        cam_x = self.player.x - SCREEN_WIDTH // 2
        cam_y = self.player.y - SCREEN_HEIGHT // 2
        
        # Chọn cạnh spawn ngẫu nhiên
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            x = random.uniform(cam_x - SPAWN_OFFSET, cam_x + SCREEN_WIDTH + SPAWN_OFFSET)
            y = cam_y - SPAWN_OFFSET
        elif side == "bottom":
            x = random.uniform(cam_x - SPAWN_OFFSET, cam_x + SCREEN_WIDTH + SPAWN_OFFSET)
            y = cam_y + SCREEN_HEIGHT + SPAWN_OFFSET
        elif side == "left":
            x = cam_x - SPAWN_OFFSET
            y = random.uniform(cam_y - SPAWN_OFFSET, cam_y + SCREEN_HEIGHT + SPAWN_OFFSET)
        else:  # right
            x = cam_x + SCREEN_WIDTH + SPAWN_OFFSET
            y = random.uniform(cam_y - SPAWN_OFFSET, cam_y + SCREEN_HEIGHT + SPAWN_OFFSET)

        # Giới hạn trong map
        MARGIN = 200
        x = max(MARGIN, min(x, MAP_WIDTH - MARGIN))
        y = max(MARGIN, min(y, MAP_HEIGHT - MARGIN))

        # Tạo quái + gán player + thêm vào danh sách
        e = cls(x, y, scale_factor=DEFAULT_SCALE)
        e.set_player(self.player)
        self.enemies.append(e)
        self._sync_enemies()

    # Đồng bộ danh sách enemy cho player
    def _sync_enemies(self):
        self.player.set_enemies(self.enemies)

    # ------------------------------------------------------------------
    # XỬ LÝ TẤN CÔNG & VÀNG RƠI
    # ------------------------------------------------------------------

    # Kiểm tra đòn tấn công của player có trúng quái không
    def _check_player_attack_collision(self):
        attack_hitbox = self.player.get_attack_hitbox()
        if not attack_hitbox:
            return
        
        for enemy in self.enemies:
            if enemy.is_dead:
                continue
            
            try:
                # Kiểm tra hitbox tròn vs rect
                cx, cy, radius = enemy.get_hitbox()
                
                closest_x = max(attack_hitbox.left, min(cx, attack_hitbox.right))
                closest_y = max(attack_hitbox.top, min(cy, attack_hitbox.bottom))
                
                dx = closest_x - cx
                dy = closest_y - cy
                
                if dx * dx + dy * dy < radius * radius:
                    enemy.take_damage(self.player.damage)
                    
            except AttributeError:
                # Fallback: rect vs rect
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                if attack_hitbox.colliderect(enemy_rect):
                    enemy.take_damage(self.player.damage)

    # Xóa quái đã chết và tạo vàng rơi
    def _remove_dead(self):
        alive = []
        changed = False
        
        for e in self.enemies:
            if e.fully_dead:
                gold_value = self._get_gold_value(e)
                cx = e.x + e.width // 2
                cy = e.y + e.height // 2
                self.gold_drops.append(GoldDrop(cx, cy, value=gold_value))
                changed = True
            else:
                alive.append(e)
        
        if changed:
            self.enemies = alive
            self._sync_enemies()

    # Lấy giá trị vàng dựa trên class của quái
    def _get_gold_value(self, enemy):
        class_to_name = {v: k for k, v in ENEMY_CLASSES.items()}
        name = class_to_name.get(type(enemy), "slime1")
        return GOLD_VALUES.get(name, 5)

    # ------------------------------------------------------------------
    # THUỘC TÍNH TIỆN ÍCH
    # ------------------------------------------------------------------

    @property
    def wave_number(self):
        """Số đợt hiện tại (bắt đầu từ 1)"""
        return self.current_wave + 1

    @property
    def wave_name(self):
        """Tên loại quái đang spawn"""
        return WAVE_ORDER[self.current_wave]

    # ------------------------------------------------------------------
    # VẼ
    # ------------------------------------------------------------------

    def draw(self, surface, camera):
        # Vẽ từng quái
        for e in self.enemies:
            e.draw(surface, camera)
        # Vẽ từng vàng rơi
        for gold in self.gold_drops:
            gold.draw(surface, camera)