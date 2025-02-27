import os
import pymongo
from info import DATABASE_NAME  # Keep DATABASE_NAME as it is
from pyrogram import enums
from sample_info import tempDict
import logging

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

async def add_gfilter(gfilters, text, reply_text, btn, file, alert):
    # Check indexDB
    if tempDict['indexDB'] == DATABASE_URI:
        mycol = mydb[str(gfilters)]
    else:
        mycol = mydb2[str(gfilters)]

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
        logger.exception('Some error occurred while adding gfilter!', exc_info=True)

async def find_gfilter(gfilters, name):
    mycol = mydb[str(gfilters)]
    mycol2 = mydb2[str(gfilters)]
    
    query = mycol.find({"text": name})
    if query.count() == 0:
        query = mycol2.find({"text": name})

    try:
        for file in query:
            reply_text = file['reply']
            btn = file['btn']
            fileid = file['file']
            alert = file.get('alert', None)  # Use .get() to avoid KeyError
            return reply_text, btn, alert, fileid
    except Exception as e:
        logger.exception('Error in finding gfilter!', exc_info=True)
        return None, None, None, None

async def get_gfilters(gfilters):
    mycol = mydb[str(gfilters)]
    mycol2 = mydb2[str(gfilters)]

    texts = []
    query = mycol.find()
    query2 = mycol2.find()

    try:
        for file in query:
            text = file['text']
            texts.append(text)
    except Exception as e:
        logger.exception('Error in getting gfilters from primary DB', exc_info=True)

    try:
        for file in query2:
            text = file['text']
            texts.append(text)
    except Exception as e:
        logger.exception('Error in getting gfilters from secondary DB', exc_info=True)

    return texts

async def delete_gfilter(message, text, gfilters):
    mycol = mydb[str(gfilters)]
    mycol2 = mydb2[str(gfilters)]
    
    myquery = {'text': text}
    query = mycol.count_documents(myquery)
    query2 = mycol2.count_documents(myquery)

    if query == 1:
        mycol.delete_one(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that gfilter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    elif query2 == 1:
        mycol2.delete_one(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that gfilter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("Couldn't find that gfilter!", quote=True)

async def del_allg(message, gfilters):
    if str(gfilters) not in mydb.list_collection_names() and str(gfilters) not in mydb2.list_collection_names():
        await message.edit_text("Nothing to remove!")
        return

    mycol = mydb[str(gfilters)]
    mycol2 = mydb2[str(gfilters)]
    try:
        mycol.drop()
        mycol2.drop()
        await message.edit_text("All gfilters have been removed!")
    except Exception as e:
        logger.exception('Error in deleting all gfilters', exc_info=True)
        await message.edit_text("Couldn't remove all gfilters!")

async def count_gfilters(gfilters):
    mycol = mydb[str(gfilters)]
    mycol2 = mydb2[str(gfilters)]

    count = mycol.count_documents({}) + mycol2.count_documents({})
    return False if count == 0 else count

async def gfilter_stats():
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
