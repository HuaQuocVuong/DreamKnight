import pygame
import os
from knight1_animation import Animation

# ================================================================================================
# CẤU HÌNH ANIMATION CHO SLIME1
# ================================================================================================

SLIME1_ANIMATION_CONFIGS = {
    # Animation đứng yên — 6 frame mỗi hướng, 200ms/frame
    "idle": {
        "folder": "slime1_idle",
        "directions": {
            "up":    {"prefix": "slime1_idle_up",    "frames": 6},
            "down":  {"prefix": "slime1_idle_down",  "frames": 6},
            "left":  {"prefix": "slime1_idle_left",  "frames": 6},
            "right": {"prefix": "slime1_idle_right", "frames": 6},
        },
    },
    # Animation đi bộ — 6 frame, 100ms/frame
    "walk": {
        "folder": "slime1_walk",
        "directions": {
            "up":    {"prefix": "slime1_walk_up",    "frames": 6},
            "down":  {"prefix": "slime1_walk_down",  "frames": 6},
            "left":  {"prefix": "slime1_walk_left",  "frames": 6},
            "right": {"prefix": "slime1_walk_right", "frames": 6},
        },
    },
    # Animation chạy — 8 frame, 60ms/frame
    "run": {
        "folder": "slime1_run",
        "directions": {
            "up":    {"prefix": "slime1_run_up",    "frames": 8},
            "down":  {"prefix": "slime1_run_down",  "frames": 8},
            "left":  {"prefix": "slime1_run_left",  "frames": 8},
            "right": {"prefix": "slime1_run_right", "frames": 8},
        },
    },
    # Animation tấn công — 10 frame, 70ms/frame (tổng 700ms, code dùng 550ms)
    "attack": {
        "folder": "slime1_attack",
        "directions": {
            "up":    {"prefix": "slime1_attack_up",    "frames": 10},
            "down":  {"prefix": "slime1_attack_down",  "frames": 10},
            "left":  {"prefix": "slime1_attack_left",  "frames": 10},
            "right": {"prefix": "slime1_attack_right", "frames": 10},
        },
    },
    # Animation bị thương — 5 frame, 100ms/frame (tổng 500ms, code dùng 300ms)
    "hit": {
        "folder": "slime1_hurt",
        "directions": {
            "up":    {"prefix": "slime1_hurt_up",    "frames": 5},
            "down":  {"prefix": "slime1_hurt_down",  "frames": 5},
            "left":  {"prefix": "slime1_hurt_left",  "frames": 5},
            "right": {"prefix": "slime1_hurt_right", "frames": 5},
        },
    },
    # Animation chết — 10 frame, 50ms/frame (tổng 500ms)
    "death": {
        "folder": "slime1_death",
        "directions": {
            "up":    {"prefix": "slime1_death_up",    "frames": 10},
            "down":  {"prefix": "slime1_death_down",  "frames": 10},
            "left":  {"prefix": "slime1_death_left",  "frames": 10},
            "right": {"prefix": "slime1_death_right", "frames": 10},
        },
    },
}

# Thời gian mỗi frame (ms) — càng nhỏ animation càng nhanh
FRAME_DURATIONS = {
    "idle":   200,   # Chậm, tạo cảm giác thở
    "walk":   100,   # Vừa phải, đồng bộ với tốc độ đi bộ
    "run":    60,    # Nhanh, phù hợp tốc độ chạy
    "attack": 70,    # Nhanh, tạo cảm giác dứt khoát
    "hit":    100,   # Vừa phải, animation ngắn gọn
    "death":  50,    # Nhanh nhất, không delay game
}

# Màu fallback khi không tìm thấy sprite — tím
FALLBACK_COLOR = (128, 0, 128)


# ================================================================================================
# CLASS LOADER — tải tất cả animation cho Slime1 từ assets
# ================================================================================================

