import asyncio
import pygame
import pygame.sprite
import pygame.font
import pygame.transform
import pygame.draw
import pygame.display
import pygame.event
import pygame.key
import pygame.time
from game import Game

async def main():
    await Game().run()

asyncio.run(main())
