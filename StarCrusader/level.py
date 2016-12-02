#!/usr/bin/python

#########################################
# File:         level.py
# Author:       Michael / Chris
# Date:         12/09/16
# Class:        Open Source
# Assignment:   Final Project
# Purpose:      Provides basic level
#               functionality
#########################################

import pygame
import random
import math
from asteroid import Asteroid
from spaceship import Spaceship
from spaceship import Camera
from hero import Hero
from pirate import Pirate
from item import Fuel
from ground import Ground
from star_field import *


# Constants
RED = (255, 0, 0)
YELLOW = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

WIDTH = 900
HEIGHT = 900

# Universe
ASTEROID1 = 1
ASTEROID2 = 2
ASTEROID3 = 3
ASTEROID4 = 4
ASTEROID5 = 5
ASTEROID6 = 6
ASTEROID_IMAGE_COUNT = 6

CHUNK_SIZE = 900
CHUNK_HALF_SIZE = 450
RENDER_DISTANCE = 1
COORDS = 0
X_COORD = 0
Y_COORD = 1
ASTEROID_INDEX = 1

# Planet
CENTER_X = 432
CENTER_Y = 1550
PLAYER_SPEED = .0025


class Level:
    """ Parent class of Universe and Planet """
    def __init__(self, player):
        self.background = None
        self.type = None
        self.player = player

    def draw(self, screen):
        #screen.fill(BLACK)
        if self.background:
            screen.blit(self.background, (0,0))

    def get_type(self):
        return self.type


class Planet(Level):
    """ Generate Planet level """
    def __init__(self, screen):
        player = Hero()
        Level.__init__(self, player)
        self.screen = screen
        self.background = pygame.image.load("Sprites/Planet.png").convert_alpha()
        self.planet_angle = 0
        self.time = 0
        self.stars = Star(self.screen)

        # test item creation; create fuel
        self.entity_list = Fuel(700, 700)
        self.ground = Ground(450,698)

    def get_input(self):
        """ Input Function for Planet Level """
        if pygame.key.get_pressed()[pygame.K_a] != 0:
            self.rotate_right(self.entity_list)
            self.player.move(self.time, "L")
        elif pygame.key.get_pressed()[pygame.K_d] != 0:
            self.rotate_left(self.entity_list)
            self.player.move(self.time, "R")
        elif pygame.key.get_pressed()[pygame.K_a] == 0:
            self.player.stop(self.time)
        elif pygame.key.get_pressed()[pygame.K_d] == 0:
            self.player.stop(self.time)

        if pygame.key.get_pressed()[pygame.K_w] != 0 and self.player.center_y:
            self.player.jump()

    def update(self):
        """ Update all entities on the Planet -- TODO: collisions, gravity etc """
        self.time += 1
        self.entity_list.update()
        self.player.update(self.entity_list, self.ground)

    def rotate_right(self, object):
        """ Rotates an entity right around a given sized circle """
        object.rect.x = CENTER_X + (object.center_x - (CENTER_X)) * math.cos(object.angle) - (object.center_y - (CENTER_Y)) * math.sin(object.angle)
        object.rect.y = CENTER_Y + (object.center_x - (CENTER_X)) * math.sin(object.angle) + (object.center_y - (CENTER_Y)) * math.cos(object.angle)
        object.angle += PLAYER_SPEED
        self.planet_angle = object.angle

    def rotate_left(self, object):
        """ Rotates an entity left around a given sized circle """
        object.rect.x = CENTER_X + (object.center_x - (CENTER_X)) * math.cos(object.angle) - (object.center_y - (CENTER_Y)) * math.sin(object.angle)
        object.rect.y = CENTER_Y + (object.center_x - (CENTER_X)) * math.sin(object.angle) + (object.center_y - (CENTER_Y)) * math.cos(object.angle)
        object.angle -= PLAYER_SPEED
        self.planet_angle = object.angle

    def set_dt(self, dt):
        pass

    def render_level(self, fps):
        """ Draw background and all entities on Planet """
        self.stars.draw_stars(self.screen, self.player.move_speed)
        self.draw(self.screen)
        self.screen.blit(self.player.image, self.player.get_pos())
        self.screen.blit(self.entity_list.image, self.entity_list.get_pos())

        """ For Debug """
        if pygame.font:
            font = pygame.font.Font("courbd.ttf", 12)

            cur_f = font.render('F: ' + str(self.player.falling), 1, (255, 255, 255))
            cur_g = font.render('G: ' + str(self.player.on_ground), 1, (255, 255, 255))
            cur_d = font.render('D: ' + str(self.player.direction), 1, (255, 255, 255))
            cur_v = font.render('V: ' + str(self.player.velocity), 1, (255, 255, 255))

            self.screen.blit(cur_f, (5, 835))
            self.screen.blit(cur_g, (5, 850))
            self.screen.blit(cur_d, (5, 865))
            self.screen.blit(cur_v, (5,880))


