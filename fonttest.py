import pygame

pygame.init()
screen = pygame.display.set_mode((400, 200))

# Replace with your font path
font_path = "assets/font/PressStart2P-Regular.ttf"
font = pygame.font.Font(font_path, 32)

# Latin phrase: "The game begins"
text_surface = font.render("LŪDUS INCIPIT", True, (255, 255, 255))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit()

    screen.fill((0, 0, 0))
    screen.blit(text_surface, (50, 80))
    pygame.display.flip()