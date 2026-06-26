import pygame
import os

# ================================================================================================
# CLASS ANIMATEDOBJECT — Vật thể có animation (ảnh tĩnh + chuỗi frame)
# Hỗ trợ: bật/tắt animation, cập nhật theo thời gian, vẽ theo camera
# ================================================================================================

class AnimatedObject:
    def __init__(self, x, y, static_image_path, animation_folder, frame_duration=0.05):
        """
        x, y: vị trí world
        static_image_path: đường dẫn ảnh tĩnh (hiển thị khi tắt animation)
        animation_folder: thư mục chứa frame animation
        frame_duration: thời gian mỗi frame (giây)
        """
        self.x = x
        self.y = y
        
        # Load ảnh tĩnh
        self.static_image = pygame.image.load(static_image_path).convert_alpha()
        
        # Load animation frames
        self.animation_frames = []
        self.load_animation_frames(animation_folder)
        
        # Biến điều khiển animation
        self.current_frame = 0              # Chỉ số frame hiện tại
        self.frame_duration = frame_duration  # Thời gian mỗi frame (giây)
        self.timer = 0                      # Bộ đếm thời gian chuyển frame
        self.animation_enabled = True       # Đang chạy animation
        self.current_image = self.static_image  # Ảnh hiển thị hiện tại
    
    # Load tối đa 24 frame từ folder, sắp xếp theo tên
    def load_animation_frames(self, folder_path):
        try:
            # Lọc file ảnh, sắp xếp theo tên
            image_files = sorted([f for f in os.listdir(folder_path) 
                                 if f.endswith(('.png', '.jpg', '.jpeg'))])
            
            # Giới hạn 24 frame
            image_files = image_files[:24]
            
            # Load từng frame
            for image_file in image_files:
                frame = pygame.image.load(os.path.join(folder_path, image_file)).convert_alpha()
                self.animation_frames.append(frame)
            
            print(f"Đã load {len(self.animation_frames)} frame animation từ {folder_path}")
        except Exception as e:
            print(f"Lỗi khi load animation: {e}")
    
    # Cập nhật animation: chuyển frame khi đủ thời gian
    def update(self, delta_time):
        # Animation tắt hoặc không có frame → hiển thị ảnh tĩnh
        if not self.animation_enabled or not self.animation_frames:
            self.current_image = self.static_image
            return
        
        self.timer += delta_time
        
        # Đủ thời gian → chuyển frame tiếp theo (loop)
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            self.current_image = self.animation_frames[self.current_frame]
    
    # Vẽ object tại vị trí world (trừ camera offset)
    def draw(self, surface, camera):
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        surface.blit(self.current_image, (draw_x, draw_y))
    
    # Bật animation
    def enable_animation(self):
        self.animation_enabled = True
        
    # Tắt animation → hiển thị ảnh tĩnh
    def disable_animation(self):
        self.animation_enabled = False
        self.current_image = self.static_image