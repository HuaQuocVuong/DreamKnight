import sound_manager  # Phải import trước để monkey-patch pygame.mixer.Sound có hiệu lực
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT, MAP_IMAGE_PATH
from knight1 import Player1
from camera import Camera

from game_object import GameObject
from npc_system import NPCSystem
from enemy_manager import EnemyManager  

from ui import UI, PauseMenu

# ================================================================================================
# CLASS GAME — Điều khiển toàn bộ vòng đời game
# Quản lý: cửa sổ, vòng lặp, sự kiện, logic, render, nhạc nền
# Kết nối: player, camera, map, game objects, enemies, NPC, UI
# ================================================================================================

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Cửa sổ game
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("DREAM KNIGHT")
        self.clock = pygame.time.Clock()

        # Load map
        self.map_image = pygame.image.load(MAP_IMAGE_PATH).convert()

        # Player + Camera
        self.player = Player1(400, 450)
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.game_surface = pygame.Surface((self.camera.view_width, self.camera.view_height))

        # Quản lý quái & vàng tập trung
        self.enemies = EnemyManager(self.player)

        # Nhạc nền
        self.setup_music()

        # Trạng thái game
        self.running   = True
        self.game_over = False
        self.victory   = False  # Chiến thắng khi hết tất cả wave

        # UI + Pause
        self.ui         = UI()
        self.pause_menu = PauseMenu()

        # --- Game Objects (cảnh vật) ---
        
        # Nhà 1
        self.home001_object = GameObject(
            x=900, y=10,
            image_path="assets/home/home_001.png",
            animation_folder=None, frame_duration=None, scale=2.0,
        )

        # Nhà 2 + ống khói
        self.home002_object = GameObject(
            x=1500, y=10,
            image_path="assets/home2/home2.png",
            animation_folder=None, frame_duration=None, scale=2.0,
        )
        self.chimney_home2_object = GameObject(
            x=1500, y=10,
            image_path=None,
            animation_folder="assets/chimney", frame_duration=0.15, scale=2.0,
        )
        
        # NPC Luneblade
        self.lunebladeNPC_object = GameObject(
            x=1100, y=700,
            image_path=None,
            animation_folder="assets/luneblade", frame_duration=0.1, scale=2.0,
        )
        
        # Nhà 3 + cờ
        self.home003_object = GameObject(
            x=950, y=410,
            image_path="assets/home3/home3.png",
            animation_folder=None, frame_duration=None, scale=2.0,
        )
        self.flag1_object = GameObject(
            x=950, y=410,
            image_path=None,
            animation_folder="assets/flag1", frame_duration=0.6, scale=2.0,
        )
        
        # Nhà chính + rồng
        self.home_base01_object = GameObject(
            x=200, y=101,
            image_path="assets/home_base/home_base01.png",
            animation_folder=None, frame_duration=2.0, scale=2.0,
        )
        self.dragonHome001_object = GameObject(
            x=200, y=100,
            image_path=None,
            animation_folder="assets/dragon_home", frame_duration=0.15, scale=2.0,
        )
        
        # Cây
        self.tree_01_object = GameObject(
            x=830, y=120,
            image_path=None,
            animation_folder="assets/tree_01", frame_duration=2.0, scale=2.0,
        )
        
        # Giỏ trái cây (3 cái)
        self.fruit_pasket_01 = GameObject(
            x=1225, y=190,
            image_path="assets/fruit_basket/fruit_basket_01.png",
            animation_folder=None, frame_duration=2.0, scale=2.0,
        )
        self.fruit_pasket_02 = GameObject(
            x=1330, y=190,
            image_path="assets/fruit_basket/fruit_basket_02.png",
            animation_folder=None, frame_duration=2.0, scale=2.0,
        )
        self.fruit_pasket_03 = GameObject(
            x=1430, y=200,
            image_path="assets/fruit_basket/fruit_basket_03.png",
            animation_folder=None, frame_duration=2.0, scale=2.0,
        )

        # NPC Sample
        self.sampleNPC_object = GameObject(
            x=1290, y=235,
            image_path=None,
            animation_folder="assets/sample01", frame_duration=1, scale=2.0,
        )

        # Hàng rào (18 cột dọc bên trái + 18 cột dọc bên phải)
        fence_positions = [
            (152, 101), (152, 133), (152, 165), (152, 197), (152, 229), (152, 261),
            (152, 293), (152, 325), (152, 357), (152, 389), (152, 421), (152, 453),
            (152, 485), (152, 517), (152, 549), (152, 581), (152, 613), (152, 645),
            (801, 101), (801, 133), (801, 165), (801, 197), (801, 229), (801, 261),
            (801, 293), (801, 325), (801, 357), (801, 389), (801, 421), (801, 453),
            (801, 485), (801, 517), (801, 549), (801, 581), (801, 613), (801, 645),
        ]
        self.fences = [
            GameObject(x=x, y=y, image_path="assets/fence/fence2.png",
                       animation_folder=None, frame_duration=2.0, scale=2.0)
            for x, y in fence_positions
        ]

        # Hệ thống NPC (hội thoại + shop)
        self.npc_manager = NPCSystem()
        
        # Áp dụng volume SFX hiện tại
        sound_manager.set_sfx_volume(sound_manager.get_sfx_volume())

    # ------------------------------------------------------------------
    # ÂM NHẠC — Phát nhạc nền loop
    # ------------------------------------------------------------------

    def setup_music(self):
        try:
            pygame.mixer.music.load("03_sounds/map/H101-62 ASPID REVISED.mp3")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # Loop vô hạn
            print("Đang phát nhạc nền...")
        except FileNotFoundError:
            print("Không tìm thấy file nhạc nền! Bỏ qua phát nhạc.")
        except pygame.error as e:
            print(f"Lỗi khi phát nhạc: {e}")

    # ------------------------------------------------------------------
    # SỰ KIỆN — Xử lý tất cả input (bàn phím, chuột)
    # ------------------------------------------------------------------

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            # Thoát game
            if event.type == pygame.QUIT:
                self.running = False

            # Thả chuột → kết thúc kéo slider
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.pause_menu.handle_mouseup()

            # Kéo chuột → điều chỉnh slider volume
            elif event.type == pygame.MOUSEMOTION:
                result = self.pause_menu.handle_mousemotion(event.pos, SCREEN_WIDTH, SCREEN_HEIGHT)
                if result:
                    kind, value = result
                    if kind == "music":
                        sound_manager.set_music_volume(value)
                    elif kind == "sfx":
                        sound_manager.set_sfx_volume(value)

            # Click chuột trái
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Đang mở shop → ưu tiên xử lý mua hàng
                if self.npc_manager.is_showing_shop:
                    self.npc_manager.handle_click(event.pos, self.player)
                
                # Xử lý click trong pause menu
                self.pause_menu.handle_mousedown(event.pos, SCREEN_WIDTH, SCREEN_HEIGHT)
                action = self.pause_menu.handle_click(event.pos, SCREEN_WIDTH, SCREEN_HEIGHT)
                if action == "quit":
                    self.running = False
                elif action == "resume":
                    pygame.mixer.music.unpause()

                # Click nút Play Again khi Game Over
                if self.game_over:
                    box_w, box_h = 360, 260
                    box_x = (SCREEN_WIDTH  - box_w) // 2
                    box_y = (SCREEN_HEIGHT - box_h) // 2
                    btn_w, btn_h = 220, 44
                    btn_x = box_x + (box_w - btn_w) // 2
                    if pygame.Rect(btn_x, box_y + 140, btn_w, btn_h).collidepoint(event.pos):
                        self._reset_game()
                        self.game_over = False
                        pygame.mixer.music.unpause()

                # Click nút Play Again khi Victory
                if self.victory:
                    box_w, box_h = 420, 300
                    box_x = (SCREEN_WIDTH  - box_w) // 2
                    box_y = (SCREEN_HEIGHT - box_h) // 2
                    btn_w, btn_h = 230, 48
                    btn_x = box_x + (box_w - btn_w) // 2
                    if pygame.Rect(btn_x, box_y + 160, btn_w, btn_h).collidepoint(event.pos):
                        self._reset_game()
                        self.victory = False
                        pygame.mixer.music.unpause()

            # Phím
            elif event.type == pygame.KEYDOWN:
                self.npc_manager.handle_keydown(event.key)

                # ESC khi Game Over hoặc Victory → thoát game
                if self.game_over or self.victory:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    continue

                # ESC → bật/tắt pause menu
                if event.key == pygame.K_ESCAPE:
                    self.pause_menu.toggle()
                    if self.pause_menu.visible:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()

        # Nếu đang pause, game over hoặc victory → không trả về events cho player
        if self.pause_menu.visible or self.game_over or self.victory:
            return []
        return events

    # ------------------------------------------------------------------
    # UPDATE — Cập nhật logic mỗi frame
    # ------------------------------------------------------------------

    def update(self):
        # 1. Lấy sự kiện từ bàn phím/chuột
        events = self.handle_events()

        dt = self.clock.get_time()
        
        # Game over, victory hoặc pause → dừng toàn bộ logic
        if self.game_over or self.victory or self.pause_menu.visible:
            return

        # 2. Cập nhật hệ thống NPC (khoảng cách, hội thoại)
        self.npc_manager.update(self.player, self, dt)

        # 3. Chỉ cập nhật player & quái khi KHÔNG xem hội thoại và KHÔNG mở shop
        if not self.npc_manager.is_showing_dialogue and not self.npc_manager.is_showing_shop:
            self.player.update(MAP_WIDTH, MAP_HEIGHT, events)
            self.enemies.update(1/60, MAP_WIDTH, MAP_HEIGHT)

        # 4. Kiểm tra player chết → Game Over
        if self.player.is_dead and not self.game_over:
            self.game_over = True
            pygame.mixer.music.pause()
            pygame.mixer.stop()

        # 5. Kiểm tra hoàn thành tất cả wave → Victory
        if self.enemies.all_waves_completed and not self.victory:
            self.victory = True
            pygame.mixer.music.pause()
            pygame.mixer.stop()

        # 6. Camera bám theo player
        self.camera.update(self.player)

        # 7. Cập nhật animation cho tất cả vật thể cảnh
        for obj in self._scene_objects():
            obj.update(1/60)
        for fence in self.fences:
            fence.update(1/60)

    # ------------------------------------------------------------------
    # VẼ — Render toàn bộ game
    # ------------------------------------------------------------------

    def draw(self):
        # Xóa surface game
        self.game_surface.fill((0, 0, 0))
        
        # Vẽ map (có camera offset)
        self.game_surface.blit(self.map_image, (-self.camera.x, -self.camera.y))

        # Vẽ cảnh vật
        for obj in self._scene_objects():
            obj.draw(self.game_surface, self.camera)

        # Vẽ quái + vàng rơi
        self.enemies.draw(self.game_surface, self.camera)

        # Vẽ player
        self.player.draw(self.game_surface, self.camera)

        # Scale game surface lên kích thước màn hình
        scaled_surface = pygame.transform.scale(self.game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(scaled_surface, (0, 0))

        # Vẽ UI (máu, dash, vàng, stats, game over/victory)
        self.ui.draw(self.screen, self.player, SCREEN_WIDTH, SCREEN_HEIGHT, self.victory)
        
        # Vẽ pause menu (nếu đang mở)
        self.pause_menu.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                             sound_manager.get_music_volume(), sound_manager.get_sfx_volume())
        
        # Vẽ NPC dialogue/shop
        self.npc_manager.draw(self.screen, self.camera, self)
        
        pygame.display.flip()

    # ------------------------------------------------------------------
    # TIỆN ÍCH
    # ------------------------------------------------------------------

    # Trả về tất cả game object tĩnh theo đúng thứ tự vẽ
    def _scene_objects(self):
        return [
            self.home001_object, self.home002_object, self.chimney_home2_object,
            self.home003_object, self.flag1_object,
            self.fruit_pasket_01, self.fruit_pasket_02, self.fruit_pasket_03,
            self.lunebladeNPC_object, self.sampleNPC_object,
            self.tree_01_object,
            self.home_base01_object, self.dragonHome001_object,
            *self.fences,
        ]

    # Reset toàn bộ game về trạng thái ban đầu (khi Play Again)
    def _reset_game(self):
        # Reset player
        self.player.health          = self.player.max_health
        self.player.is_dead         = False
        self.player.ghost_mode      = False
        self.player.ghost_used      = False
        self.player.ghost_start_time = 0
        self.player.x               = 400
        self.player.y               = 450
        self.player.rect.center     = (400, 450)
        self.player.direction       = "down"
        self.player.image           = self.player.idle_animations["down"].current_frame
        
        # Reset vàng và cấp kỹ năng
        self.player.gold                 = 0
        self.player.attack_damage_level  = 0
        self.player.attack_speed_level   = 0
        self.player.dash_upgrade_level   = 0
        self.player.range_upgrade_level  = 0
        self.player.damage               = 50    # Sát thương gốc
        self.player.dash_cooldown        = 500   # Cooldown dash gốc
        
        # Reset wave và quái
        self.enemies = EnemyManager(self.player)

    # ------------------------------------------------------------------
    # VÒNG LẶP CHÍNH
    # ------------------------------------------------------------------

    def run(self):
        while self.running:
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS
        
        pygame.mixer.music.stop()
        pygame.quit()