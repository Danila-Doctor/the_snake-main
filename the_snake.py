import pygame
from random import randint


# <!-- Яндекс — найдётся всё. Может даже ляпы в коде. -->

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Colors
BOARD_BACKGROUND_COLOR = (255, 255, 255)  # White background
TEXT_COLOR = (0, 0, 0)                    # Black text
APPLE_COLOR = (255, 0, 0)                 # Red "Я"
ERROR_COLOR = (255, 0, 0)                 # Error message color
HINT_COLOR = (0, 128, 0)                  # Hint color

# Default speed
BASE_SPEED = 14
ADMIN_SPEED = 30

# Apple Sizes
NORMAL_APPLE_SIZE = GRID_SIZE
ADMIN_APPLE_SIZE = GRID_SIZE * 4  # 4x size in admin mode

# Initialize PyGame
pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Змейка | Яндекс')
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont('timesnewroman', 18, bold=True)
big_font = pygame.font.SysFont('timesnewroman', 36, bold=True)


def create_sound(frequency, duration=0.1):
    """Generate a simple square wave sound without numpy."""
    sample_rate = 22050
    frames = int(sample_rate * duration)
    arr = bytearray()
    for i in range(frames):
        phase = i * frequency / sample_rate
        wave = int(32767 * 0.3 * (phase - int(phase)))
        sample = min(wave, 32767)
        arr += sample.to_bytes(2, 'little', signed=True)
    return pygame.mixer.Sound(buffer=arr)


# Create sounds
eat_sound = create_sound(800, 0.1)
crash_sound = create_sound(200, 0.3)
error_sound = create_sound(400, 0.15)
correct_sound = create_sound(600, 0.1)


class GameObject:
    """Base class for all game objects."""

    def __init__(self, position=None, body_color=None):
        self.position = position
        self.body_color = body_color

    def draw(self):
        """Draw the object. Must be implemented in subclass."""
        raise NotImplementedError("Subclasses must implement draw()")


