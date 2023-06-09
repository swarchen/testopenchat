from algoliasearch.search_client import SearchClient
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Initialize the Algolia client
algolia_client = SearchClient.create(
  os.getenv("ALGOLIA_APP_ID"),
  os.getenv("ALGOLIA_ADMIN_KEY")
)
algolia_index = algolia_client.init_index('coloring_pages')

def delete_coloring_pages(slugs):
    for slug in slugs:
        try:
            print(f"Processing coloring page with slug: {slug}")
            # Retrieve the coloring page ID using the slug
            response = supabase.table("coloring_pages").select("id").eq("slug", slug).execute()
            
            # If the response has data
            if response.data:
                # Extract the ID from the response
                id = response.data[0]['id']

                # Delete the relations from the coloring_pages_categories table
                print(f"Deleting relations for coloring page with ID {id}")
                supabase.table("coloring_pages_categories").delete().eq("coloring_page_id", id).execute()

                # Delete the record from the coloring_pages table
                print(f"Deleting coloring page with ID {id}")
                supabase.table("coloring_pages").delete().eq("id", id).execute()

                # Delete the object from the Algolia index
                print(f"Deleting coloring page with ID {id} from Algolia index")
                algolia_index.delete_object(str(id))

                print(f"Successfully deleted coloring page with slug: {slug}")
                
            else:
                print(f"No data found for slug {slug}")

        except Exception as e:
            print(f"Error occurred while deleting coloring page with slug {slug}: {e}")

# Usage
slugs_to_delete = ["splish-splash-987f"]
delete_coloring_pages(slugs_to_delete)