class Slime1AnimationLoader:
    """
    Tải toàn bộ animation của Slime1 từ thư mục assets.
    Trả về dict lồng: { anim_type: { direction: Animation } }
    
    Cấu trúc thư mục:
    assets/resource_slime1_2_3/slime_1/
        ├── slime1_idle/
        ├── slime1_walk/
        ├── slime1_run/
        ├── slime1_attack/
        ├── slime1_hurt/
        └── slime1_death/
    """

    # Đường dẫn gốc đến thư mục sprite slime1
    BASE_PATH = os.path.join("assets", "resource_slime1_2_3", "slime_1")

    @classmethod
    def load_all(cls, scale_factor: float = 2.0) -> dict:
        """
        Tải tất cả animation theo config, scale về kích thước mong muốn
        scale_factor: hệ số phóng to (mặc định 2.0)
        """
        if not os.path.exists(cls.BASE_PATH):
            print(f"[Slime1Anim] Thư mục không tồn tại: {cls.BASE_PATH}")

        all_anims = {}
        # Lặp qua từng loại animation (idle, walk, run, attack, hit, death)
        for anim_type, duration in FRAME_DURATIONS.items():
            loaded = cls._load_anim_type(anim_type, duration, scale_factor)
            # Đảm bảo luôn có 4 hướng, tạo fallback nếu load thất bại
            all_anims[anim_type] = cls._ensure_fallback(loaded, anim_type, duration)

        return all_anims

    # ------------------------------------------------------------------
    # INTERNAL HELPERS — Các hàm hỗ trợ load
    # ------------------------------------------------------------------

    @classmethod
    def _load_anim_type(cls, anim_type: str, frame_duration: int, scale_factor: float) -> dict:
        """Tải một loại animation cho cả 4 hướng, trả về dict {direction: Animation}"""
        anims = {}
        config = SLIME1_ANIMATION_CONFIGS.get(anim_type)
        if not config:
            return anims

        folder = config["folder"]
        for direction, dir_cfg in config["directions"].items():
            frames = cls._load_frames(folder, dir_cfg, scale_factor)
            if frames:
                anims[direction] = Animation(frames, frame_duration)
                print(f"[Slime1Anim] Loaded {len(frames)} frames — {anim_type}/{direction}")

        return anims

    @classmethod
    def _load_frames(cls, folder: str, dir_cfg: dict, scale_factor: float) -> list:
        """
        Tải danh sách surface cho một hướng cụ thể
        Cách đặt tên file: {prefix}{i}.png (vd: slime1_idle_down1.png)
        """
        prefix      = dir_cfg["prefix"]
        frame_count = dir_cfg["frames"]
        frames      = []

        for i in range(1, frame_count + 1):
            filepath = os.path.join(cls.BASE_PATH, folder, f"{prefix}{i}.png")
            try:
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    # Scale nếu cần
                    if scale_factor != 1.0:
                        new_size = (
                            int(img.get_width()  * scale_factor),
                            int(img.get_height() * scale_factor),
                        )
                        img = pygame.transform.scale(img, new_size)
                    frames.append(img)
                else:
                    # File không tồn tại → dùng fallback
                    frames.append(cls._make_fallback())
            except Exception as e:
                print(f"[Slime1Anim] Lỗi load {filepath}: {e}")
                frames.append(cls._make_fallback())

        return frames

    @staticmethod
    def _make_fallback(size: int = 64) -> pygame.Surface:
        """Tạo surface vuông màu tím khi không load được sprite"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill(FALLBACK_COLOR)
        return surf

    @classmethod
    def _ensure_fallback(cls, anims: dict, anim_type: str, duration: int) -> dict:
        """Đảm bảo luôn có 4 hướng, nếu load thất bại → tạo fallback cho tất cả"""
        if anims:
            return anims

        print(f"[Slime1Anim] Tạo animation fallback cho: {anim_type}")
        fallback_frame = [cls._make_fallback()]
        return {d: Animation(fallback_frame, duration) for d in ("up", "down", "left", "right")}