import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

# Difficulty settings
DIFFICULTY_SETTINGS = {
    'Easy': {'speed': 8, 'score_multiplier': 1},
    'Medium': {'speed': 12, 'score_multiplier': 1.5},
    'Hard': {'speed': 18, 'score_multiplier': 2},
    'Expert': {'speed': 25, 'score_multiplier': 3}
}

class SoundManager:
    def __init__(self):
        self.sounds = {}
        # Create simple sound effects using numpy arrays
        self.create_sounds()
    
    def create_sounds(self):
        try:
            import numpy as np
            # Create eat sound (simple beep)
            self.sounds['eat'] = self.create_beep(440, 0.1)  # A4 note
            # Create collision sound (lower tone)
            self.sounds['collision'] = self.create_beep(220, 0.3)  # A3 note
            # Create menu sound
            self.sounds['menu'] = self.create_beep(660, 0.1)  # E5 note
        except ImportError:
            # If numpy is not available, use empty sounds
            print("NumPy not available - running without sound effects")
            self.sounds = {'eat': None, 'collision': None, 'menu': None}
    
    def create_beep(self, frequency, duration):
        try:
            import numpy as np
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
            arr = (arr * 32767).astype(np.int16)
            # Create stereo sound
            stereo_arr = np.array([arr, arr]).T
            sound = pygame.sndarray.make_sound(stereo_arr)
            return sound
        except:
            return None
    
    def play(self, sound_name):
        if sound_name in self.sounds and self.sounds[sound_name] is not None:
            self.sounds[sound_name].play()

class Snake:
    def __init__(self):
        self.reset()
        self.move_timer = 0
        self.move_delay = 100  # milliseconds between moves
    
    def reset(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)  # Moving right initially
        self.grow = False
        self.smooth_offset = [0, 0]  # For smooth movement animation
    
    def move(self, dt):
        self.move_timer += dt
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            
            # Move snake
            head_x, head_y = self.body[0]
            new_head = (head_x + self.direction[0], head_y + self.direction[1])
            self.body.insert(0, new_head)
            
            if not self.grow:
                self.body.pop()
            else:
                self.grow = False
    
    def change_direction(self, new_direction):
        # Prevent moving into itself
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction
    
    def check_collision(self):
        head_x, head_y = self.body[0]
        
        # Wall collision
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            return True
        
        # Self collision
        if (head_x, head_y) in self.body[1:]:
            return True
        
        return False
    
    def eat_apple(self):
        self.grow = True
    
    def set_speed(self, speed):
        self.move_delay = max(50, 200 - speed * 5)
    
    def draw(self, screen):
        for i, (x, y) in enumerate(self.body):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if i == 0:  # Head
                pygame.draw.rect(screen, DARK_GREEN, rect)
                pygame.draw.rect(screen, WHITE, rect, 2)
                # Draw eyes
                eye_size = 3
                left_eye = (x * GRID_SIZE + 5, y * GRID_SIZE + 5)
                right_eye = (x * GRID_SIZE + GRID_SIZE - 8, y * GRID_SIZE + 5)
                pygame.draw.circle(screen, WHITE, left_eye, eye_size)
                pygame.draw.circle(screen, WHITE, right_eye, eye_size)
            else:  # Body
                pygame.draw.rect(screen, GREEN, rect)
                pygame.draw.rect(screen, DARK_GREEN, rect, 1)