class Universe(Level):
    "Universe level"
    def __init__(self, screen):
        self.spaceship_group = pygame.sprite.Group()
        self.laser_group = pygame.sprite.Group()
        self.camera = Camera(WIDTH, HEIGHT)
        self.spaceship = Spaceship(self.spaceship_group, self.laser_group)
        self.screen = screen
        Level.__init__(self, self.spaceship)
        self.asteroid_image_set = []
        self.asteroid_damage_set = []
        self.load_asteroid_data()

        self.player_chunk = self.spaceship.player_chunk
        self.current_rendered_chunks = []
        self.player_chunk_coords = [0, 0]
        self.player_coords = [self.spaceship.rect.x, self.spaceship.rect.y]
        self.asteroid_set = []
        self.new_chunk = []

    def get_input(self):
        """ Input Function for Universe Level """
        if pygame.key.get_pressed()[pygame.K_w] != 0:
            self.spaceship.get_event('accelerate')
        if pygame.key.get_pressed()[pygame.K_a] != 0:
            self.spaceship.get_event('rotate_l')
        if pygame.key.get_pressed()[pygame.K_d] != 0:
            self.spaceship.get_event('rotate_r')
        if pygame.key.get_pressed()[pygame.K_SPACE] != 0:
            self.spaceship.shoot_laser()

    def generate_asteroid(self, sprite_group, lower_x, upper_x, lower_y, upper_y):
        random_asteroid = random.randint(0, 5)
        return Asteroid(sprite_group, self.asteroid_image_set[random_asteroid], random.randint(lower_x, upper_x), random.randint(lower_y, upper_y), self.asteroid_damage_set[random_asteroid])

    # TODO: Chunks seem important... lets move to separate module if time permits?
    def generate_chunk(self, chunk_x_coord, chunk_y_coord):
        chunk_already_exists = False
        chunk_sprite_group = pygame.sprite.Group()

        for chunk in self.current_rendered_chunks:
            if (chunk_x_coord, chunk_y_coord) in chunk:
                chunk_already_exists = True

        if not chunk_already_exists:
            for sprite in self.new_chunk:
                self.new_chunk.remove(sprite)

            asteroid_count = random.randint(2, 10)

            for count in range(asteroid_count):
                self.new_chunk.append(self.generate_asteroid(chunk_sprite_group, (chunk_x_coord * CHUNK_SIZE), ((chunk_x_coord * CHUNK_SIZE) + CHUNK_SIZE),
                                           (chunk_y_coord * CHUNK_SIZE), ((chunk_y_coord * CHUNK_SIZE) + CHUNK_SIZE)))

            self.current_rendered_chunks.append(((chunk_x_coord, chunk_y_coord), chunk_sprite_group))

    def player_moved_chunks(self):
        player_moved_chunks = False

        if int(self.player_chunk.centerx % CHUNK_HALF_SIZE <= 30) or int(self.player_chunk.centery % CHUNK_HALF_SIZE <= 30):
            if self.player_coords[X_COORD] not in range(self.player_chunk_coords[X_COORD] * CHUNK_SIZE, (self.player_chunk_coords[X_COORD] * CHUNK_SIZE) + CHUNK_SIZE) or self.player_coords[Y_COORD] not in range(self.player_chunk_coords[Y_COORD] * CHUNK_SIZE, (self.player_chunk_coords[Y_COORD] * CHUNK_SIZE) + CHUNK_SIZE):
                player_moved_chunks = True

        return player_moved_chunks

    def update_current_chunk_coords(self):
        self.player_chunk_coords[X_COORD] = int(self.player_chunk.x / CHUNK_SIZE)
        self.player_chunk_coords[Y_COORD] = int(self.player_chunk.y / CHUNK_SIZE)

    def update_current_player_coords(self):
        self.player_coords[X_COORD] = self.spaceship.rect.x
        self.player_coords[Y_COORD] = self.spaceship.rect.y

    def generate_nearby_chunks(self):
        self.generate_chunk(self.player_chunk_coords[X_COORD], self.player_chunk_coords[Y_COORD])
        self.generate_chunk(self.player_chunk_coords[X_COORD] + RENDER_DISTANCE, self.player_chunk_coords[Y_COORD])
        self.generate_chunk(self.player_chunk_coords[X_COORD] - RENDER_DISTANCE, self.player_chunk_coords[Y_COORD])
        self.generate_chunk(self.player_chunk_coords[X_COORD], self.player_chunk_coords[Y_COORD] + RENDER_DISTANCE)
        self.generate_chunk(self.player_chunk_coords[X_COORD], self.player_chunk_coords[Y_COORD] - RENDER_DISTANCE)
        self.generate_chunk(self.player_chunk_coords[X_COORD] - RENDER_DISTANCE, self.player_chunk_coords[Y_COORD] + RENDER_DISTANCE)
        self.generate_chunk(self.player_chunk_coords[X_COORD] + RENDER_DISTANCE, self.player_chunk_coords[Y_COORD] - RENDER_DISTANCE)
        self.generate_chunk(self.player_chunk_coords[X_COORD] - RENDER_DISTANCE, self.player_chunk_coords[Y_COORD] - RENDER_DISTANCE)
        self.generate_chunk(self.player_chunk_coords[X_COORD] + RENDER_DISTANCE, self.player_chunk_coords[Y_COORD] + RENDER_DISTANCE)

    def remove_far_chunks(self):
        for chunk in self.current_rendered_chunks:
            chunk_already_removed = False

            if not chunk_already_removed:
                if self.player_chunk_coords[X_COORD] - RENDER_DISTANCE > chunk[COORDS][X_COORD] or self.player_chunk_coords[X_COORD] + RENDER_DISTANCE < chunk[COORDS][X_COORD]:
                    chunk[ASTEROID_INDEX].empty()
                    self.current_rendered_chunks.remove(chunk)
                    chunk_already_removed = True

            if not chunk_already_removed:
                if self.player_chunk_coords[Y_COORD] - RENDER_DISTANCE > chunk[COORDS][Y_COORD] or self.player_chunk_coords[Y_COORD] + RENDER_DISTANCE < chunk[COORDS][Y_COORD]:
                    chunk[ASTEROID_INDEX].empty()
                    self.current_rendered_chunks.remove(chunk)
                    chunk_already_removed = True

    def debugging(self):
        if pygame.font:
            total_sprites = 0
            for data in self.current_rendered_chunks:
                for sprite in data[ASTEROID_INDEX]:
                    total_sprites += 1

            font = pygame.font.Font("courbd.ttf", 12)

            player_coords1 = font.render(str(self.player_chunk_coords), 1, (255, 255, 255))
            player_coords = font.render('Player chunk coords: ', 1, (255, 255, 255))
            num_chunks1 = font.render(str(len(self.current_rendered_chunks)), 1, (255, 255, 255))
            num_chunks = font.render('Chunks rendered: ', 1, (255, 255, 255))
            num_sprites1 = font.render(str(total_sprites), 1, (255, 255, 255))
            num_sprites = font.render('Sprites rendered: ', 1, (255, 255, 255))

            pc1_text = player_coords1.get_rect().move(150, 880)
            pc_text = player_coords.get_rect().move(10, 880)
            nc1_text = num_chunks1.get_rect().move(150, 865)
            nc_text = num_chunks.get_rect().move(10, 865)
            ns1_text = num_sprites1.get_rect().move(150, 850)
            ns_text = num_sprites.get_rect().move(10, 850)

            self.screen.blit(player_coords, pc_text)
            self.screen.blit(player_coords1, pc1_text)
            self.screen.blit(num_chunks, nc_text)
            self.screen.blit(num_chunks1, nc1_text)
            self.screen.blit(num_sprites, ns_text)
            self.screen.blit(num_sprites1, ns1_text)

    def update(self):
        self.spaceship_group.update()
        self.laser_group.update()

        for data in self.current_rendered_chunks:
            data[ASTEROID_INDEX].update(self.spaceship_group, self.laser_group)

        self.update_current_player_coords()

        if 0 == len(self.current_rendered_chunks):
            self.generate_nearby_chunks()

        if self.player_moved_chunks():
            self.update_current_chunk_coords()
            self.generate_nearby_chunks()
            self.remove_far_chunks()

    def load_asteroid_data(self):
        image1 = pygame.image.load('Sprites/asteroid1.png')
        self.asteroid_image_set.append(image1)
        damage1 = 47
        self.asteroid_damage_set.append(damage1)
        image2 = pygame.image.load('Sprites/asteroid2.png')
        self.asteroid_image_set.append(image2)
        damage2 = 74
        self.asteroid_damage_set.append(damage2)
        image3 = pygame.image.load('Sprites/asteroid3.png')
        self.asteroid_image_set.append(image3)
        damage3 = 63
        self.asteroid_damage_set.append(damage3)
        image4 = pygame.image.load('Sprites/asteroid4.png')
        self.asteroid_image_set.append(image4)
        damage4 = 18
        self.asteroid_damage_set.append(damage4)
        image5 = pygame.image.load('Sprites/asteroid5.png')
        self.asteroid_image_set.append(image5)
        damage5 = 7
        self.asteroid_damage_set.append(damage5)
        image6 = pygame.image.load('Sprites/asteroid6.png')
        self.asteroid_image_set.append(image6)
        damage6 = 8
        self.asteroid_damage_set.append(damage6)

    def render_level(self, fps):
        self.camera.update(self.spaceship)

        for data in self.current_rendered_chunks:
            for asteroid in data[ASTEROID_INDEX]:
                self.screen.blit(asteroid.image, self.camera.apply(asteroid))

        for laser in self.spaceship.laser_group:
            self.screen.blit(laser.image, self.camera.apply(laser))

        for sprite in self.spaceship_group:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        self.spaceship.debugging(self.screen, fps)
        self.debugging()

    def set_dt(self, dt):
        self.spaceship.set_dt(dt)

    def get_spaceship(self):
        return self.spaceship

    def get_camera(self):
        return self.camera
