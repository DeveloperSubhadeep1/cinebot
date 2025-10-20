from pymongo import MongoClient, errors
from tqdm import tqdm  # pip install tqdm

# Old Cluster URI
old_uri = "mongodb+srv://devildevil:devildevil@cluster0.0hajx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
old_client = MongoClient(old_uri)
old_db = old_client["cluster0"]
old_collection = old_db["Deendayal_files"]

# New Cluster URI
new_uri = "mongodb+srv://hellking1:hellking1@cluster0.zqg7rco.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
new_client = MongoClient(new_uri)
new_db = new_client["cluster0"]
new_collection = new_db["hellking_files"]

# Total documents
total_docs = old_collection.count_documents({})

inserted, skipped, failed = 0, 0, 0
failed_docs = []

# tqdm progress bar
for doc in tqdm(old_collection.find({}), total=total_docs, desc="Transferring"):
    try:
        new_collection.insert_one(doc)
        inserted += 1
    except errors.DuplicateKeyError:
        skipped += 1
    except Exception as e:
        # jodi kono document fail hoy
        failed += 1
        failed_docs.append({"_id": doc.get("_id"), "error": str(e)})

print(f"\n✅ Transfer Completed!")
print(f"Inserted: {inserted}, Skipped: {skipped}, Failed: {failed}")

if failed_docs:
    print("\nFailed documents:")
    for f in failed_docs:
        print(f)
