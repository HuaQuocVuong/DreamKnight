import pygame
import math
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT
import sound_manager

# Khởi tạo pygame.mixer để phát nhạc và voice
pygame.mixer.init()

# ================================================================================================
# CLASS NPCSYSTEM — Hệ thống NPC, hội thoại và cửa hàng
# ================================================================================================
class NPCSystem:
    
    def __init__(self):
        # Trạng thái giao diện
        self.is_showing_dialogue = False  # Đang hiển thị hộp thoại
        self.is_showing_shop = False      # Đang hiển thị cửa hàng
        self.shop_type = None             # Loại cửa hàng: "vat pham" hoặc "ky nang"
        
        self.active_npc_id = None  # ID NPC đang tương tác
        self.current_step = 0      # Bước hội thoại hiện tại
        self.selected_option = 0   # Lựa chọn được chọn (dự phòng)
        
        # Hệ thống thông báo trong shop
        self.shop_message = ""         # Nội dung thông báo
        self.shop_message_timer = 0    # Thời gian hiển thị thông báo (frame)
        self.button_rects = []         # Danh sách rect các nút trong shop

        # Cache icon đã load để tránh load lại mỗi frame
        self.shop_icons = {}
        
        # Hệ thống audio cho dialogue
        self.current_voice = None     # Sound đang phát
        self.voice_timer = 0          # Thời gian còn lại của voice (ms)
        self.is_playing_voice = False # Cờ đang phát voice

        # Kịch bản hội thoại NPC (có kèm đường dẫn file voice)
        self.npc_data = {
            1: {
                "name": "Iselda",
                "dialogues": {
                    0: "Chao Knight, nguoi trong co ve can su giup do...",
                    1: "Ta co nhung mon do co the giup do nguoi.",
                    2: "Hay dua cho ta tien tu nhung con quai bi ha va lay thu nguoi can!" 
                },
                # File voice cho từng câu thoại
                "voices": {
                    0: "03_sounds/sample_sound/IseldaShopOpen.mp3",
                    1: "03_sounds/sample_sound/IseldaShopTalk01.mp3",
                    2: "03_sounds/sample_sound/IseldaShopTalk02.mp3",
                }
            },
            2: {
                "name": "The Hunter",
                "dialogues": {
                    0: "Tiny squib... You approach fearless. Are you a hunter like me?.",
                    1: "Do you feel the urge inside, to stalk, to kill, to understand?",
                    2: "Then take it! My journal. It will aid you. At first the text may seem difficult to discern, but a learned hunter will come to understand its words.",
                    3: "Venture the depths of this land and slay its beasts. Prove yourself worthy to bear the mark of Hunter.",
                },
                # File voice cho từng câu thoại
                "voices": {
                    0: "03_sounds/TheHunter/HunterTalk01.mp3",
                    1: "03_sounds/TheHunter/HunterTalk02.mp3",
                    2: "03_sounds/TheHunter/HunterTalk03.mp3",
                    3: "03_sounds/TheHunter/HunterTalk04.mp3",
                }
            }
        }

        # KHO HÀNG HÓA — mỗi NPC bán 1 loại shop riêng
        self.shop_goods = {
            # Iselda (NPC 1) — bán vật phẩm hồi máu
            "vat pham": [
                {"name": "Minor Health Potion", "desc": "+20 HP", "price": 15, "type": "heal", "value": 20, "quantity": 1, "icon": "fc266.png"},
                {"name": "Health Potion", "desc": "+40 HP", "price": 30, "type": "heal", "value": 40, "quantity": 1, "icon": "fc268.png"},
                {"name": "Greater Health Potion", "desc": "+MAX HP", "price": 60, "type": "heal", "value": 100, "quantity": 1, "icon": "fc272.png"}
            ],
            # The Hunter (NPC 2) — bán kỹ năng
            "ky nang": [
                {"name": "Upgrade sword", "desc": "Tang Sat Thuong Kiem (+15)", "price": 100, "type": "damage", "value": 15, "quantity": 1, "icon": "fc730.png"},
                {"name": "Dashmaster", "desc": "Giam Cooldown Dash (-0.2s)", "price": 150, "type": "dash_cd", "value": 0.2, "quantity": 1, "icon": "fc790.png"},
            ]
        }

    # ------------------------------------------------------------------
    # HỆ THỐNG AUDIO CHO DIALOGUE
    # ------------------------------------------------------------------
    
    # Phát file voice cho câu thoại hiện tại
    def play_dialogue_voice(self, npc_id, step):
        # Dừng voice đang phát nếu có
        if self.current_voice:
            self.current_voice.stop()
            
        # Kiểm tra NPC có voice cho step này không
        if npc_id in self.npc_data:
            voices = self.npc_data[npc_id].get("voices", {})
            voice_file = voices.get(step)
            
            if voice_file and os.path.exists(voice_file):
                try:
                    self.current_voice = pygame.mixer.Sound(voice_file)
                    # Đăng ký với sound_manager để control volume
                    sound_manager.register_npc_voice(self.current_voice)
                    self.current_voice.play()
                    self.is_playing_voice = True
                    # Tính thời gian phát (ms)
                    self.voice_timer = int(self.current_voice.get_length() * 1000)
                    print(f"✅ Đang phát: {voice_file}")
                    print(f"📊 Volume hiện tại: {sound_manager.get_sfx_volume()}")
                except Exception as e:
                    print(f"❌ Lỗi: {e}")
                    self.is_playing_voice = False
            else:
                if voice_file:
                    print(f"❌ Không tìm thấy file: {voice_file}")
                self.is_playing_voice = False
        
    # Dừng voice đang phát
    def stop_current_voice(self):
        if self.current_voice:
            self.current_voice.stop()
            self.current_voice = None
        self.is_playing_voice = False
        self.voice_timer = 0
    
    # Cập nhật timer cho voice (gọi trong game loop)
    def update_voice(self, dt):
        if self.is_playing_voice:
            self.voice_timer -= dt
            if self.voice_timer <= 0:
                self.is_playing_voice = False
                self.voice_timer = 0

    # ------------------------------------------------------------------
    # LOAD ICON — cache để tránh load lại mỗi frame
    # ------------------------------------------------------------------
    
    # Load icon từ thư mục assets/icon_item, cache lại
    def load_shop_icon(self, icon_path, size=(64, 64)):
        if icon_path in self.shop_icons:
            return self.shop_icons[icon_path]
        
        full_path = f"assets/icon_item/{icon_path}"
        if os.path.exists(full_path):
            try:
                icon = pygame.image.load(full_path).convert_alpha()
                self.shop_icons[icon_path] = pygame.transform.scale(icon, size)
                return self.shop_icons[icon_path]
            except:
                return None
        return None

    # ------------------------------------------------------------------
    # CẬP NHẬT — Kiểm tra player có đến gần NPC không
    # ------------------------------------------------------------------
    
    def update(self, player, game_instance, dt=0):
        # Cập nhật voice timer
        self.update_voice(dt)
        
        # Giảm timer thông báo shop
        if self.is_showing_dialogue or self.is_showing_shop:
            if self.shop_message_timer > 0:
                self.shop_message_timer -= 1
            return

        # Map NPC ID → object trong game
        npc_objects = {
            1: game_instance.sampleNPC_object,
            2: game_instance.lunebladeNPC_object
        }

        player_cx = player.x + player.width // 2
        player_cy = player.y + player.height // 2

        # Kiểm tra khoảng cách đến từng NPC
        for npc_id, npc_obj in npc_objects.items():
            if npc_obj:
                img_w = npc_obj.current_image.get_width() if npc_obj.current_image else 32
                img_h = npc_obj.current_image.get_height() if npc_obj.current_image else 48
                
                npc_cx = npc_obj.x + img_w // 2
                npc_cy = npc_obj.y + img_h // 2
                
                distance = math.hypot(npc_cx - player_cx, npc_cy - player_cy)
                
                # Trong phạm vi 80px → kích hoạt NPC
                if distance <= 80: 
                    self.active_npc_id = npc_id
                    return
                
        self.active_npc_id = None

    # ------------------------------------------------------------------
    # XỬ LÝ CLICK CHUỘT — Mua hàng trong shop
    # ------------------------------------------------------------------
    
    def handle_click(self, mouse_pos, player):
        if not self.is_showing_shop:
            return

        # Duyệt qua tất cả nút đã đăng ký
        for btn in self.button_rects:
            if btn["rect"].collidepoint(mouse_pos):
                
                # Nút chuyển tab (hiện không dùng)
                if btn["action"] == "change_tab":
                    self.shop_type = btn["tab_target"]
                    self.shop_message = ""
                    return

                goods_list = self.shop_goods[self.shop_type]
                idx = btn["item_index"]
                
                # Nút đóng shop
                if btn["action"] == "close":
                    self.is_showing_shop = False
                    self.shop_type = None
                    return
                    
                # Nút mua hàng
                elif btn["action"] == "buy":
                    item = goods_list[idx]
                    total_cost = item["price"] * item["quantity"]
                    
                    # Kiểm tra đủ vàng không
                    if player.gold >= total_cost:
                        player.gold -= total_cost
                        
                        # Áp dụng hiệu ứng vật phẩm
                        for _ in range(item["quantity"]):
                            if item["type"] == "heal":
                                # Hồi máu (không vượt max_health)
                                player.health = min(player.max_health, player.health + item["value"])
                            elif item["type"] == "damage":
                                # Tăng sát thương
                                if hasattr(player, 'damage'): 
                                    player.damage += item["value"]
                                elif hasattr(player, 'attack_damage'): 
                                    player.attack_damage += item["value"]
                            elif item["type"] == "dash_cd":
                                # Giảm cooldown dash (tối thiểu 100ms)
                                if hasattr(player, 'dash_cooldown'):
                                    player.dash_cooldown = max(100, player.dash_cooldown - (item["value"] * 1000))
                        
                        self.shop_message = f"Mua thanh cong {item['quantity']}x {item['name']}!"
                        item["quantity"] = 1  # Reset quantity
                        self.shop_message_timer = 90  # Hiển thị 90 frame
                    else:
                        self.shop_message = "Khong du tien Vang de mua!"
                        self.shop_message_timer = 90
                    return

    # ------------------------------------------------------------------
    # XỬ LÝ PHÍM — Mở hội thoại, chuyển câu, mở shop
    # ------------------------------------------------------------------
    
    def handle_keydown(self, key):
        # Trong shop: F để đóng
        if self.is_showing_shop:
            if key == pygame.K_f: 
                self.is_showing_shop = False
                self.shop_type = None
            return

        # Chưa trong dialogue: F để bắt đầu hội thoại
        if not self.is_showing_dialogue:
            if key == pygame.K_f and self.active_npc_id is not None:
                self.is_showing_dialogue = True
                self.current_step = 0
                self.selected_option = 0
                # Phát voice câu đầu tiên
                self.play_dialogue_voice(self.active_npc_id, 0)
            return

        # Đang trong dialogue: F để tiếp tục hoặc mở shop
        if self.is_showing_dialogue and self.active_npc_id:
            npc = self.npc_data[self.active_npc_id]
            total_dialogues = len(npc["dialogues"])

            # NPC 1 (Iselda) — câu cuối → mở shop vật phẩm
            if self.active_npc_id == 1 and self.current_step == total_dialogues - 1:
                if key == pygame.K_f:
                    self.is_showing_dialogue = False 
                    self.is_showing_shop = True     
                    self.shop_type = "vat pham"
                    self.stop_current_voice()
                return

            # NPC 2 (Hunter) — câu cuối → mở shop kỹ năng
            if self.active_npc_id == 2 and self.current_step == total_dialogues - 1:
                if key == pygame.K_f:
                    self.is_showing_dialogue = False 
                    self.is_showing_shop = True     
                    self.shop_type = "ky nang"
                    self.stop_current_voice()
                return

            # Chưa đến câu cuối: F để sang câu tiếp theo
            if key == pygame.K_f:
                self.current_step += 1
                if self.current_step >= total_dialogues:
                    # Hết hội thoại → đóng
                    self.is_showing_dialogue = False
                    self.active_npc_id = None
                    self.stop_current_voice()
                else:
                    # Phát voice cho câu tiếp theo
                    self.play_dialogue_voice(self.active_npc_id, self.current_step)

    # ------------------------------------------------------------------
    # VẼ GIAO DIỆN — Hộp thoại và cửa hàng
    # ------------------------------------------------------------------
    
    def draw(self, surface, camera, game_instance):
        font_small = pygame.font.SysFont("Arial", 18)
        font_bold = pygame.font.SysFont("Arial", 22, bold=True)
        player = game_instance.player

        # 1. VẼ HỘP THOẠI — hiển thị khi đang nói chuyện với NPC
        if self.is_showing_dialogue and self.active_npc_id:
            npc = self.npc_data[self.active_npc_id]
            
            # Nền hộp thoại
            box_rect = pygame.Rect(50, SCREEN_HEIGHT - 160, SCREEN_WIDTH - 100, 130)
            pygame.draw.rect(surface, (25, 25, 25), box_rect, border_radius=10)
            pygame.draw.rect(surface, (255, 215, 0), box_rect, 2, border_radius=10) 
            
            # Tên NPC
            name_surf = font_bold.render(npc["name"], True, (255, 165, 0))
            surface.blit(name_surf, (70, SCREEN_HEIGHT - 150))
            
            # Nội dung hội thoại
            msg = npc["dialogues"].get(self.current_step, "")
            msg_surf = font_small.render(msg, True, (255, 255, 255))
            surface.blit(msg_surf, (70, SCREEN_HEIGHT - 110))
            
            # Icon đang phát voice (nếu có)
            if self.is_playing_voice:
                voice_icon = font_small.render("🔊", True, (100, 255, 100))
                surface.blit(voice_icon, (SCREEN_WIDTH - 60, SCREEN_HEIGHT - 150))
            
            total_dialogues = len(npc["dialogues"])
            
            # NPC 1 (Iselda) — câu cuối: hiển thị nút mở shop vật phẩm
            if self.active_npc_id == 1 and self.current_step == total_dialogues - 1:
                rect_item = pygame.Rect(70, SCREEN_HEIGHT - 75, 200, 35)
                pygame.draw.rect(surface, (40, 40, 40), rect_item, border_radius=5)
                pygame.draw.rect(surface, (255, 215, 0), rect_item, 2, border_radius=5)
                txt_item = font_small.render("Mo Shop Vat Pham", True, (255, 255, 255))
                surface.blit(txt_item, (rect_item.x + 30, rect_item.y + 6))
                hint = font_small.render("[Nhan F de mo shop]", True, (0, 255, 255))
                surface.blit(hint, (SCREEN_WIDTH - 280, SCREEN_HEIGHT - 60))
                
            # NPC 2 (Hunter) — câu cuối: hiển thị nút mở shop kỹ năng
            elif self.active_npc_id == 2 and self.current_step == total_dialogues - 1:
                rect_skill = pygame.Rect(70, SCREEN_HEIGHT - 75, 200, 35)
                pygame.draw.rect(surface, (40, 40, 40), rect_skill, border_radius=5)
                pygame.draw.rect(surface, (255, 215, 0), rect_skill, 2, border_radius=5)
                txt_skill = font_small.render("Mo Shop Ky Nang", True, (255, 255, 255))
                surface.blit(txt_skill, (rect_skill.x + 30, rect_skill.y + 6))
                hint = font_small.render("[Nhan F de mo shop]", True, (0, 255, 255))
                surface.blit(hint, (SCREEN_WIDTH - 280, SCREEN_HEIGHT - 60))
            else:
                # Các câu khác: hint nhấn F để tiếp tục
                hint = font_small.render("[Nhan F de tiep tuc...]", True, (160, 160, 160))
                surface.blit(hint, (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60))

        # 2. VẼ CỬA HÀNG — hiển thị khi đang mở shop
        if self.is_showing_shop:
            self.button_rects = []  # Reset danh sách nút mỗi frame

            # Khung shop
            shop_rect = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 8, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.4)
            pygame.draw.rect(surface, (35, 30, 25), shop_rect, border_radius=12)
            pygame.draw.rect(surface, (255, 215, 0), shop_rect, 3, border_radius=12)
            
            # Tiêu đề shop
            title_text = f"CUA HANG {self.shop_type.upper()}"
            title_surf = font_bold.render(title_text, True, (255, 215, 0))
            surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, shop_rect.y + 15))
            
            # Tên NPC đang bán
            npc_name = "Iselda" if self.active_npc_id == 1 else "The Hunter"
            npc_label = font_small.render(f"Nguoi ban: {npc_name}", True, (200, 200, 200))
            surface.blit(npc_label, (shop_rect.x + 30, shop_rect.y + 50))
            
            # Hiển thị số vàng hiện có
            gold_surf = font_bold.render(f"Vang: {player.gold}", True, (255, 255, 0))
            surface.blit(gold_surf, (shop_rect.right - gold_surf.get_width() - 30, shop_rect.y + 50))
            
            # Danh sách vật phẩm
            goods = self.shop_goods[self.shop_type]
            start_y = shop_rect.y + 95
            
            for i, item in enumerate(goods):
                # Ô vật phẩm
                row_rect = pygame.Rect(shop_rect.x + 30, start_y + (i * 80), shop_rect.width - 60, 70)
                pygame.draw.rect(surface, (50, 40, 35), row_rect, border_radius=8)
                
                # Icon vật phẩm
                icon_file = item.get("icon", None)
                if icon_file:
                    item_surface = self.load_shop_icon(icon_file, (64, 64))
                    if item_surface:
                        surface.blit(item_surface, (row_rect.x + 5, row_rect.y + 3))
                        name_surf = font_bold.render(item["name"], True, (255, 255, 255))
                        desc_surf = font_small.render(item["desc"], True, (170, 170, 170))
                        surface.blit(name_surf, (row_rect.x + 75, row_rect.y + 12))
                        surface.blit(desc_surf, (row_rect.x + 75, row_rect.y + 38))
                    else:
                        name_surf = font_bold.render(item["name"], True, (255, 255, 255))
                        desc_surf = font_small.render(item["desc"], True, (170, 170, 170))
                        surface.blit(name_surf, (row_rect.x + 65, row_rect.y + 10))
                        surface.blit(desc_surf, (row_rect.x + 65, row_rect.y + 35))
                else:
                    name_surf = font_bold.render(item["name"], True, (255, 255, 255))
                    desc_surf = font_small.render(item["desc"], True, (170, 170, 170))
                    surface.blit(name_surf, (row_rect.x + 65, row_rect.y + 10))
                    surface.blit(desc_surf, (row_rect.x + 65, row_rect.y + 35))
                
                # Nút mua (vàng gold)
                total_item_price = item["price"] * item["quantity"]
                btn_buy = pygame.Rect(row_rect.right - 145, row_rect.y + 18, 130, 35)
                pygame.draw.rect(surface, (218, 165, 32), btn_buy, border_radius=6)
                buy_str = f"Mua: {total_item_price}G"
                buy_surf = font_small.render(buy_str, True, (25, 25, 25))
                surface.blit(buy_surf, (btn_buy.x + (btn_buy.width - buy_surf.get_width()) // 2, btn_buy.y + 7))
                # Đăng ký nút để xử lý click
                self.button_rects.append({"rect": btn_buy, "action": "buy", "item_index": i})

            # Thông báo khi mua hàng (xanh: thành công, đỏ: thất bại)
            if self.shop_message_timer > 0:
                text_color = (100, 255, 100) if "thanh cong" in self.shop_message else (255, 100, 100)
                msg_surf = font_bold.render(self.shop_message, True, text_color)
                surface.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, shop_rect.bottom - 75))

            # Hướng dẫn đóng shop
            hint_str = "Nhan phim [F] de Dong Cua Hang  |  click de tuong tac"
            close_surf = font_small.render(hint_str, True, (200, 200, 200))
            surface.blit(close_surf, (SCREEN_WIDTH // 2 - close_surf.get_width() // 2, shop_rect.bottom - 35))