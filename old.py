import pygame
import random
import math
from pygame import mixer
import os, sys

APP_FOLDER = os.path.dirname(os.path.realpath(sys.argv[0]))
full_path_bgm = os.path.join(APP_FOLDER, "background_music.wav")
full_path_bsi = os.path.join(APP_FOLDER, "BasicSpaceInvader.png")
full_path_battleship = os.path.join(APP_FOLDER, "battleship.png")
full_path_earth = os.path.join(APP_FOLDER, "Earth-800x600.png")
full_path_missle = os.path.join(APP_FOLDER, "missile_sprite.png")
full_path_space_ship = os.path.join(APP_FOLDER, "Space Ship.png")
full_path_explosion_se = os.path.join(APP_FOLDER, "explosion.wav")
full_path_firing_se = os.path.join(APP_FOLDER, "firing_sound.wav")

pygame.init() # initalize the pygame
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800, 600)) # create screen

background = pygame.image.load(full_path_earth)
pygame.display.set_caption("Space Invaders") # name window
icon = pygame.image.load(full_path_battleship) # load window icon
pygame.display.set_icon(icon) # set window icon






# Music Funcitonality
mixer.music.load(full_path_bgm)
mixer.music.play(-1)


# Player
playerImg = pygame.image.load(full_path_space_ship)
playerX = 370
playerY = 480
playerX_change = 0

# Enemies
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 6

for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load(full_path_bsi))
    enemyX.append(random.randint(0, 735))
    enemyY.append(random.randint(50, 150))
    enemyX_change.append(4)
    enemyY_change.append(40)
    # print("made enemy" + str(i))

# bullet    
bulletImg = pygame.image.load(full_path_missle)
bulletX = 0
bulletY = 480
bulletX_change = 0
bulletY_change = 10
bullet_state = "ready"

#score
score_value = 0
font = pygame.font.Font("freesansbold.ttf", 32)
textX = 10
textY = 10

game_over_font = pygame.font.Font("freesansbold.ttf", 64)

def game_over_text():
    game_over_text = game_over_font.render("GAME OVER", True, (255,255,255))
    screen.blit(game_over_text, (200,250))

def show_score(x,y): 
    score = font.render("Score : " + str(score_value), True, (255,255,255))
    screen.blit(score, (x,y))

def player(x,y):
    screen.blit(playerImg, (x, y))

def enemy(x,y, i):
    screen.blit(enemyImg[i], (x, y))


def fire_bullet(x,y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg, (x+16,y+10))

def isCollision(enemyX,enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX-bulletX,2) + math.pow(enemyY-bulletY, 2)) # math to find distance with two points
    if distance < 27:
        return True
    else:
        return False


# Game Loop
running = True
while running:
    screen.fill((0,0,0)) # Blank the screen out
    screen.blit(background,(0,0))
    for event in pygame.event.get(): # for every event happening
        if event.type == pygame.QUIT: # if it's the quit event
            running = False # then leave the while loop
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -5
            if event.key == pygame.K_RIGHT:
                playerX_change = 5
            if event.key == pygame.K_SPACE:
                if bullet_state == "ready":
                    bulletX = playerX
                    fire_bullet(bulletX,bulletY)
                    bullet_Sound = mixer.Sound(full_path_firing_se)
                    bullet_Sound.play()
        if event.type == pygame.KEYUP:
            if event.key == pygame .K_LEFT or event.key == pygame .K_RIGHT:
                playerX_change = 0


    
    playerX += playerX_change

    if playerX < 0:
        playerX = 0
        
    elif playerX >=736:
        playerX = 736
        
    for i in range(num_of_enemies):

        #  Game over
        if enemyY[i] > 430:
            for j in range(num_of_enemies):
                enemyY[j] = 2000
            game_over_text()
            break



        enemyX[i] += enemyX_change[i]
        if enemyX[i] < 0:
            enemyX_change[i] = 4
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >=768:
            enemyX_change[i] = -4
            enemyY[i] += enemyY_change[i]

        # Collision
        collision = isCollision(enemyX[i], enemyY[i], bulletX, bulletY)
        if collision:
            explosion_Sound = mixer.Sound(full_path_explosion_se)
            explosion_Sound.play()
            bulletY = 480
            bullet_state = "ready"
            score_value += 1
            enemyX[i] = random.randint(0, 735)
            enemyY[i] = random.randint(50, 150)

        enemy(enemyX[i], enemyY[i], i)



    #bullet Movement
    if bulletY <= -5 :
        bulletY = 480
        bullet_state = "ready"

    if bullet_state == "fire":
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change 




    player(playerX, playerY)
    show_score(textX, textY)
    pygame.display.update()
    clock.tick(60)