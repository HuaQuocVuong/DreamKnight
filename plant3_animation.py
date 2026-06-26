import pygame
import os
from knight1_animation import Animation

# ================================================================================================
# CẤU HÌNH ANIMATION CHO PLANT3 (đầy đủ idle, walk, run, attack, hit, death)
# ================================================================================================

PLANT3_ANIMATION_CONFIGS = {
    # Animation đứng yên — 4 frame mỗi hướng, 200ms/frame
    "idle": {
        "folder": "plant3_idle",
        "directions": {
            "up":    {"prefix": "plant3_idle_up",    "frames": 4},
            "down":  {"prefix": "plant3_idle_down",  "frames": 4},
            "left":  {"prefix": "plant3_idle_left",  "frames": 4},
            "right": {"prefix": "plant3_idle_right", "frames": 4},
        },
    },
    # Animation đi bộ — 6 frame, 100ms/frame, tốc độ PLAYER_SPEED * 0.4
    "walk": {
        "folder": "plant3_walk",
        "directions": {
            "up":    {"prefix": "plant3_walk_up",    "frames": 6},
            "down":  {"prefix": "plant3_walk_down",  "frames": 6},
            "left":  {"prefix": "plant3_walk_left",  "frames": 6},
            "right": {"prefix": "plant3_walk_right", "frames": 6},
        },
    },
    # Animation chạy — 8 frame, 90ms/frame, tốc độ RUN_SPEED * 0.5
    "run": {
        "folder": "plant3_run",
        "directions": {
            "up":    {"prefix": "plant3_run_up",    "frames": 8},
            "down":  {"prefix": "plant3_run_down",  "frames": 8},
            "left":  {"prefix": "plant3_run_left",  "frames": 8},
            "right": {"prefix": "plant3_run_right", "frames": 8},
        },
    },
    # Animation tấn công — 7 frame, 70ms/frame (tổng 490ms)
    "attack": {
        "folder": "plant3_attack",
        "directions": {
            "up":    {"prefix": "plant3_attack_up",    "frames": 7},
            "down":  {"prefix": "plant3_attack_down",  "frames": 7},
            "left":  {"prefix": "plant3_attack_left",  "frames": 7},
            "right": {"prefix": "plant3_attack_right", "frames": 7},
        },
    },
    # Animation bị thương — 5 frame, 75ms/frame (tổng 375ms, code dùng 300ms)
    "hit": {
        "folder": "plant3_hurt",
        "directions": {
            "up":    {"prefix": "plant3_hurt_up",    "frames": 5},
            "down":  {"prefix": "plant3_hurt_down",  "frames": 5},
            "left":  {"prefix": "plant3_hurt_left",  "frames": 5},
            "right": {"prefix": "plant3_hurt_right", "frames": 5},
        },
    },
    # Animation chết — 10 frame, 50ms/frame (tổng 500ms)
    "death": {
        "folder": "plant3_death",
        "directions": {
            "up":    {"prefix": "plant3_death_up",    "frames": 10},
            "down":  {"prefix": "plant3_death_down",  "frames": 10},
            "left":  {"prefix": "plant3_death_left",  "frames": 10},
            "right": {"prefix": "plant3_death_right", "frames": 10},
        },
    },
}

# Thời gian mỗi frame (ms) — càng nhỏ animation càng nhanh
FRAME_DURATIONS = {
    "idle":   200,   # Chậm, tạo cảm giác thở
    "walk":   100,   # Vừa phải, đồng bộ với tốc độ đi bộ
    "run":    90,    # Nhanh, phù hợp tốc độ chạy
    "attack": 70,    # Nhanh, tạo cảm giác dứt khoát
    "hit":    75,    # Nhanh, animation ngắn gọn
    "death":  50,    # Nhanh nhất, không delay game
}

# Màu fallback khi không tìm thấy sprite — xanh lá đậm
FALLBACK_COLOR = (0, 100, 0)