class Apple(GameObject):
    """Red 'Я' apple. Can be large in admin mode."""

    def __init__(self, snake_positions=None, is_admin=False):
        super().__init__(body_color=APPLE_COLOR)
        self.is_admin = is_admin
        self.size = ADMIN_APPLE_SIZE if is_admin else NORMAL_APPLE_SIZE
        self.randomize_position(snake_positions or [])

    def randomize_position(self, snake_positions):
        """Set a new random position not overlapping with the snake."""
        while True:
            max_x = (SCREEN_WIDTH // GRID_SIZE) - (self.size // GRID_SIZE)
            max_y = (SCREEN_HEIGHT // GRID_SIZE) - (self.size // GRID_SIZE)
            x = randint(0, max_x - 1) * GRID_SIZE
            y = randint(0, max_y - 1) * GRID_SIZE
            self.position = (x, y)
            if self.position not in snake_positions:
                break

    def draw(self):
        """Render the apple as the letter 'Я'."""
        x, y = self.position
        size = 36 if self.is_admin else 18
        apple_font = pygame.font.SysFont('timesnewroman', size, bold=True)
        text_surface = apple_font.render("Я", True, APPLE_COLOR)
        text_rect = text_surface.get_rect(
            center=(x + self.size // 2, y + self.size // 2),
        )
        screen.blit(text_surface, text_rect)


class Snake(GameObject):
    """Snake that spells 'индекс', then '_→яндес→_→яндекс...'."""

    def __init__(self):
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        super().__init__((center_x, center_y), TEXT_COLOR)
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None
        self.base_word = "ндекс"
        self.full_word = "яндекс"
        self.full_word_colors = [
            (255, 0, 0),  # "я" — red
            (0, 0, 0),    # "н"
            (0, 0, 0),    # "д"
            (0, 0, 0),    # "е"
            (0, 0, 0),    # "к"
            (0, 0, 0),     # "с"
        ]

    def get_head_position(self):
        """Return the head position."""
        return self.positions[0]

    def update_direction(self):
        """Update direction from next_direction."""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

    def move(self):
        """Move the snake, with wrap-around."""
        head_x, head_y = self.get_head_position()
        dx, dy = self.direction
        new_head = (
            (head_x + dx * GRID_SIZE) % SCREEN_WIDTH,
            (head_y + dy * GRID_SIZE) % SCREEN_HEIGHT,
        )
        self.positions.insert(0, new_head)
        if len(self.positions) > self.length:
            self.positions.pop()

    def grow(self):
        """Increase snake length."""
        self.length += 1

    def check_collision(self, ignore_self=False):
        """Check if head collides with body."""
        head = self.get_head_position()
        return not ignore_self and head in self.positions[1:]

    def reset(self):
        """Reset snake to initial state."""
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        self.positions = [(center_x, center_y)]
        self.length = 1
        self.direction = RIGHT
        self.next_direction = None

    def draw(self):
        """Draw each segment of the snake."""
        for i, pos in enumerate(self.positions):
            x, y = pos
            if i < len(self.base_word):
                letter = self.base_word[i]
                color = TEXT_COLOR
            elif (i - 5) % 7 == 0:
                letter = "_"
                color = TEXT_COLOR
            else:
                offset = i - 6
                word_idx = offset % len(self.full_word)
                letter = self.full_word[word_idx]
                color = self.full_word_colors[word_idx]
            text_surface = font.render(letter, True, color)
            text_rect = text_surface.get_rect(
                center=(x + GRID_SIZE // 2, y + GRID_SIZE // 2),
            )
            screen.blit(text_surface, text_rect)


def handle_keys(snake):
    """Process keyboard input."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and snake.direction != DOWN:
                snake.next_direction = UP
            elif event.key == pygame.K_DOWN and snake.direction != UP:
                snake.next_direction = DOWN
            elif event.key == pygame.K_LEFT and snake.direction != RIGHT:
                snake.next_direction = LEFT
            elif event.key == pygame.K_RIGHT and snake.direction != LEFT:
                snake.next_direction = RIGHT


def show_game_over(score):
    """Display game over screen."""
    screen.fill(BOARD_BACKGROUND_COLOR)
    game_over_text = big_font.render("Игра окончена!", True, (255, 0, 0))
    score_text = font.render(f"Очки: {score}", True, TEXT_COLOR)
    restart_text = font.render("R — Рестарт | Q — Выход", True, TEXT_COLOR)
    hint_text = font.render(
        "Подсказка: введите 'Admin' в ответ на первый вопрос",
        True, (0, 0, 255),
    )

    screen.blit(game_over_text, (
        SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
        SCREEN_HEIGHT // 2 - 60,
    ))
    screen.blit(score_text, (
        SCREEN_WIDTH // 2 - score_text.get_width() // 2,
        SCREEN_HEIGHT // 2,
    ))
    screen.blit(restart_text, (
        SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
        SCREEN_HEIGHT // 2 + 40,
    ))
    screen.blit(hint_text, (
        SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
        SCREEN_HEIGHT - 50,
    ))

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                key_char = event.unicode.lower()
                if event.key == pygame.K_r or key_char == 'к':
                    waiting = False
                    return True
                if event.key == pygame.K_q or key_char == 'й':
                    pygame.quit()
                    raise SystemExit


def ask_question(question, correct_answer):
    """Display a question with a flying 'Я' and text input."""
    input_text = ""
    error_count = 0
    font_normal = font
    font_small = pygame.font.SysFont('timesnewroman', 16)

    # Flying "Я"
    y_font = pygame.font.SysFont('timesnewroman', 36, bold=True)
    y_surface = y_font.render("Я", True, (255, 0, 0))
    y_pos = [randint(50, SCREEN_WIDTH - 50), randint(50, SCREEN_HEIGHT - 50)]
    y_speed = [randint(-3, 3), randint(-3, 3)]
    while y_speed == [0, 0]:
        y_speed = [randint(-3, 3), randint(-3, 3)]

    while True:
        y_pos[0] += y_speed[0]
        y_pos[1] += y_speed[1]

        if y_pos[0] <= 0 or y_pos[0] >= SCREEN_WIDTH - 30:
            y_speed[0] *= -1
        if y_pos[1] <= 0 or y_pos[1] >= SCREEN_HEIGHT - 30:
            y_speed[1] *= -1

        screen.fill(BOARD_BACKGROUND_COLOR)
        screen.blit(y_surface, (y_pos[0], y_pos[1]))

        question_surf = font_normal.render(question, True, TEXT_COLOR)
        screen.blit(question_surf, (
            SCREEN_WIDTH // 2 - question_surf.get_width() // 2,
            SCREEN_HEIGHT // 2 - 60,
        ))

        input_surf = font_normal.render(f"> {input_text}_", True, TEXT_COLOR)
        screen.blit(input_surf, (
            SCREEN_WIDTH // 2 - input_surf.get_width() // 2,
            SCREEN_HEIGHT // 2 - 10,
        ))

        if error_count > 0:
            error_surf = font_small.render(
                "Ответ неверный", True, ERROR_COLOR,
            )
            screen.blit(error_surf, (
                SCREEN_WIDTH // 2 - error_surf.get_width() // 2,
                SCREEN_HEIGHT // 2 + 30,
            ))

        if error_count >= 3:
            hint_surf = font_small.render(
                f"Правильный ответ: {correct_answer}",
                True, HINT_COLOR,
            )
            screen.blit(hint_surf, (
                SCREEN_WIDTH // 2 - hint_surf.get_width() // 2,
                SCREEN_HEIGHT // 2 + 60,
            ))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    user_input = input_text.strip()
                    if user_input.lower() == "admin":
                        correct_sound.play()
                        return True, "admin"
                    if user_input == correct_answer:
                        correct_sound.play()
                        return True, user_input
                    error_sound.play()
                    error_count += 1
                    input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isprintable() and len(input_text) < 20:
                    input_text += event.unicode

        clock.tick(60)


def show_intro():
    """Ask first question. Skip second if 'admin'."""
    _, answer = ask_question("Сколько лет Яндексу в 2026 году?", "28")
    if answer.lower() == "admin":
        return "admin"
    ask_question("Чему равно число π? (4 знака после запятой)", "3,1416")
    return "normal"


def main():
    """Main game loop."""
    mode = show_intro()
    is_admin = mode == "admin"
    speed = ADMIN_SPEED if is_admin else BASE_SPEED

    snake = Snake()
    apple = Apple(snake.positions, is_admin=is_admin)
    score = 0
    running = True
    effect_levels = {50, 100, 200, 300}
    last_effect_triggered = set()

    while running:
        clock.tick(speed)
        handle_keys(snake)
        snake.update_direction()
        snake.move()

        # Collision only in normal mode
        if not is_admin and snake.check_collision():
            crash_sound.play()
            screen.fill((255, 0, 0))
            pygame.display.update()
            pygame.time.delay(200)
            if show_game_over(score):
                snake.reset()
                apple = Apple(snake.positions, is_admin=is_admin)
                score = 0
                last_effect_triggered.clear()

        # Check for apple collision
        head_pos = snake.get_head_position()
        apple_rect = pygame.Rect(apple.position, (apple.size, apple.size))
        if apple_rect.collidepoint(head_pos):
            snake.grow()
            apple.randomize_position(snake.positions)
            score += 10
            eat_sound.play()

            if score in effect_levels and score not in last_effect_triggered:
                last_effect_triggered.add(score)
                screen.fill(BOARD_BACKGROUND_COLOR)
                apple.draw()
                for pos in snake.positions:
                    rect = pygame.Rect(pos[0], pos[1], GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(screen, (255, 0, 0), rect)
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)
                pygame.display.update()
                pygame.time.delay(200)

        screen.fill(BOARD_BACKGROUND_COLOR)
        score_text = font.render(f"Очки: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (10, 10))
        snake.draw()
        apple.draw()
        pygame.display.update()


if __name__ == '__main__':
    main()
    