import pygame
import os

# ================================================================================================
# CLASS GAMEOBJECT — Đối tượng trong game (ảnh tĩnh hoặc animation)
# Hỗ trợ: load ảnh, animation, scale, cập nhật theo thời gian, vẽ theo camera
# ================================================================================================

class GameObject:
    def __init__(self, x, y, image_path=None, animation_folder=None, frame_duration=0.05, scale=1.0):
        """
        x, y: vị trí world
        image_path: đường dẫn ảnh tĩnh (None nếu chỉ dùng animation)
        animation_folder: thư mục chứa frame animation (None nếu chỉ dùng ảnh tĩnh)
        frame_duration: thời gian mỗi frame (giây)
        scale: hệ số phóng to
        """
        self.x = x
        self.y = y
        self.scale = scale  
        
        # Lưu đường dẫn để dùng sau (reload khi đổi scale)
        self.image_path = image_path
        self.animation_folder = animation_folder
        
        # Ảnh tĩnh (nếu có)
        self.static_image = None
        if image_path:
            try:
                self.static_image = pygame.image.load(image_path).convert_alpha()
                if scale != 1.0:
                    self.static_image = self._scale_image(self.static_image)
                self.current_image = self.static_image
            except Exception as e:
                print(f"Không thể load ảnh: {image_path} - Lỗi: {e}")
                self.static_image = None
                self.current_image = None
        else:
            self.current_image = None  # Sẽ set khi load animation
        
        # Animation
        self.animation_frames = []    # Danh sách frame
        self.is_animating = False     # Đang chạy animation
        self.current_frame = 0        # Chỉ số frame hiện tại
        self.timer = 0                # Bộ đếm thời gian chuyển frame
        self.frame_duration = frame_duration
        
        # Load animation nếu có folder
        if animation_folder:
            self.load_animation(animation_folder)
            
    # Scale ảnh theo self.scale
    def _scale_image(self, image):
        if self.scale == 1.0:
            return image
        new_width = int(image.get_width() * self.scale)
        new_height = int(image.get_height() * self.scale)
        return pygame.transform.scale(image, (new_width, new_height))
    
    # Load tối đa 24 frame từ folder, sắp xếp theo tên
    def load_animation(self, folder_path):
        try:
            if not os.path.exists(folder_path):
                print(f"Thư mục không tồn tại: {folder_path}")
                return
                
            # Lọc file ảnh (.png, .jpg, .jpeg), sắp xếp theo tên
            image_files = sorted([f for f in os.listdir(folder_path) 
                                 if f.endswith(('.png', '.jpg', '.jpeg'))])
            
            if not image_files:
                print(f"Không tìm thấy file ảnh nào trong {folder_path}")
                return
            
            # Giới hạn 24 frame
            image_files = image_files[:24]
            
            # Load từng frame
            self.animation_frames = []
            for image_file in image_files:
                frame_path = os.path.join(folder_path, image_file)
                frame = pygame.image.load(frame_path).convert_alpha()
                if self.scale != 1.0:
                    frame = self._scale_image(frame)
                self.animation_frames.append(frame)

            # Kích hoạt animation nếu có frame
            if self.animation_frames:
                self.is_animating = True
                self.current_image = self.animation_frames[0]
                print(f"Đã load {len(self.animation_frames)} frame animation từ {folder_path}")
            else:
                print(f"Không tìm thấy ảnh animation trong {folder_path}")

        except Exception as e:
            print(f"Lỗi khi load animation: {e}")
    
    # Cập nhật animation: chuyển frame khi đủ thời gian
    def update(self, delta_time):
        if not self.is_animating or not self.animation_frames:
            return
        
        self.timer += delta_time  # delta_time: giây

        if self.timer >= self.frame_duration:
            self.timer = 0
            # Loop: quay về frame 0 khi hết
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            self.current_image = self.animation_frames[self.current_frame]
    
    # Vẽ object tại vị trí world (trừ camera offset)
    def draw(self, surface, camera):
        if not self.current_image:
            return
            
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        surface.blit(self.current_image, (draw_x, draw_y))

    # Bật animation (nếu có frame)
    def enable_animation(self):
        if self.animation_frames:
            self.is_animating = True

    # Tắt animation → hiển thị ảnh tĩnh
    def disable_animation(self):
        if self.static_image:
            self.is_animating = False
            self.current_image = self.static_image

    # Reset animation về frame đầu
    def reset_animation(self):
        self.current_frame = 0
        self.timer = 0
        if self.animation_frames:
            self.current_image = self.animation_frames[0]

    # Đổi scale và reload lại ảnh + animation
    def set_scale(self, new_scale):
        self.scale = new_scale
        
        # Reload ảnh tĩnh với scale mới
        if self.image_path and self.static_image:
            try:
                original = pygame.image.load(self.image_path).convert_alpha()
                self.static_image = self._scale_image(original)
                if not self.is_animating:
                    self.current_image = self.static_image
            except Exception as e:
                print(f"Lỗi khi reload ảnh tĩnh: {e}")
        
        # Reload animation với scale mới
        if self.animation_folder and self.animation_frames:
            self.load_animation(self.animation_folder)