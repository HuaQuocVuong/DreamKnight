import pygame

class UI:
    """Lớp quản lý giao diện người dùng (thanh máu, thanh cooldown dash, animation, game over)"""

    def __init__(self):
        """Khởi tạo các thành phần UI và load tài nguyên"""
        pygame.font.init()
        self.font       = pygame.font.SysFont("Arial", 16, bold=True)  # Font nhỏ cho text UI
        self.font_big   = pygame.font.SysFont("Arial", 60, bold=True)  # Font lớn cho GAME OVER
        self.font_btn   = pygame.font.SysFont("Arial", 26, bold=True)  # Font cho nút bấm
        self.tick       = 0  # Biến đếm frame, dùng để tạo hiệu ứng nhấp nháy cho thanh máu khi thấp
        
        # Load ảnh dash
        self.dash_frames = []  # Mảng chứa 5 khung hình animation của dash
        self.load_dash_frames()
        
        # Load ảnh HP animation (thay thế hoàn toàn thanh máu vẽ bằng code)
        self.hp_frames = []  # Mảng chứa 5 khung hình animation của HP (0% → 100%)
        self.load_hp_frames()
        
        # ===== BIẾN ANIMATION DASH =====
        self.dash_animation_progress = 0.0   # Tiến độ animation (0.0 → 1.0)
        self.is_dashing_anim = False        # Cờ báo hiệu đang chạy animation dash
        self.dash_animation_speed = 0.04    # Tốc độ chạy animation (mỗi frame tăng 0.04)
        self.has_played_dash_anim = False   # THÊM: đánh dấu đã chạy animation cho lần dash này
        
        # Load animation gold
        self.gold_frames = []
        self.gold_frame_index = 0
        self.gold_frame_timer = 0
        self.gold_frame_duration = 100
        for i in range(1, 6):
            img = pygame.image.load(f"assets/gold/gold01/gold{i}.png").convert_alpha()
            img = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
            self.gold_frames.append(img)


    def load_hp_frames(self):
        """Load 5 ảnh HP từ thư mục assets/HP_UI/ (0% → 100% máu) và scale gấp đôi"""
        for i in range(5):  # hp_UI0.png (0% máu) → hp_UI4.png (100% máu)
            try:
                frame = pygame.image.load(f"assets/HP_UI/hp_UI{i}.png").convert_alpha()
                w, h = frame.get_width(), frame.get_height()
                frame = pygame.transform.scale(frame, (w * 3, h * 3))
                self.hp_frames.append(frame)
            except Exception as e:
                print(f"LỖI: Không load được HP_UI{i}.png - {e}")
                # Tạo frame giả nếu lỗi
                dummy = pygame.Surface((100, 30), pygame.SRCALPHA)
                dummy.fill((100, 0, 0))
                self.hp_frames.append(dummy)


    def load_dash_frames(self):
        """Load 5 ảnh dash từ thư mục assets/dash_UI/ và scale gấp đôi kích thước"""
        for i in range(5):  # Duyệt từ 0 đến 4 tương ứng dashUI00.png → dashUI04.png
            try:
                frame = pygame.image.load(f"assets/dash_UI/dashUI0{i}.png").convert_alpha()
                w, h = frame.get_width(), frame.get_height()
                frame = pygame.transform.scale(frame, (w * 3, h * 3))  # Scale gấp đôi để rõ nét hơn
                self.dash_frames.append(frame)
            except Exception as e:
                print(f"LỖI: Không load được dashUI0{i}.png - {e}")
                pygame.quit()
                exit()


    def draw_health_bar(self, surface, player):
        """Vẽ thanh máu HOÀN TOÀN bằng SPRITE (không còn vẽ bằng code nữa)"""
        self.tick += 1
        
        health_percent = max(0, player.health / player.max_health)  # Tính % máu (0.0 → 1.0)
        
        # Chọn frame dựa trên % máu (0% → frame 0, 100% → frame 4)
        # 5 frame tương ứng: 0%, 25%, 50%, 75%, 100%
        frame_index = int(health_percent * 4)  # 0.0 → 0, 1.0 → 4
        frame_index = max(0, min(frame_index, len(self.hp_frames) - 1))
        
        # Vị trí thanh máu
        PAD    = 20
        BAR_X  = PAD
        BAR_Y  = PAD
        
        # Vẽ sprite thanh máu
        hp_frame = self.hp_frames[frame_index]
        surface.blit(hp_frame, (BAR_X, BAR_Y))


    def start_dash_animation(self):
        """Bắt đầu animation dash (chỉ gọi 1 lần mỗi lần dash)"""
        self.is_dashing_anim = True
        self.dash_animation_progress = 0.0
        self.has_played_dash_anim = True


    def reset_dash_animation_flag(self):
        """Reset flag khi dash kết thúc, cho phép lần dash sau có thể chạy animation lại"""
        self.has_played_dash_anim = False


    def update_dash_animation(self):
        """Cập nhật animation dash ở mỗi frame (tăng progress, kết thúc khi đạt 1.0)"""
        if self.is_dashing_anim:
            self.dash_animation_progress += self.dash_animation_speed
            if self.dash_animation_progress >= 1.0:
                self.is_dashing_anim = False
                self.dash_animation_progress = 0.0
                self.reset_dash_animation_flag()


    def draw_dash_cooldown(self, surface, player):
        """Vẽ thanh dash - chỉ chạy animation 1 lần mỗi lần dash"""
        
        # ===== CHỈ GỌI ANIMATION NẾU CHƯA CHẠY CHO LẦN DASH NÀY =====
        # Nếu player đang dash và animation chưa được chạy thì bắt đầu
        if player.is_dashing and not self.has_played_dash_anim:
            self.start_dash_animation()
        
        # Cập nhật animation (tăng progress, kết thúc khi cần)
        self.update_dash_animation()
        
        # Tính thời gian cooldown còn lại của dash
        remaining = player.get_dash_cooldown_remaining()
        ready_pct = 1.0 - (remaining / player.dash_cooldown)  # 0 = đang cooldown, 1 = sẵn sàng
        ready_pct = max(0.0, min(1.0, ready_pct))

        # Vị trí thanh dash (ngay dưới thanh máu)
        PAD   = 20
        BAR_X = PAD
        BAR_Y = PAD + 28

        # ===== CHỌN FRAME HIỂN THỊ =====
        if self.is_dashing_anim:
            # ĐANG CHẠY ANIMATION: chọn frame dựa trên progress (0 → 4)
            frame_index = int(self.dash_animation_progress * 5)
            frame_index = min(4, frame_index)
        else:
            # BÌNH THƯỜNG: hiển thị theo cooldown (frame càng cao khi sẵn sàng)
            frame_index = int(ready_pct * 5)
            frame_index = min(4, frame_index)
        
        # Giới hạn frame_index trong khoảng hợp lệ
        frame_index = max(0, min(frame_index, len(self.dash_frames) - 1))
        
        # Vẽ frame dash
        current_frame = self.dash_frames[frame_index]
        frame_width = current_frame.get_width()
        frame_height = current_frame.get_height()
        
        surface.blit(current_frame, (BAR_X, BAR_Y))
        
        # Vẽ chữ "DASH" bên cạnh
        if self.is_dashing_anim:
            label_color = (255, 200, 50)  # Màu vàng sáng khi đang dash
        else:
            # Màu xanh sáng nếu sẵn sàng, xanh nhạt nếu đang cooldown
            label_color = (80, 220, 255) if ready_pct >= 1.0 else (150, 180, 210)
        
        label = self.font.render("DASH", True, label_color)
        surface.blit(label, (BAR_X + frame_width + 8, BAR_Y + (frame_height // 2) - 8))


    def draw_gold(self, surface, player):
        """Vẽ icon đồng vàng + số vàng hiện có bên dưới thanh dash"""
        PAD   = 14
        BAR_Y = PAD + 28
        DASH_H = 30
        GOLD_Y = PAD + DASH_H + 30
        
        # Cập nhật animation
        current_time = pygame.time.get_ticks()
        if current_time - self.gold_frame_timer >= self.gold_frame_duration:
            self.gold_frame_timer = current_time
            self.gold_frame_index = (self.gold_frame_index + 1) % len(self.gold_frames)
        
        # Vẽ icon vàng animation
        gold_icon = self.gold_frames[self.gold_frame_index]
        surface.blit(gold_icon, (PAD, GOLD_Y))
        
        # Vẽ số vàng
        gold = getattr(player, 'gold', 0)
        gold_text = self.font.render(f"{gold}", True, (255, 230, 80))
        
        text_x = PAD + gold_icon.get_width() + 1
        text_y = GOLD_Y + 22
        surface.blit(gold_text, (text_x, text_y))


    def draw_stats(self, surface, player, screen_width):
        """Vẽ bảng thông số (damage, dash cooldown) góc trên phải màn hình"""
        PAD = 14
        box_w = 170
        box_h = 70
        box_x = screen_width - box_w - PAD
        box_y = PAD

        # Nền mờ
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        pygame.draw.rect(bg, (0, 0, 0, 120), (0, 0, box_w, box_h), border_radius=10)
        surface.blit(bg, (box_x, box_y))
        pygame.draw.rect(surface, (255, 210, 100), (box_x, box_y, box_w, box_h), 1, border_radius=10)

        # Lấy thông số từ player
        damage       = getattr(player, 'damage', 0)
        dash_cd_ms   = getattr(player, 'dash_cooldown', 0)
        dash_cd_sec  = dash_cd_ms / 1000

        # Vẽ dòng DMG
        dmg_text = self.font.render(f"DMG: {damage}", True, (255, 140, 140))
        surface.blit(dmg_text, (box_x + 12, box_y + 12))

        # Vẽ dòng Dash CD
        dash_text = self.font.render(f"Dash CD: {dash_cd_sec:.1f}s", True, (140, 210, 255))
        surface.blit(dash_text, (box_x + 12, box_y + 38))


    def draw_game_over(self, surface, screen_width, screen_height):
        """Vẽ màn hình Game Over dạng khung menu"""
        # Nền mờ toàn màn hình
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Khung menu
        box_w, box_h = 360, 260
        box_x = (screen_width  - box_w) // 2
        box_y = (screen_height - box_h) // 2
        pygame.draw.rect(surface, (40, 10, 10),  (box_x, box_y, box_w, box_h), border_radius=16)
        pygame.draw.rect(surface, (220, 50, 50), (box_x, box_y, box_w, box_h), 2, border_radius=16)

        # Chữ GAME OVER
        title = self.font_big.render("GAME OVER", True, (220, 50, 50))
        surface.blit(title, (box_x + (box_w - title.get_width()) // 2, box_y + 20))

        # Nút Play Again
        btn_w, btn_h = 220, 44
        btn_x = box_x + (box_w - btn_w) // 2
        mouse_pos = pygame.mouse.get_pos()

        r_rect = pygame.Rect(btn_x, box_y + 140, btn_w, btn_h)
        if r_rect.collidepoint(mouse_pos):
            color_bg, color_txt = (220, 50, 50), (255, 255, 255)
        else:
            color_bg, color_txt = (100, 20, 20), (255, 180, 180)
        pygame.draw.rect(surface, color_bg,      r_rect, border_radius=10)
        pygame.draw.rect(surface, (220, 50, 50), r_rect, 2, border_radius=10)
        t = self.font_btn.render("Play Again", True, color_txt)
        surface.blit(t, (btn_x + (btn_w - t.get_width()) // 2, box_y + 140 + (btn_h - t.get_height()) // 2))

        # Hint ESC
        hint = self.font.render("ESC to Quit", True, (160, 160, 160))
        surface.blit(hint, (box_x + (box_w - hint.get_width()) // 2, box_y + 205))


    def draw_victory(self, surface, screen_width, screen_height):
        """Vẽ màn hình Victory khi đánh hết tất cả wave"""
        # Nền mờ toàn màn hình
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Khung menu
        box_w, box_h = 360, 260
        box_x = (screen_width  - box_w) // 2
        box_y = (screen_height - box_h) // 2
        pygame.draw.rect(surface, (20, 30, 10),  (box_x, box_y, box_w, box_h), border_radius=16)
        pygame.draw.rect(surface, (255, 210, 50), (box_x, box_y, box_w, box_h), 2, border_radius=16)

        # Chữ VICTORY
        title = self.font_big.render("VICTORY!", True, (255, 210, 50))
        surface.blit(title, (box_x + (box_w - title.get_width()) // 2, box_y + 20))

        # Nút Play Again
        btn_w, btn_h = 220, 44
        btn_x = box_x + (box_w - btn_w) // 2
        mouse_pos = pygame.mouse.get_pos()

        r_rect = pygame.Rect(btn_x, box_y + 140, btn_w, btn_h)
        if r_rect.collidepoint(mouse_pos):
            color_bg, color_txt = (255, 210, 50), (30, 20, 10)
        else:
            color_bg, color_txt = (90, 75, 10), (255, 230, 150)
        pygame.draw.rect(surface, color_bg,       r_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 210, 50), r_rect, 2, border_radius=10)
        t = self.font_btn.render("Play Again", True, color_txt)
        surface.blit(t, (btn_x + (btn_w - t.get_width()) // 2, box_y + 140 + (btn_h - t.get_height()) // 2))

        # Hint ESC
        hint = self.font.render("ESC to Quit", True, (200, 200, 160))
        surface.blit(hint, (box_x + (box_w - hint.get_width()) // 2, box_y + 205))


    def draw(self, surface, player, screen_width, screen_height, victory=False):
        """Vẽ toàn bộ UI (hàm chính gọi từ game loop)"""
        # Vẽ thanh máu (bằng SPRITE)
        self.draw_health_bar(surface, player)
        
        # Vẽ thanh cooldown dash
        self.draw_dash_cooldown(surface, player)

        # Vẽ số vàng
        self.draw_gold(surface, player)

        # Vẽ bảng thông số DMG, Dash CD
        self.draw_stats(surface, player, screen_width)

        # Nếu đã chiến thắng, vẽ màn hình Victory (ưu tiên trước Game Over)
        if victory:
            self.draw_victory(surface, screen_width, screen_height)
        # Nếu player đã chết, vẽ màn hình Game Over
        elif hasattr(player, 'is_dead') and player.is_dead:
            self.draw_game_over(surface, screen_width, screen_height)


class PauseMenu:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_btn   = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 15, bold=True)
        self.visible    = False

        # Thông số layout — dùng chung cho draw và handle
        self.box_w, self.box_h = 340, 380
        self.btn_w, self.btn_h = 220, 44

        # Trạng thái kéo slider
        self.dragging = None  # None | "music" | "sfx"

    def toggle(self):
        self.visible = not self.visible

    def _get_positions(self, screen_width, screen_height):
        """Tính vị trí các phần tử dựa theo kích thước màn hình"""
        box_x = (screen_width  - self.box_w) // 2
        box_y = (screen_height - self.box_h) // 2
        btn_x = box_x + (self.box_w - self.btn_w) // 2
        return box_x, box_y, btn_x

    def _slider_rect(self, btn_x, y):
        """Trả về rect của vùng kéo slider"""
        return pygame.Rect(btn_x, y + 22, self.btn_w, 14)

    def _draw_slider(self, surface, label, value, btn_x, y):
        """Vẽ 1 thanh slider có thể kéo"""
        txt = self.font_small.render(f"{label}: {int(value*100)}%", True, (200, 200, 200))
        surface.blit(txt, (btn_x, y))

        bar_y  = y + 22
        bar_w  = self.btn_w
        fill_w = int(bar_w * value)

        # Nền thanh
        pygame.draw.rect(surface, (60, 60, 60),    (btn_x, bar_y, bar_w, 10), border_radius=4)
        # Phần fill
        pygame.draw.rect(surface, (255, 210, 100), (btn_x, bar_y, fill_w, 10), border_radius=4)
        # Viền
        pygame.draw.rect(surface, (200, 200, 200), (btn_x, bar_y, bar_w, 10), 1, border_radius=4)

        # Nút tròn kéo
        knob_x = btn_x + fill_w
        knob_x = max(btn_x + 7, min(btn_x + bar_w - 7, knob_x))
        pygame.draw.circle(surface, (255, 210, 100), (knob_x, bar_y + 5), 8)
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, bar_y + 5), 8, 2)

    def draw(self, surface, screen_width, screen_height, music_volume=0.5, sfx_volume=0.5):
        if not self.visible:
            return

        # Nền mờ
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        box_x, box_y, btn_x = self._get_positions(screen_width, screen_height)

        # Khung
        pygame.draw.rect(surface, (30, 20, 50),    (box_x, box_y, self.box_w, self.box_h), border_radius=16)
        pygame.draw.rect(surface, (255, 210, 100), (box_x, box_y, self.box_w, self.box_h), 2, border_radius=16)

        # Tiêu đề
        title = self.font_title.render("PAUSE", True, (255, 210, 100))
        surface.blit(title, (box_x + (self.box_w - title.get_width()) // 2, box_y + 20))

        mouse_pos = pygame.mouse.get_pos()

        # Nút Resume
        resume_rect = pygame.Rect(btn_x, box_y + 90, self.btn_w, self.btn_h)
        if resume_rect.collidepoint(mouse_pos):
            color_bg, color_txt = (255, 210, 100), (30, 20, 50)
        else:
            color_bg, color_txt = (60, 45, 90), (255, 255, 255)
        pygame.draw.rect(surface, color_bg,        resume_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 210, 100), resume_rect, 2, border_radius=10)
        t = self.font_btn.render("Resume", True, color_txt)
        surface.blit(t, (btn_x + (self.btn_w - t.get_width()) // 2, box_y + 90 + (self.btn_h - t.get_height()) // 2))

        # Slider Music
        self._draw_slider(surface, "Music", music_volume, btn_x, box_y + 158)

        # Slider SFX
        self._draw_slider(surface, "SFX  ", sfx_volume,   btn_x, box_y + 220)

        # Nút Quit
        quit_rect = pygame.Rect(btn_x, box_y + 296, self.btn_w, self.btn_h)
        if quit_rect.collidepoint(mouse_pos):
            color_bg, color_txt = (200, 50, 50), (255, 255, 255)
        else:
            color_bg, color_txt = (100, 30, 30), (255, 180, 180)
        pygame.draw.rect(surface, color_bg,      quit_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 80, 80), quit_rect, 2, border_radius=10)
        t = self.font_btn.render("Quit", True, color_txt)
        surface.blit(t, (btn_x + (self.btn_w - t.get_width()) // 2, box_y + 296 + (self.btn_h - t.get_height()) // 2))

    def handle_mousedown(self, pos, screen_width, screen_height):
        """Gọi khi nhấn chuột — kiểm tra có click vào slider không"""
        if not self.visible:
            return None
        box_x, box_y, btn_x = self._get_positions(screen_width, screen_height)

        if self._slider_rect(btn_x, box_y + 158).collidepoint(pos):
            self.dragging = "music"
            return "drag"
        if self._slider_rect(btn_x, box_y + 220).collidepoint(pos):
            self.dragging = "sfx"
            return "drag"
        return None

    def handle_mousemotion(self, pos, screen_width, screen_height):
        """Gọi khi kéo chuột — trả về (loại, giá trị mới) hoặc None"""
        if not self.visible or self.dragging is None:
            return None
        _, _, btn_x = self._get_positions(screen_width, screen_height)
        # Tính volume từ vị trí chuột trên thanh
        value = (pos[0] - btn_x) / self.btn_w
        value = max(0.0, min(1.0, value))
        return (self.dragging, value)

    def handle_mouseup(self):
        """Gọi khi thả chuột"""
        self.dragging = None

    def handle_click(self, pos, screen_width, screen_height):
        """Xử lý click nút Resume/Quit"""
        if not self.visible:
            return None
        box_x, box_y, btn_x = self._get_positions(screen_width, screen_height)

        if pygame.Rect(btn_x, box_y + 90,  self.btn_w, self.btn_h).collidepoint(pos):
            self.visible = False
            return "resume"
        if pygame.Rect(btn_x, box_y + 296, self.btn_w, self.btn_h).collidepoint(pos):
            return "quit"
        return None