from ai_helper import categorization_assistant, copy_writer, categorization_assistant_v2
import os
import re
import json
import requests
import uuid
import discord
from PIL import Image
from dotenv import load_dotenv
from discord.ext import commands
from supabase import create_client, Client
import asyncio
import logging


load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
discord_token = os.getenv('DISCORD_BOT_TOKEN')

client = commands.Bot(command_prefix="*", intents=discord.Intents.all())
directory = os.getcwd()
supabase = create_client(url, key)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


def process_request(table_name, data):
    logging.info(f"Inserting {table_name}: {data}")
    response = supabase.table(table_name).insert(data).execute()
    logging.info(f"Response from inserting {table_name}: {response}")
    return response.data[0]

def update_request(table_name, data, id):
    logging.info(f"Updating {table_name}: {data}")
    response = supabase.table(table_name).update(data).eq("id", id).execute()
    logging.info(f"Response from updating {table_name}: {response}")
    return response.data[0]

def get_existing_categories():
    return supabase.table("categories").select("id, name").execute().data

def handle_image(image_file):
    with Image.open(image_file) as im:
        width, height = im.size
        mid_x, mid_y = width // 2, height // 2
        return [im.crop((0, 0, mid_x, mid_y)), im.crop((mid_x, 0, width, mid_y)), 
                im.crop((0, mid_y, mid_x, height)), im.crop((mid_x, mid_y, width, height))]

def generate_filename(midjourney_prompt):
    return midjourney_prompt.split(",")[0].strip().replace(" ", "_").lower()

async def download_image(url, midjourney_prompt):
    logging.info(f"Downloading image from url: {url}")
    response = requests.get(url)
    filename = generate_filename(midjourney_prompt)

    loop = asyncio.get_event_loop()
    coloring_page_data = await loop.run_in_executor(None, copy_writer, filename)
    existing_categories = await loop.run_in_executor(None, get_existing_categories)
    # get all names from existing_categories and join them into a string by comma
    existing_categories_names = ", ".join([category["name"] for category in existing_categories])

    coloring_page_json = json.loads(coloring_page_data)
    # get all titles from colorin_page_json
    coloring_page_titles = [coloring_page["title"] for coloring_page in coloring_page_json]

    # get categories from categorization assistant v2. eg: ["Animals", "Nature", "Food"]
    categories_data = await loop.run_in_executor(None, categorization_assistant_v2, existing_categories_names, filename)
    categories_json = json.loads(categories_data)
    
    # transform categories_data into array of category ids based on the category name using existing_categories
    category_ids = [next((category["id"] for category in existing_categories if category["name"] == category_name), None) for category_name in categories_json]

    # log the prompt and the matched categories
    logging.info(f"\nPrompt: {midjourney_prompt}\n")
    logging.info(f"\nCategories: {categories_json} Type: {type(categories_json)}\n")
    logging.info(f"\nCategory Ids: {category_ids}\n")

    if response.status_code == 200:
        logging.info("Image downloaded successfully. Processing image...")
        input_folder, output_folder = "input", "../front-end/public/images"
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(input_folder, exist_ok=True)

        with open(f"{directory}/{input_folder}/{filename}", "wb") as f:
            f.write(response.content)

        input_file = os.path.join(input_folder, filename)
        file_prefix = os.path.splitext(filename)[0]
        images = handle_image(input_file)

        for image_index, image in enumerate(images):
            uuid_4 = str(uuid.uuid4())[:4]
            img_filename = file_prefix + '_' + uuid_4
            title, description = coloring_page_json[image_index]["title"], coloring_page_json[image_index]["description"]
            slug = title.lower().replace(" ", "-") + f"-{uuid_4}"
            image.save(os.path.join(output_folder, img_filename + ".jpg"))
            inserted_coloring_page = await loop.run_in_executor(None, process_request, "coloring_pages", {"filename": img_filename + ".jpg", "title": title, "description": description, "slug": slug})
            logging.info(f"Inserted coloring page: {inserted_coloring_page}")
            
            # link coloring page to categories in supabase if categories exist
            if(category_ids):
                for category_id in category_ids:
                    if(category_id):
                        logging.info(f"Inserting coloring page to category: {category_id}")
                        await loop.run_in_executor(None, process_request, "coloring_pages_categories", {"coloring_page_id": inserted_coloring_page["id"], "category_id": category_id})
                        await loop.run_in_executor(None, update_request, "categories", {"feature_image": img_filename + ".jpg"}, category_id)
                # else:
                #     logging.info(f"Creating new category: {category['name']}")
                #     inserted_category = await loop.run_in_executor(None, process_request, "categories", {"name": category["name"], "slug": category["slug"], "description": category["description"], "feature_image": img_filename + ".jpg"})
                #     categories_json[category_index]["id"] = inserted_category["id"]
                #     await loop.run_in_executor(None, process_request, "coloring_pages_categories", {"coloring_page_id": inserted_coloring_page["id"], "category_id": inserted_category["id"]})
        logging.info("Image processed successfully.")
        
        # Delete the input file
        os.remove(f"{directory}/{input_folder}/{filename}")
        return True
    else:
        logging.error("Failed to download image.")
        return False

@client.event
async def on_ready():
    logging.info(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.attachments:
        for attachment in message.attachments:
            match = re.search(r'\*\*(.*?)\*\*', message.content)
            if match:
                midjourney_prompt = match.group(1)
                result = await download_image(attachment.url, midjourney_prompt)
                if result:
                    await message.channel.send('Image processed and saved.')
                else:
                    await message.channel.send('Failed to download image.')

client.run(discord_token)
