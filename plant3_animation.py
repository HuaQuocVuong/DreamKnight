# plant3_animation.py
import pygame
import os
from knight1_animation import Animation

# ================================================================================================
# CẤU HÌNH ANIMATION CHO PLANT3 (đầy đủ idle, walk, run, attack, hit, death)
# ================================================================================================

PLANT3_ANIMATION_CONFIGS = {
    "idle": {
        "folder": "plant3_idle",
        "directions": {
            "up":    {"prefix": "plant3_idle_up",    "frames": 4},
            "down":  {"prefix": "plant3_idle_down",  "frames": 4},
            "left":  {"prefix": "plant3_idle_left",  "frames": 4},
            "right": {"prefix": "plant3_idle_right", "frames": 4},
        },
    },
    "walk": {
        "folder": "plant3_walk",
        "directions": {
            "up":    {"prefix": "plant3_walk_up",    "frames": 6},
            "down":  {"prefix": "plant3_walk_down",  "frames": 6},
            "left":  {"prefix": "plant3_walk_left",  "frames": 6},
            "right": {"prefix": "plant3_walk_right", "frames": 6},
        },
    },
    "run": {
        "folder": "plant3_run",
        "directions": {
            "up":    {"prefix": "plant3_run_up",    "frames": 8},
            "down":  {"prefix": "plant3_run_down",  "frames": 8},
            "left":  {"prefix": "plant3_run_left",  "frames": 8},
            "right": {"prefix": "plant3_run_right", "frames": 8},
        },
    },
    "attack": {
        "folder": "plant3_attack",
        "directions": {
            "up":    {"prefix": "plant3_attack_up",    "frames": 7},
            "down":  {"prefix": "plant3_attack_down",  "frames": 7},
            "left":  {"prefix": "plant3_attack_left",  "frames": 7},
            "right": {"prefix": "plant3_attack_right", "frames": 7},
        },
    },
    "hit": {
        "folder": "plant3_hurt",
        "directions": {
            "up":    {"prefix": "plant3_hurt_up",    "frames": 5},
            "down":  {"prefix": "plant3_hurt_down",  "frames": 5},
            "left":  {"prefix": "plant3_hurt_left",  "frames": 5},
            "right": {"prefix": "plant3_hurt_right", "frames": 5},
        },
    },
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

FRAME_DURATIONS = {
    "idle":   200,
    "walk":   100,
    "run":    90,
    "attack": 70,
    "hit":    75,
    "death":  50,
}

FALLBACK_COLOR = (0, 100, 0)  # Dark Green


class Plant3AnimationLoader:
    BASE_PATH = os.path.join("assets", "resource_plant1_2_3", "plant3")

    @classmethod
    def load_all(cls, scale_factor: float = 2.0) -> dict:
        if not os.path.exists(cls.BASE_PATH):
            print(f"[Plant3Anim] Thư mục không tồn tại: {cls.BASE_PATH}")

        all_anims = {}
        for anim_type, duration in FRAME_DURATIONS.items():
            loaded = cls._load_anim_type(anim_type, duration, scale_factor)
            all_anims[anim_type] = cls._ensure_fallback(loaded, anim_type, duration)

        return all_anims

    @classmethod
    def _load_anim_type(cls, anim_type: str, frame_duration: int, scale_factor: float) -> dict:
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
        prefix = dir_cfg["prefix"]
        frame_count = dir_cfg["frames"]
        frames = []

        for i in range(1, frame_count + 1):
            filepath = os.path.join(cls.BASE_PATH, folder, f"{prefix}{i}.png")
            try:
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    if scale_factor != 1.0:
                        new_size = (
                            int(img.get_width() * scale_factor),
                            int(img.get_height() * scale_factor),
                        )
                        img = pygame.transform.scale(img, new_size)
                    frames.append(img)
                else:
                    frames.append(cls._make_fallback())
            except Exception as e:
                print(f"[Plant3Anim] Lỗi load {filepath}: {e}")
                frames.append(cls._make_fallback())

        return frames

    @staticmethod
    def _make_fallback(size: int = 64) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill(FALLBACK_COLOR)
        return surf

    @classmethod
    def _ensure_fallback(cls, anims: dict, anim_type: str, duration: int) -> dict:
        if anims:
            return anims

        print(f"[Plant3Anim] Tạo animation fallback cho: {anim_type}")
        fallback_frame = [cls._make_fallback()]
        return {d: Animation(fallback_frame, duration) for d in ("up", "down", "left", "right")}