# ================================================================================================
# CLASS LOADER — tải tất cả animation cho Plant3 từ assets
# ================================================================================================

class Plant3AnimationLoader:
    """
    Tải toàn bộ animation của Plant3 từ thư mục assets.
    Trả về dict lồng: { anim_type: { direction: Animation } }
    
    Cấu trúc thư mục:
    assets/resource_plant1_2_3/plant3/
        ├── plant3_idle/
        ├── plant3_walk/
        ├── plant3_run/
        ├── plant3_attack/
        ├── plant3_hurt/
        └── plant3_death/
    """

    # Đường dẫn gốc đến thư mục sprite plant3
    BASE_PATH = os.path.join("assets", "resource_plant1_2_3", "plant3")

    @classmethod
    def load_all(cls, scale_factor: float = 2.0) -> dict:
        """
        Tải tất cả animation theo config, scale về kích thước mong muốn
        scale_factor: hệ số phóng to (mặc định 2.0)
        """
        if not os.path.exists(cls.BASE_PATH):
            print(f"[Plant3Anim] Thư mục không tồn tại: {cls.BASE_PATH}")

        all_anims = {}
        # Lặp qua từng loại animation (idle, walk, run, attack, hit, death)
        for anim_type, duration in FRAME_DURATIONS.items():
            loaded = cls._load_anim_type(anim_type, duration, scale_factor)
            # Đảm bảo luôn có 4 hướng, tạo fallback nếu load thất bại
            all_anims[anim_type] = cls._ensure_fallback(loaded, anim_type, duration)

        return all_anims

    @classmethod
    def _load_anim_type(cls, anim_type: str, frame_duration: int, scale_factor: float) -> dict:
        """Tải một loại animation cho cả 4 hướng, trả về dict {direction: Animation}"""
        anims = {}
        config = PLANT3_ANIMATION_CONFIGS.get(anim_type)
        if not config:
            return anims

        folder = config["folder"]
        for direction, dir_cfg in config["directions"].items():
            frames = cls._load_frames(folder, dir_cfg, scale_factor)
            if frames:
                anims[direction] = Animation(frames, frame_duration)
                print(f"[Plant3Anim] Loaded {len(frames)} frames — {anim_type}/{direction}")

        return anims

    @classmethod
    def _load_frames(cls, folder: str, dir_cfg: dict, scale_factor: float) -> list:
        """
        Tải danh sách surface cho một hướng cụ thể
        Cách đặt tên file: {prefix}{i}.png (vd: plant3_idle_down1.png)
        """
        prefix = dir_cfg["prefix"]
        frame_count = dir_cfg["frames"]
        frames = []

        for i in range(1, frame_count + 1):
            filepath = os.path.join(cls.BASE_PATH, folder, f"{prefix}{i}.png")
            try:
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    # Scale nếu cần
                    if scale_factor != 1.0:
                        new_size = (
                            int(img.get_width() * scale_factor),
                            int(img.get_height() * scale_factor),
                        )
                        img = pygame.transform.scale(img, new_size)
                    frames.append(img)
                else:
                    # File không tồn tại → dùng fallback
                    frames.append(cls._make_fallback())
            except Exception as e:
                print(f"[Plant3Anim] Lỗi load {filepath}: {e}")
                frames.append(cls._make_fallback())

        return frames

    @staticmethod
    def _make_fallback(size: int = 64) -> pygame.Surface:
        """Tạo surface vuông màu xanh lá đậm khi không load được sprite"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill(FALLBACK_COLOR)
        return surf

    @classmethod
    def _ensure_fallback(cls, anims: dict, anim_type: str, duration: int) -> dict:
        """Đảm bảo luôn có 4 hướng, nếu load thất bại → tạo fallback cho tất cả"""
        if anims:
            return anims

        print(f"[Plant3Anim] Tạo animation fallback cho: {anim_type}")
        fallback_frame = [cls._make_fallback()]
        return {d: Animation(fallback_frame, duration) for d in ("up", "down", "left", "right")}