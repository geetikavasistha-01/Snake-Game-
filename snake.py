import pygame
import math
import random
import sys

# CONSTANTS
WIDTH = 640
HEIGHT = 640
PIXELS = 32
SQUARES = int(WIDTH / PIXELS)

# COLORS
BG1 = (156, 210, 54)
BG2 = (147, 203, 57)
RED = (255, 0, 0)
BLUE = (0, 0, 50)
BLACK = (0, 0, 0)


def load_high_score(filename="highscore.txt"):
    try:
        with open(filename, "r") as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(score, filename="highscore.txt"):
    with open(filename, "w") as f:
        f.write(str(score))


class Snake:
    def __init__(self):
        self.color = BLUE
        self.headX = random.randrange(0, WIDTH, PIXELS)
        self.headY = random.randrange(0, HEIGHT, PIXELS)
        self.bodies = []
        self.body_color = 50
        self.state = "STOP"  # STOP, UP, DOWN, RIGHT, LEFT

    def move_head(self):
        if self.state == "UP":
            self.headY -= PIXELS
        elif self.state == "DOWN":
            self.headY += PIXELS
        elif self.state == "RIGHT":
            self.headX += PIXELS
        elif self.state == "LEFT":
            self.headX -= PIXELS

    def move_body(self):
        if len(self.bodies) > 0:
            for i in range(len(self.bodies) - 1, -1, -1):
                if i == 0:
                    self.bodies[0].posX = self.headX
                    self.bodies[0].posY = self.headY
                else:
                    self.bodies[i].posX = self.bodies[i - 1].posX
                    self.bodies[i].posY = self.bodies[i - 1].posY

    def add_body(self):
        self.body_color += 10
        body = Body((0, 0, self.body_color), self.headX, self.headY)
        self.bodies.append(body)

    def draw(self, surface):
        # Draw snake head with rounded corners
        pygame.draw.rect(surface, self.color,
                         (self.headX, self.headY, PIXELS, PIXELS), border_radius=7)

        # Draw simple eyes on the snake's head
        eye_radius = PIXELS // 8
        eye_x_offset = PIXELS // 4
        eye_y_offset = PIXELS // 4

        # Left eye
        pygame.draw.circle(surface, (255, 255, 255),
                           (self.headX + eye_x_offset, self.headY + eye_y_offset), eye_radius)
        pygame.draw.circle(surface, (0, 0, 0),
                           (self.headX + eye_x_offset, self.headY + eye_y_offset), eye_radius // 2)

        # Right eye
        pygame.draw.circle(surface, (255, 255, 255),
                           (self.headX + PIXELS - eye_x_offset, self.headY + eye_y_offset), eye_radius)
        pygame.draw.circle(surface, (0, 0, 0),
                           (self.headX + PIXELS - eye_x_offset, self.headY + eye_y_offset), eye_radius // 2)

        # Draw snake body with rounded corners
        if len(self.bodies) > 0:
            for body in self.bodies:
                pygame.draw.rect(surface, body.color,
                                 (body.posX, body.posY, PIXELS, PIXELS), border_radius=7)

    def die(self):
        self.headX = random.randrange(0, WIDTH, PIXELS)
        self.headY = random.randrange(0, HEIGHT, PIXELS)
        self.bodies = []
        self.body_color = 50
        self.state = "STOP"


class Body:
    def __init__(self, color, posX, posY):
        self.color = color
        self.posX = posX
        self.posY = posY


class Apple:
    def __init__(self):
        self.color = RED
        self.spawn()

    def spawn(self):
        self.posX = random.randrange(0, WIDTH, PIXELS)
        self.posY = random.randrange(0, HEIGHT, PIXELS)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color,
                         (self.posX, self.posY, PIXELS, PIXELS))


class Background:
    def draw(self, surface):
        surface.fill(BG1)
        counter = 0
        for row in range(SQUARES):
            for col in range(SQUARES):
                if counter % 2 == 0:
                    pygame.draw.rect(
                        surface, BG2, (col * PIXELS, row * PIXELS, PIXELS, PIXELS))
                if col != SQUARES - 1:
                    counter += 1


class Collision:
    def between_snake_and_apple(self, snake, apple):
        distance = math.sqrt(math.pow((snake.headX - apple.posX), 2) +
                             math.pow((snake.headY - apple.posY), 2))
        return distance < PIXELS

    def between_snake_and_walls(self, snake):
        if snake.headX < 0 or snake.headX > WIDTH - PIXELS or snake.headY < 0 or snake.headY > HEIGHT - PIXELS:
            return True
        return False

    def between_head_and_body(self, snake):
        for body in snake.bodies:
            distance = math.sqrt(math.pow((snake.headX - body.posX), 2) +
                                 math.pow((snake.headY - body.posY), 2))
            if distance < PIXELS:
                return True
        return False


class Score:
    def __init__(self):
        self.points = 0
        self.font = pygame.font.SysFont('monospace', 30, bold=False)

    def increase(self):
        self.points += 1

    def reset(self):
        self.points = 0

    def show(self, surface, high_score):
        lbl = self.font.render('Score: ' + str(self.points), 1, BLACK)
        surface.blit(lbl, (5, 5))
        hs_lbl = self.font.render('High Score: ' + str(high_score), 1, BLACK)
        surface.blit(hs_lbl, (5, 35))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SNAKE")

    # OBJECTS
    snake = Snake()
    apple = Apple()
    background = Background()
    collision = Collision()
    score = Score()

    high_score = load_high_score()

    while True:
        background.draw(screen)
        snake.draw(screen)
        apple.draw(screen)
        score.show(screen, high_score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_high_score(high_score)
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if snake.state != "DOWN":
                        snake.state = "UP"
                if event.key == pygame.K_DOWN:
                    if snake.state != "UP":
                        snake.state = "DOWN"
                if event.key == pygame.K_RIGHT:
                    if snake.state != "LEFT":
                        snake.state = "RIGHT"
                if event.key == pygame.K_LEFT:
                    if snake.state != "RIGHT":
                        snake.state = "LEFT"
                if event.key == pygame.K_p:
                    snake.state = "STOP"

        if collision.between_snake_and_apple(snake, apple):
            apple.spawn()
            snake.add_body()
            score.increase()

            # Check for new high score
            if score.points > high_score:
                high_score = score.points
                save_high_score(high_score)

        # movement
        if snake.state != "STOP":
            snake.move_body()
            snake.move_head()

        if collision.between_snake_and_walls(snake):
            snake.die()
            apple.spawn()
            score.reset()

        if collision.between_head_and_body(snake):
            snake.die()
            apple.spawn()
            score.reset()

        pygame.time.delay(110)
        pygame.display.update()


if __name__ == "__main__":
    main()
