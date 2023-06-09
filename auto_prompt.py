import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
import asyncio
import pyautogui as pg

load_dotenv()

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

discord_token = os.getenv('DISCORD_BOT_TOKEN')

# Using readlines()
prompt_file = open('prompts.txt', 'r')
prompts = prompt_file.readlines()

prompt_counter = 0
max_concurrent_jobs = 3
current_jobs = 0

# Create lock for shared variables
lock = asyncio.Lock()
pg_lock = asyncio.Lock()

client = commands.Bot(command_prefix="*", intents=discord.Intents.all())

@client.event
async def on_ready():
    logger.info("Bot connected")

@client.event
async def on_message(message):
    global prompt_counter
    global current_jobs

    msg = message.content
    logger.info(f"Received message: {msg}")
    # if message.attachments then current_jobs -=1
    if message.attachments:
        async with lock:
            current_jobs -= 1
        logger.info(f"Got image from midjourney. Current jobs: {current_jobs}")

        if prompt_counter < len(prompts) and current_jobs < max_concurrent_jobs:
            async with lock:
                current_job_index = prompt_counter
                prompt_counter += 1
                current_jobs += 1
            logger.info("total prompts left: " + str(len(prompts) - prompt_counter))
            await process_prompt(prompts[current_job_index])
    # Start Automation by typing "automation" in the discord channel
    elif msg == 'automation' and prompt_counter < len(prompts):
        for _ in range(min(max_concurrent_jobs, len(prompts) - prompt_counter)):
            async with lock:
                current_job_index = prompt_counter
                prompt_counter += 1
                current_jobs += 1
            await process_prompt(prompts[current_job_index])

async def process_prompt(prompt):
    global current_jobs
    logger.info("Starting automation")
    async with pg_lock:
        await asyncio.sleep(1)
        pg.press('tab')
        await asyncio.sleep(1)
        pg.write('/imagine')
        await asyncio.sleep(2)
        pg.press('tab')
        pg.write(prompt)
        await asyncio.sleep(1)
        pg.press('enter')
        await asyncio.sleep(2)
    logger.info(f"Automated task started for prompt {prompt}. Current jobs: {current_jobs}")
    async with lock:
        current_jobs -= 1

client.run(discord_token)
