import pygame
import os
from knight1_animation import Animation

# CẤU HÌNH ANIMATION CHO VAMPIRES1
# Mô tả: Định nghĩa cấu trúc thư mục, tên file và số lượng frame cho từng loại animation
VAMPIRES1_ANIMATION_CONFIGS = {
    # Animation đứng yên (idle) - 4 frame cho mỗi hướng
    # Sử dụng khi quái đứng yên không di chuyển
    "idle": {
        "folder": "vampires1_idle", # Thư mục con chứa sprite
        "directions": {
            "up":    {"prefix": "vampires1_idle_up",    "frames": 4},
            "down":  {"prefix": "vampires1_idle_down",  "frames": 4},
            "left":  {"prefix": "vampires1_idle_left",  "frames": 4},
            "right": {"prefix": "vampires1_idle_right", "frames": 4},
        },
    },
    # Animation đi bộ (walk) - 6 frame cho mỗi hướng
    "walk": {
        "folder": "vampires1_walk",
        "directions": {
            "up":    {"prefix": "vampires1_walk_up",    "frames": 6},
            "down":  {"prefix": "vampires1_walk_down",  "frames": 6},
            "left":  {"prefix": "vampires1_walk_left",  "frames": 6},
            "right": {"prefix": "vampires1_walk_right", "frames": 6},
        },
    },
    # Animation chạy (run) - 8 frame cho mỗi hướng
    "run": {
        "folder": "vampires1_run",
        "directions": {
            "up":    {"prefix": "vampires1_run_up",    "frames": 8},
            "down":  {"prefix": "vampires1_run_down",  "frames": 8},
            "left":  {"prefix": "vampires1_run_left",  "frames": 8},
            "right": {"prefix": "vampires1_run_right", "frames": 8},
        },
    },
    # Animation tấn công (attack) - 9 frame cho mỗi hướng
    "attack": {
        "folder": "vampires1_attack",
        "directions": {
            "up":    {"prefix": "vampires1_attack_up",    "frames": 9},
            "down":  {"prefix": "vampires1_attack_down",  "frames": 9},
            "left":  {"prefix": "vampires1_attack_left",  "frames": 9},
            "right": {"prefix": "vampires1_attack_right", "frames": 9},
        },
    },
    # Animation bị thương (hit) - 4 frame cho mỗi hướng
    "hit": {
        "folder": "vampires1_hurt",
        "directions": {
            "up":    {"prefix": "vampires1_hurt_up",    "frames": 4},
            "down":  {"prefix": "vampires1_hurt_down",  "frames": 4},
            "left":  {"prefix": "vampires1_hurt_left",  "frames": 4},
            "right": {"prefix": "vampires1_hurt_right", "frames": 4},
        },
    },
    # Animation chết (death) - 11 frame cho mỗi hướng
    "death": {
        "folder": "vampires1_death",
        "directions": {
            "up":    {"prefix": "vampires1_death_up",    "frames": 11},
            "down":  {"prefix": "vampires1_death_down",  "frames": 11},
            "left":  {"prefix": "vampires1_death_left",  "frames": 11},
            "right": {"prefix": "vampires1_death_right", "frames": 11},
        },
    },
}

# Thời gian mỗi frame (ms) cho từng loại animation
# Thời gian càng nhỏ, animation chạy càng nhanh
FRAME_DURATIONS = {
    "idle":   100,
    "walk":   100,
    "run":    90,
    "attack": 80,
    "hit":    75,
    "death":  50,
}

# Màu fallback khi không tìm thấy sprite
FALLBACK_COLOR = (128, 0, 128)  # tím


# CLASS LOADER — tải tất cả animation cho Vampires1
# Mô tả: Class chịu trách nhiệm load toàn bộ sprite animation từ thư mục assets
# Sử dụng pattern Class Method để gọi trực tiếp không cần khởi tạo đối tượng
class Vampires1AnimationLoader:
   

    # Đường dẫn gốc đến thư mục chứa tất cả sprite của vampires1
    BASE_PATH = os.path.join("assets", "resource_vampires1_2_3", "vampires1")

    # Tải tất cả animation theo VAMPIRES1_ANIMATION_CONFIGS.
    @classmethod
    def load_all(cls, scale_factor: float = 2.0) -> dict:
        """
        Tải tất cả animation theo VAMPIRES1_ANIMATION_CONFIGS.
        Trả về dict đầy đủ các loại animation.
        """
        if not os.path.exists(cls.BASE_PATH):
            print(f"[Vampires1Anim] Thư mục không tồn tại: {cls.BASE_PATH}")

        all_anims = {}
        for anim_type, duration in FRAME_DURATIONS.items():
            loaded = cls._load_anim_type(anim_type, duration, scale_factor)
            all_anims[anim_type] = cls._ensure_fallback(loaded, anim_type, duration)

        return all_anims

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    @classmethod
    def _load_anim_type(cls, anim_type: str, frame_duration: int, scale_factor: float) -> dict:
        """Tải một loại animation (idle / walk / …) cho cả 4 hướng."""
        anims = {}
        config = VAMPIRES1_ANIMATION_CONFIGS.get(anim_type)
        if not config:
            return anims

        folder = config["folder"]
        for direction, dir_cfg in config["directions"].items():
            frames = cls._load_frames(folder, dir_cfg, scale_factor)
            if frames:
                anims[direction] = Animation(frames, frame_duration)
                print(f"[Vampires1Anim] Loaded {len(frames)} frames — {anim_type}/{direction}")

        return anims

    @classmethod
    def _load_frames(cls, folder: str, dir_cfg: dict, scale_factor: float) -> list:
        """Tải danh sách surface cho một hướng cụ thể."""
        prefix      = dir_cfg["prefix"]
        frame_count = dir_cfg["frames"]
        frames      = []

        for i in range(1, frame_count + 1):
            filepath = os.path.join(cls.BASE_PATH, folder, f"{prefix}{i}.png")
            try:
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    if scale_factor != 1.0:
                        new_size = (
                            int(img.get_width()  * scale_factor),
                            int(img.get_height() * scale_factor),
                        )
                        img = pygame.transform.scale(img, new_size)
                    frames.append(img)
                else:
                    frames.append(cls._make_fallback())
            except Exception as e:
                print(f"[Vampires1Anim] Lỗi load {filepath}: {e}")
                frames.append(cls._make_fallback())

        return frames

    @staticmethod
    def _make_fallback(size: int = 64) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill(FALLBACK_COLOR)
        return surf

    @classmethod
    def _ensure_fallback(cls, anims: dict, anim_type: str, duration: int) -> dict:
        """Đảm bảo 4 hướng đều có Animation, tạo fallback nếu thiếu."""
        if anims:
            return anims

        print(f"[Vampires1Anim] Tạo animation fallback cho: {anim_type}")
        fallback_frame = [cls._make_fallback()]
        return {d: Animation(fallback_frame, duration) for d in ("up", "down", "left", "right")}