import os
import pymongo
from info import DATABASE_NAME  # Keep DATABASE_NAME as it is
from pyrogram import enums
import logging
from sample_info import tempDict

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Read the MongoDB URIs from environment variables
DATABASE_URI = os.getenv("MONGODB_URI")  # Set this in Koyeb
SECONDDB_URI = os.getenv("SECOND_MONGODB_URI")  # Set this in Koyeb

# Initialize MongoDB clients
myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]

myclient2 = pymongo.MongoClient(SECONDDB_URI)
mydb2 = myclient2[DATABASE_NAME]

async def add_filter(grp_id, text, reply_text, btn, file, alert):
    if tempDict['indexDB'] == DATABASE_URI:
        mycol = mydb[str(grp_id)]
    else:
        mycol = mydb2[str(grp_id)]

    data = {
        'text': str(text),
        'reply': str(reply_text),
        'btn': str(btn),
        'file': str(file),
        'alert': str(alert)
    }

    try:
        mycol.update_one({'text': str(text)}, {"$set": data}, upsert=True)
    except Exception as e:
        logger.exception('Some error occurred!', exc_info=True)

async def find_filter(group_id, name):
    mycol = mydb[str(group_id)]
    mycol2 = mydb2[str(group_id)]
    
    query = mycol.find({"text": name})
    query2 = mycol2.find({"text": name})

    try:
        for file in query:
            reply_text = file['reply']
            btn = file['btn']
            fileid = file['file']
            alert = file.get('alert', None)  # Use .get() to avoid KeyError
            return reply_text, btn, alert, fileid
    except Exception as e:
        logger.exception('Error in finding filter in primary DB', exc_info=True)

    try:
        for file in query2:
            reply_text = file['reply']
            btn = file['btn']
            fileid = file['file']
            alert = file.get('alert', None)  # Use .get() to avoid KeyError
            return reply_text, btn, alert, fileid
    except Exception as e:
        logger.exception('Error in finding filter in secondary DB', exc_info=True)

    return None, None, None, None

async def get_filters(group_id):
    mycol = mydb[str(group_id)]
    mycol2 = mydb2[str(group_id)]

    texts = []
    query = mycol.find()
    query2 = mycol2.find()

    try:
        for file in query:
            text = file['text']
            texts.append(text)
    except Exception as e:
        logger.exception('Error in getting filters from primary DB', exc_info=True)

    try:
        for file in query2:
            text = file['text']
            texts.append(text)
    except Exception as e:
        logger.exception('Error in getting filters from secondary DB', exc_info=True)

    return texts

async def delete_filter(message, text, group_id):
    mycol = mydb[str(group_id)]
    mycol2 = mydb2[str(group_id)]
    
    myquery = {'text': text}
    query = mycol.count_documents(myquery)
    query2 = mycol2.count_documents(myquery)

    if query == 1:
        mycol.delete_one(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that filter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    elif query2 == 1:
        mycol2.delete_one(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that filter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("Couldn't find that filter!", quote=True)

async def del_all(message, group_id, title):
    if str(group_id) not in mydb.list_collection_names() and str(group_id) not in mydb2.list_collection_names():
        await message.edit_text(f"Nothing to remove in {title}!")
        return

    mycol = mydb[str(group_id)]
    mycol2 = mydb2[str(group_id)]
    try:
        mycol.drop()
        mycol2.drop()
        await message.edit_text(f"All filters from {title} have been removed")
    except Exception as e:
        logger.exception('Error in deleting all filters', exc_info=True)
        await message.edit_text("Couldn't remove all filters from group!")

async def count_filters(group_id):
    mycol = mydb[str(group_id)]
    mycol2 = mydb2[str(group_id)]

    count = mycol.count_documents({}) + mycol2.count_documents({})
    return False if count == 0 else count

async def filter_stats():
    collections = mydb.list_collection_names()
    collections2 = mydb2.list_collection_names()

    if "CONNECTION" in collections:
        collections.remove("CONNECTION")
    elif "CONNECTION" in collections2:
        collections2.remove("CONNECTION")

    totalcount = 0
    for collection in collections:
        mycol = mydb[collection]
        count = mycol.count_documents({})
        totalcount += count

    for collection in collections2:
        mycol2 = mydb2[collection]
        count2 = mycol2.count_documents({})
        totalcount += count2

    totalcollections = len(collections) + len(collections2)

    return totalcollections, totalcount
