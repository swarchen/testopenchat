from supabase import create_client, Client
from dotenv import load_dotenv
from ai_helper import multilingual_translator_category
from multiprocessing import Pool
import os
import json
import coloredlogs, logging

load_dotenv()

# Initialize the Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Create a logger object
logger = logging.getLogger(__name__)

# Install coloredlogs
coloredlogs.install(level='DEBUG', logger=logger)

def translate_and_insert_category(category):
    multilingual_translation = multilingual_translator_category(category['name'])
    translations = json.loads(multilingual_translation)

    # Save translated coloring page to the database
    for translation in translations:
        response = supabase.table('category_translations').insert({
            'category_id': category['id'],
            'language_code': translation['language_code'],
            'name': translation['name'],
            'description': translation['description']
        }).execute()

def translate_and_save(start, end):
    # Fetch coloring pages in chunks
    categories = supabase.table("categories").select("*").range(start, end).execute().data

    if categories:
        # Translate and save each coloring page
        for category in categories:
            translate_and_insert_category(category)

        logger.info(f'Processed categories from {start} to {end}')
    else:
        logger.info(f'No more categories to process')

# You can call this function to translate and save all categories and coloring pages
# You might want to add error handling in case anything goes wrong
if __name__ == '__main__':
    limit = 1000
    page = 0

    with Pool(processes=20) as pool:  # Adjust the number of processes according to your needs and system capabilities
        while True:
            start = page * limit
            end = start + limit - 1
            categories = supabase.table("categories").select("*").range(start, end).execute().data
            
            if categories:
                pool.apply_async(translate_and_save, (start, end))
                page += 1
            else:
                break

        pool.close()
        pool.join()
