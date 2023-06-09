from supabase import create_client, Client
from dotenv import load_dotenv
from ai_helper import multilingual_translator
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
coloredlogs.install(logger=logger)

def translate_and_insert_coloring_page(coloring_page):
    # Check if translation already exists
    exists = supabase.table('coloring_page_translations').select('*').eq('coloring_page_id', coloring_page['id']).execute().data

    if exists:
        logger.info(f'Translation already exists for coloring page {coloring_page["id"]}')
        return

    # Translate title and description
    multilingual_translation = multilingual_translator(coloring_page['title'])
    translations = json.loads(multilingual_translation)

    # Save translated coloring page to the database
    for translation in translations:
        response = supabase.table('coloring_page_translations').insert({
            'coloring_page_id': coloring_page['id'],
            'language_code': translation['language_code'],
            'title': translation['title'],
            'description': translation['description']
        }).execute()

def translate_and_save(start, end):
    # Fetch coloring pages in chunks
    coloring_pages = supabase.table("coloring_pages").select("*").range(start, end).execute().data

    if coloring_pages:
        # Translate and save each coloring page
        for coloring_page in coloring_pages:
            translate_and_insert_coloring_page(coloring_page)

        logger.info(f'Processed coloring_pages from {start} to {end}')
    else:
        logger.info(f'No more coloring_pages to process')

# You can call this function to translate and save all categories and coloring pages
# You might want to add error handling in case anything goes wrong
if __name__ == '__main__':
    limit = 5
    page = 0

    with Pool(processes=20) as pool:  # Adjust the number of processes according to your needs and system capabilities
        while True:
            start = page * limit
            end = start + limit
            coloring_pages = supabase.table("coloring_pages").select("*").range(start, end).execute().data
            
            if coloring_pages:
                pool.apply_async(translate_and_save, (start, end))
                page += 1
            else:
                break

        pool.close()
        pool.join()