class Apple:
    def __init__(self):
        self.position = self.generate_position()
    
    def generate_position(self):
        return (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    
    def respawn(self, snake_body):
        while True:
            new_pos = self.generate_position()
            if new_pos not in snake_body:
                self.position = new_pos
                break
    
    def draw(self, screen):
        x, y = self.position
        center_x = x * GRID_SIZE + GRID_SIZE // 2
        center_y = y * GRID_SIZE + GRID_SIZE // 2
        radius = GRID_SIZE // 2 - 2
        
        # Draw apple as a circle with a stem
        pygame.draw.circle(screen, RED, (center_x, center_y), radius)
        pygame.draw.circle(screen, DARK_GREEN, (center_x, center_y - radius + 2), 3)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Enhanced Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        
        # Animation variables
        self.menu_time = 0
        self.title_pulse = 0
        self.snake_demo_segments = []
        self.demo_apple_pos = (10, 5)
        self.init_demo_snake()
        
        self.sound_manager = SoundManager()
        self.snake = Snake()
        self.apple = Apple()
        
        self.score = 0
        self.high_score = 0
        self.difficulty = 'Medium'
        self.game_state = 'MENU'  # MENU, PLAYING, PAUSED, GAME_OVER, DIFFICULTY_SELECT
        
        # For difficulty selection navigation
        self.difficulty_options = ['Easy', 'Medium', 'Hard', 'Expert']
        self.selected_difficulty_index = self.difficulty_options.index(self.difficulty)
        
        # For main menu navigation
        self.menu_options = ['START_GAME', 'SETTINGS', 'QUIT']
        self.selected_menu_index = 0
        
        self.snake.set_speed(DIFFICULTY_SETTINGS[self.difficulty]['speed'])
    
    def init_demo_snake(self):
        """Initialize the animated demo snake for the menu"""
        self.snake_demo_segments = [
            (5, 8), (4, 8), (3, 8), (2, 8)
        ]
        self.demo_direction = (1, 0)
        self.demo_move_timer = 0
    
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_clicked = True

            elif event.type == pygame.KEYDOWN:
                if self.game_state == 'MENU':
                    if event.key == pygame.K_UP:
                        self.selected_menu_index = (self.selected_menu_index - 1) % len(self.menu_options)
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_DOWN:
                        self.selected_menu_index = (self.selected_menu_index + 1) % len(self.menu_options)
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_RETURN:
                        if not self.handle_menu_selection():
                            return False
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_d:
                        self.game_state = 'DIFFICULTY_SELECT'
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_q:
                        return False

                elif self.game_state == 'DIFFICULTY_SELECT':
                    if event.key == pygame.K_UP:
                        self.selected_difficulty_index = (self.selected_difficulty_index - 1) % len(self.difficulty_options)
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_DOWN:
                        self.selected_difficulty_index = (self.selected_difficulty_index + 1) % len(self.difficulty_options)
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_RETURN:
                        self.difficulty = self.difficulty_options[self.selected_difficulty_index]
                        self.game_state = 'MENU'
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_1:
                        self.difficulty = 'Easy'
                        self.selected_difficulty_index = 0
                        self.game_state = 'MENU'
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_2:
                        self.difficulty = 'Medium'
                        self.selected_difficulty_index = 1
                        self.game_state = 'MENU'
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_3:
                        self.difficulty = 'Hard'
                        self.selected_difficulty_index = 2
                        self.game_state = 'MENU'
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_4:
                        self.difficulty = 'Expert'
                        self.selected_difficulty_index = 3
                        self.game_state = 'MENU'
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = 'MENU'

                elif self.game_state == 'PLAYING':
                    if event.key == pygame.K_UP and self.snake.direction != (0, 1):
                        self.snake.change_direction((0, -1))
                    elif event.key == pygame.K_DOWN and self.snake.direction != (0, -1):
                        self.snake.change_direction((0, 1))
                    elif event.key == pygame.K_LEFT and self.snake.direction != (1, 0):
                        self.snake.change_direction((-1, 0))
                    elif event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0):
                        self.snake.change_direction((1, 0))
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = 'PAUSED'

                elif self.game_state == 'PAUSED':
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'PLAYING'
                    elif event.key == pygame.K_q:
                        self.game_state = 'MENU'

                elif self.game_state == 'GAME_OVER':
                    if event.key == pygame.K_RETURN:
                        self.start_game()
                        self.sound_manager.play('menu')
                    elif event.key == pygame.K_q:
                        self.game_state = 'MENU'

        # Handle mouse clicks on menu buttons
        if self.game_state == 'MENU' and mouse_clicked:
            self.handle_menu_mouse_click(mouse_pos)

        return True
    
    def handle_menu_selection(self):
        """Handle menu selection via keyboard or mouse"""
        if self.selected_menu_index == 0:  # START GAME
            self.start_game()
        elif self.selected_menu_index == 1:  # SETTINGS
            self.game_state = 'DIFFICULTY_SELECT'
        elif self.selected_menu_index == 2:  # QUIT
            return False
        return True
    
    def handle_menu_mouse_click(self, mouse_pos):
        """Handle mouse clicks on menu buttons"""
        button_width = 280
        button_height = 50
        button_spacing = 20
        start_y = 320
        
        for i in range(len(self.menu_options)):
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(
                WINDOW_WIDTH // 2 - button_width // 2, 
                button_y, 
                button_width, 
                button_height
            )
            
            if button_rect.collidepoint(mouse_pos):
                self.selected_menu_index = i
                self.sound_manager.play('menu')
                if not self.handle_menu_selection():
                    return False
                break
                
    def start_game(self):
        self.snake.reset()
        self.apple.respawn(self.snake.body)
        self.score = 0
        self.snake.set_speed(DIFFICULTY_SETTINGS[self.difficulty]['speed'])
        self.game_state = 'PLAYING'
    
    def update(self, dt):
        # Update animations
        self.menu_time += dt
        self.title_pulse = math.sin(self.menu_time * 0.003) * 20 + 72
        
        # Update demo snake animation
        if self.game_state == 'MENU':
            self.update_demo_snake(dt)
        
        if self.game_state == 'PLAYING':
            self.snake.move(dt)
            
            # Check apple collision
            if self.snake.body[0] == self.apple.position:
                self.snake.eat_apple()
                self.apple.respawn(self.snake.body)
                self.score += int(10 * DIFFICULTY_SETTINGS[self.difficulty]['score_multiplier'])
                self.sound_manager.play('eat')
            
            # Check collisions
            if self.snake.check_collision():
                self.game_state = 'GAME_OVER'
                self.high_score = max(self.high_score, self.score)
                self.sound_manager.play('collision')
    
    def update_demo_snake(self, dt):
        """Update the animated demo snake"""
        self.demo_move_timer += dt
        if self.demo_move_timer >= 300:  # Move every 300ms
            self.demo_move_timer = 0
            
            # Move snake head
            head_x, head_y = self.snake_demo_segments[0]
            new_head = (head_x + self.demo_direction[0], head_y + self.demo_direction[1])
            
            # Boundary checking and direction changing
            if new_head[0] >= 25 or new_head[0] < 2 or new_head[1] >= 15 or new_head[1] < 5:
                # Change direction randomly at boundaries
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                self.demo_direction = random.choice(directions)
                new_head = (head_x + self.demo_direction[0], head_y + self.demo_direction[1])
            
            # Check if eating demo apple
            if new_head == self.demo_apple_pos:
                self.snake_demo_segments.insert(0, new_head)
                # Respawn demo apple
                self.demo_apple_pos = (random.randint(2, 24), random.randint(5, 14))
            else:
                self.snake_demo_segments.insert(0, new_head)
                if len(self.snake_demo_segments) > 6:  # Keep demo snake short
                    self.snake_demo_segments.pop()
    
    def draw_grid(self):
        # Draw a subtle grid pattern
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (WINDOW_WIDTH, y), 1)
    
    def draw_menu(self):
        # Create animated gradient background
        self.draw_animated_background()
        
        # Draw animated title with pulsing effect
        title_size = int(self.title_pulse)
        title_font = pygame.font.Font(None, title_size)
        title = title_font.render("SNAKE", True, GREEN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 120))
        
        # Add glow effect to title
        glow_title = title_font.render("SNAKE", True, (0, 100, 0))
        glow_rect = glow_title.get_rect(center=(WINDOW_WIDTH // 2 + 2, 122))
        self.screen.blit(glow_title, glow_rect)
        self.screen.blit(title, title_rect)
        
        # Draw animated demo snake
        self.draw_demo_snake()
        
        # Draw demo apple
        apple_x, apple_y = self.demo_apple_pos
        apple_center_x = apple_x * GRID_SIZE + GRID_SIZE // 2
        apple_center_y = apple_y * GRID_SIZE + GRID_SIZE // 2
        apple_radius = GRID_SIZE // 2 - 2
        pygame.draw.circle(self.screen, RED, (apple_center_x, apple_center_y), apple_radius)
        pygame.draw.circle(self.screen, DARK_GREEN, (apple_center_x, apple_center_y - apple_radius + 2), 3)
        
        # Draw interactive buttons instead of text
        self.draw_menu_buttons()
        
        # Draw stats at bottom
        stats_y = WINDOW_HEIGHT - 80
        difficulty_text = self.small_font.render(f"Difficulty: {self.difficulty}", True, YELLOW)
        score_text = self.small_font.render(f"Best: {self.high_score}", True, WHITE)
        
        self.screen.blit(difficulty_text, (20, stats_y))
        score_rect = score_text.get_rect(topright=(WINDOW_WIDTH - 20, stats_y))
        self.screen.blit(score_text, score_rect)
    
    def draw_animated_background(self):
        """Draw animated starfield background"""
        self.screen.fill(BLACK)
        
        # Draw moving stars
        for i in range(50):
            star_time = (self.menu_time + i * 100) * 0.001
            x = int((star_time * 30 + i * 73) % WINDOW_WIDTH)
            y = int((star_time * 20 + i * 97) % WINDOW_HEIGHT)
            brightness = int(abs(math.sin(star_time + i)) * 100 + 50)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color, (x, y), 1)
    
    def draw_demo_snake(self):
        """Draw the animated demo snake on menu"""
        for i, (x, y) in enumerate(self.snake_demo_segments):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if i == 0:  # Head
                pygame.draw.rect(self.screen, DARK_GREEN, rect)
                pygame.draw.rect(self.screen, WHITE, rect, 2)
                # Draw eyes
                eye_size = 2
                left_eye = (x * GRID_SIZE + 5, y * GRID_SIZE + 5)
                right_eye = (x * GRID_SIZE + GRID_SIZE - 8, y * GRID_SIZE + 5)
                pygame.draw.circle(self.screen, WHITE, left_eye, eye_size)
                pygame.draw.circle(self.screen, WHITE, right_eye, eye_size)
            else:  # Body
                pygame.draw.rect(self.screen, GREEN, rect)
                pygame.draw.rect(self.screen, DARK_GREEN, rect, 1)
    
    def draw_menu_buttons(self):
        """Draw the menu buttons with hover effects"""
        button_labels = ["START GAME", "SETTINGS", "QUIT"]
        button_width = 280
        button_height = 50
        button_spacing = 20
        start_y = 320
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, label in enumerate(button_labels):
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(
                WINDOW_WIDTH // 2 - button_width // 2, 
                button_y, 
                button_width, 
                button_height
            )
            
            # Check if button is selected or hovered
            is_selected = (i == self.selected_menu_index)
            is_hovered = button_rect.collidepoint(mouse_pos)
            
            # Draw button background
            if is_selected or is_hovered:
                pygame.draw.rect(self.screen, DARK_GREEN, button_rect)
                pygame.draw.rect(self.screen, GREEN, button_rect, 3)
                text_color = WHITE
            else:
                pygame.draw.rect(self.screen, (50, 50, 50), button_rect)
                pygame.draw.rect(self.screen, GRAY, button_rect, 2)
                text_color = LIGHT_GRAY
            
            # Draw button text
            text = self.font.render(label, True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
    
    def draw_difficulty_select(self):
        """Draw the difficulty selection screen"""
        self.screen.fill(BLACK)
        
        # Draw title
        title = self.big_font.render("SELECT DIFFICULTY", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Draw difficulty options
        start_y = 200
        option_height = 60
        
        for i, difficulty in enumerate(self.difficulty_options):
            y = start_y + i * option_height
            
            # Highlight selected option
            if i == self.selected_difficulty_index:
                highlight_rect = pygame.Rect(100, y - 10, WINDOW_WIDTH - 200, 50)
                pygame.draw.rect(self.screen, DARK_GREEN, highlight_rect)
                pygame.draw.rect(self.screen, GREEN, highlight_rect, 3)
                text_color = WHITE
            else:
                text_color = LIGHT_GRAY
            
            # Draw difficulty name
            diff_text = self.font.render(f"{i+1}. {difficulty}", True, text_color)
            self.screen.blit(diff_text, (150, y))
            
            # Draw difficulty stats
            settings = DIFFICULTY_SETTINGS[difficulty]
            stats_text = self.small_font.render(
                f"Speed: {settings['speed']}, Score Multiplier: {settings['score_multiplier']}x", 
                True, text_color
            )
            self.screen.blit(stats_text, (300, y + 5))
        
        # Draw instructions
        instructions = [
            "Use UP/DOWN arrows or number keys to select",
            "Press ENTER to confirm, ESC to go back"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, YELLOW)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80 + i * 25))
            self.screen.blit(text, text_rect)
    
    def draw_paused(self):
        """Draw the paused screen"""
        # Draw the game in background (dimmed)
        self.screen.fill(BLACK)
        self.draw_grid()
        
        # Dim the background
        dim_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        dim_surface.fill(BLACK)
        dim_surface.set_alpha(128)
        
        # Draw snake and apple dimmed
        self.snake.draw(self.screen)
        self.apple.draw(self.screen)
        self.screen.blit(dim_surface, (0, 0))
        
        # Draw pause menu
        pause_title = self.big_font.render("PAUSED", True, WHITE)
        title_rect = pause_title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(pause_title, title_rect)
        
        instructions = [
            "Press ESC to resume",
            "Press Q to quit to menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, YELLOW)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20 + i * 40))
            self.screen.blit(text, text_rect)
        
        # Draw current score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
    
    def draw_game_over(self):
        """Draw the game over screen"""
        self.screen.fill(BLACK)
        
        # Draw game over title
        game_over_title = self.big_font.render("GAME OVER", True, RED)
        title_rect = game_over_title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(game_over_title, title_rect)
        
        # Draw scores
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
        self.screen.blit(score_text, score_rect)
        
        if self.score == self.high_score:
            new_high_text = self.font.render("NEW HIGH SCORE!", True, YELLOW)
            new_high_rect = new_high_text.get_rect(center=(WINDOW_WIDTH // 2, 260))
            self.screen.blit(new_high_text, new_high_rect)
        else:
            high_score_text = self.font.render(f"Best Score: {self.high_score}", True, YELLOW)
            high_score_rect = high_score_text.get_rect(center=(WINDOW_WIDTH // 2, 260))
            self.screen.blit(high_score_text, high_score_rect)
        
        # Draw snake length
        snake_length = len(self.snake.body)
        length_text = self.font.render(f"Snake Length: {snake_length}", True, GREEN)
        length_rect = length_text.get_rect(center=(WINDOW_WIDTH // 2, 300))
        self.screen.blit(length_text, length_rect)
        
        # Draw difficulty
        diff_text = self.font.render(f"Difficulty: {self.difficulty}", True, BLUE)
        diff_rect = diff_text.get_rect(center=(WINDOW_WIDTH // 2, 340))
        self.screen.blit(diff_text, diff_rect)
        
        # Draw instructions
        instructions = [
            "Press ENTER to play again",
            "Press Q to return to menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, LIGHT_GRAY)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 420 + i * 40))
            self.screen.blit(text, text_rect)
    
    def draw_playing(self):
        """Draw the main game screen"""
        self.screen.fill(BLACK)
        self.draw_grid()
        self.snake.draw(self.screen)
        self.apple.draw(self.screen)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        high_score_text = self.small_font.render(f"Best: {self.high_score}", True, YELLOW)
        self.screen.blit(high_score_text, (10, 50))
        
        difficulty_text = self.small_font.render(f"Difficulty: {self.difficulty}", True, BLUE)
        diff_rect = difficulty_text.get_rect(topright=(WINDOW_WIDTH - 10, 10))
        self.screen.blit(difficulty_text, diff_rect)
        
        length_text = self.small_font.render(f"Length: {len(self.snake.body)}", True, GREEN)
        length_rect = length_text.get_rect(topright=(WINDOW_WIDTH - 10, 40))
        self.screen.blit(length_text, length_rect)



    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)  # Limit to 60 FPS and get delta time in milliseconds
            running = self.handle_events()
            self.update(dt)

            if self.game_state == 'MENU':
                self.draw_menu()
            elif self.game_state == 'DIFFICULTY_SELECT':
                self.draw_difficulty_select()
            elif self.game_state == 'PLAYING':
                self.draw_playing()
            elif self.game_state == 'PAUSED':
                self.draw_paused()
            elif self.game_state == 'GAME_OVER':
                self.draw_game_over()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
