

import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import CAPTION_LANGUAGES, DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, DEENDAYAL_MOVIE_UPDATE_CHANNEL, OWNERID
from utils import get_settings, save_group_settings, temp, get_status
from database.users_chats_db import add_name
from .Imdbposter import get_movie_details, fetch_image
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#---------------------------------------------------------
# Some basic variables needed
tempDict = {'indexDB': DATABASE_URI}

# Primary DB
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

#secondary db
client2 = AsyncIOMotorClient(DATABASE_URI2)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)


# Primary DB Model
@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance2.register
class Media2(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def choose_mediaDB():
    """This Function chooses which database to use based on the value of indexDB key in the dict tempDict."""
    global saveMedia
    if tempDict['indexDB'] == DATABASE_URI:
        logger.info("Using first db (Media)")
        saveMedia = Media
    else:
        logger.info("Using second db (Media2)")
        saveMedia = Media2

async def save_file(bot, media):
  """Save file in database"""
  global saveMedia
  file_id, file_ref = unpack_new_file_id(media.file_id)
  file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
  try:
    if saveMedia == Media2:
        if await Media.count_documents({'file_id': file_id}, limit=1):
            logger.warning(f'{file_name} is already saved in primary database!')
            return False, 0
    file = saveMedia(
        file_id=file_id,
        file_ref=file_ref,
        file_name=file_name,
        file_size=media.file_size,
        file_type=media.file_type,
        mime_type=media.mime_type,
        caption=media.caption.html if media.caption else None,
    )
  except ValidationError:
    logger.exception('Error occurred while saving file in database')
    return False, 2
  else:
    try:
      await file.commit()
    except DuplicateKeyError:
      logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in database')
      return False, 0
    else:
        logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
        if await get_status(bot.me.id):
            await send_msg(bot, media.file_name, media.caption.html if media.caption else "", media.file_size)
        return True, 1

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = ((await Media.count_documents(filter))+(await Media2.count_documents(filter)))

    #verifies max_results is an even number or not
    if max_results%2 != 0:
        logger.info(f"Since max_results is an odd number ({max_results}), bot will use {max_results+1} as max_results to make it even.")
        max_results += 1

    cursor = Media.find(filter)
    cursor2 = Media2.find(filter)

    cursor.sort('$natural', -1)
    cursor2.sort('$natural', -1)

    cursor2.skip(offset).limit(max_results)

    fileList2 = await cursor2.to_list(length=max_results)
    if len(fileList2)<max_results:
        next_offset = offset+len(fileList2)
        cursorSkipper = (next_offset-(await Media2.count_documents(filter)))
        cursor.skip(cursorSkipper if cursorSkipper>=0 else 0).limit(max_results-len(fileList2))
        fileList1 = await cursor.to_list(length=(max_results-len(fileList2)))
        files = fileList2+fileList1
        next_offset = next_offset + len(fileList1)
    else:
        files = fileList2
        next_offset = offset + max_results
    if next_offset >= total_results:
        next_offset = ''
    return files, next_offset, total_results


async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    cursor = Media.find(filter)
    cursor2 = Media2.find(filter)

    cursor.sort('$natural', -1)
    cursor2.sort('$natural', -1)

    files = ((await cursor2.to_list(length=(await Media2.count_documents(filter))))+(await cursor.to_list(length=(await Media.count_documents(filter)))))

    total_results = len(files)

    return files, total_results

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    if not filedetails:
        cursor2 = Media2.find(filter)
        filedetails = await cursor2.to_list(length=1)
    return filedetails


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref


async def send_msg(bot, filename, caption, file_size):
    try:
        filename = re.sub(r'\(\@\S+\)|\[\@\S+\]|\b@\S+|\bwww\.\S+', '', filename).strip()
        caption = re.sub(r'\(\@\S+\)|\[\@\S+\]|\b@\S+|\bwww\.\S+', '', caption).strip()
        
        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None

        pattern = r"(?i)(?:s|season)0*(\d{1,2})"
        season = re.search(pattern, caption) or re.search(pattern, filename)
        season = season.group(1) if season else None 

        if year:
            filename = filename[: filename.find(year) + 4]  
        elif season and season in filename:
            filename = filename[: filename.find(season) + 1]

        qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", "camrip", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", "dvdrip", "dvdscr", "HDTC", "dvdscreen", "HDTS", "hdts"]
        quality = await get_qualities(caption.lower(), qualities) or "HDRip"


        language = ""
        possible_languages = CAPTION_LANGUAGES
        for lang in possible_languages:
            if lang.lower() in caption.lower():
                language += f"{lang}, "
        language = language[:-2] if language else "N/A"

        if await add_name(OWNERID, filename):
            imdb = await get_movie_details(filename)
            resized_poster = None

            # IMDb থেকে ডেটা সংগ্রহ
            title = imdb.get('title', filename) if imdb else filename
            year = imdb.get('year', '') if imdb else ''
            # clean_title = re.sub(r'[^a-zA-Z0-9]', '', title)
            clean_title = re.sub(r'\s+', ' ', re.sub(r'[^a-zA-Z0-9 ]', '', title.replace("_", " ").replace("-", " ").replace(".", " "))).strip()


            movie_name_hashtag = f"#{clean_title.replace(' ', '')}"
            #movie_name_hashtag = f"#{title.strip().replace(' ', '').replace('-', '').replace('.', '').replace('_', '').replace(',', '').replace(';', '').replace(':', '')}"
            
            genres = imdb.get('genres', 'N/A') if imdb else 'N/A'
            kind_raw = imdb.get('kind', 'FILE') if imdb else 'FILE'
            # hashtag = f"#{kind_raw.upper().replace(' ', '_')}"



            genre_list = genres.split(',')
            genre_hashtags = []
            for genre in genre_list:
                # Remove leading/trailing whitespace and convert to lowercase
                clean_genre = genre.strip().lower()
                if clean_genre and clean_genre != 'n/a':
                    # Replace spaces with underscores and add a hashtag
                    hashtag = f"#{clean_genre.replace(' ', '_')}"
                    genre_hashtags.append(hashtag)

            # Limit to a maximum of 6 hashtags
            limited_genre_hashtags = genre_hashtags[:6]

            # Join the limited list of hashtags into a single string
            genres_to_display = ", ".join(limited_genre_hashtags) if limited_genre_hashtags else "N/A"



            # Existing hashtag for the file kind
            hashtag = f"#{kind_raw.upper().replace(' ', '_')}"


            # বর্তমান সময় (Asia/Kolkata timezone)
            kolkata_tz = pytz.timezone("Asia/Kolkata")
            now = datetime.now(kolkata_tz)
            timestamp = now.strftime("%d %b %Y | %I:%M %p")

            # নতুন ফরম্যাট অনুযায়ী টেক্সট তৈরি
            text_template = (
                "#𝑵𝒆𝒘_𝑭𝒊𝒍𝒆_𝑨𝒅𝒅𝒆𝒅 ✅\n\n😈 `{title} {year}` ⿻ \n\n🎭 ɢᴇɴʀᴇs : {genre_hashtags_text}\n\n📽 ғᴏʀᴍᴀᴛ: {quality}\n🔊 ᴀᴜᴅɪᴏ: {language}\n\n{hashtag}\n\n𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝖡𝗒 - @Hell_king_69_Bot\n\n🕒 {timestamp}\n\n#️⃣ {movie_name_hashtag}\n\n<blockquote>ᴄᴏᴘʏ ᴛʜᴇ ɴᴀᴍᴇ ᴀɴᴅ ᴄʟɪᴄᴋ ᴏɴ <b>ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ</b>\nʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴘᴇꜱᴛ ᴛʜᴇ ɴᴀᴍᴇ ᴀᴛ ɢʀᴏᴜᴘ</blockquote>")
            
            text = text_template.format(
                title=title,
                year=year,
                # genres=genres,
                genre_hashtags_text=genres_to_display,
                quality=quality,
                language=language,
                hashtag=hashtag,
                timestamp=timestamp,
                movie_name_hashtag=movie_name_hashtag
            )

            if imdb:
                poster_url = imdb.get('poster_url')
                if poster_url:
                    resized_poster = await fetch_image(poster_url)

            filenames = re.sub(r'[^a-zA-Z0-9\-]', '', 
                   filename.replace(" ", "-")
                           .replace(".", "-")
                           .replace("_", "-"))
            btn = [[InlineKeyboardButton('🔍 𝕊𝕖𝕒𝕣𝕔𝕙 ℍ𝕖𝕣𝕖 🔍', url="https://t.me/The_hell_king_movie_group")]]

            if resized_poster:
                await bot.send_photo(chat_id=DEENDAYAL_MOVIE_UPDATE_CHANNEL, photo=resized_poster, caption=text, reply_markup=InlineKeyboardMarkup(btn))
            else:
                await bot.send_message(chat_id=DEENDAYAL_MOVIE_UPDATE_CHANNEL, text=text, reply_markup=InlineKeyboardMarkup(btn))

    except Exception as e:
        logger.error(f"Error in send_msg: {e}")


async def get_qualities(text, qualities: list):
    """Get all Quality from text"""
    quality = []
    for q in qualities:
        if q in text:
            quality.append(q)





# import logging
# from struct import pack
# import re
# import base64
# from pyrogram.file_id import FileId
# from pymongo.errors import DuplicateKeyError
# from umongo import Instance, Document, fields
# from motor.motor_asyncio import AsyncIOMotorClient
# from marshmallow.exceptions import ValidationError
# from info import CAPTION_LANGUAGES, DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, DEENDAYAL_MOVIE_UPDATE_CHANNEL, OWNERID
# from utils import get_settings, save_group_settings, temp, get_status
# from database.users_chats_db import add_name
# from .Imdbposter import get_movie_details, fetch_image
# from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# from datetime import datetime
# import pytz

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# #---------------------------------------------------------
# # Some basic variables needed
# tempDict = {'indexDB': DATABASE_URI}

# # Primary DB
# client = AsyncIOMotorClient(DATABASE_URI)
# db = client[DATABASE_NAME]
# instance = Instance.from_db(db)

# #secondary db
# client2 = AsyncIOMotorClient(DATABASE_URI2)
# db2 = client2[DATABASE_NAME]
# instance2 = Instance.from_db(db2)


# # Primary DB Model
# @instance.register
# class Media(Document):
#     file_id = fields.StrField(attribute='_id')
#     file_ref = fields.StrField(allow_none=True)
#     file_name = fields.StrField(required=True)
#     file_size = fields.IntField(required=True)
#     file_type = fields.StrField(allow_none=True)
#     mime_type = fields.StrField(allow_none=True)
#     caption = fields.StrField(allow_none=True)

#     class Meta:
#         indexes = ('$file_name', )
#         collection_name = COLLECTION_NAME

# @instance2.register
# class Media2(Document):
#     file_id = fields.StrField(attribute='_id')
#     file_ref = fields.StrField(allow_none=True)
#     file_name = fields.StrField(required=True)
#     file_size = fields.IntField(required=True)
#     file_type = fields.StrField(allow_none=True)
#     mime_type = fields.StrField(allow_none=True)
#     caption = fields.StrField(allow_none=True)

#     class Meta:
#         indexes = ('$file_name', )
#         collection_name = COLLECTION_NAME

# async def choose_mediaDB():
#     """This Function chooses which database to use based on the value of indexDB key in the dict tempDict."""
#     global saveMedia
#     if tempDict['indexDB'] == DATABASE_URI:
#         logger.info("Using first db (Media)")
#         saveMedia = Media
#     else:
#         logger.info("Using second db (Media2)")
#         saveMedia = Media2

# async def save_file(bot, media):
#   """Save file in database"""
#   global saveMedia
#   file_id, file_ref = unpack_new_file_id(media.file_id)
#   file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
#   try:
#     if saveMedia == Media2:
#         if await Media.count_documents({'file_id': file_id}, limit=1):
#             logger.warning(f'{file_name} is already saved in primary database!')
#             return False, 0
#     file = saveMedia(
#         file_id=file_id,
#         file_ref=file_ref,
#         file_name=file_name,
#         file_size=media.file_size,
#         file_type=media.file_type,
#         mime_type=media.mime_type,
#         caption=media.caption.html if media.caption else None,
#     )
#   except ValidationError:
#     logger.exception('Error occurred while saving file in database')
#     return False, 2
#   else:
#     try:
#       await file.commit()
#     except DuplicateKeyError:
#       logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in database')
#       return False, 0
#     else:
#         logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
#         if await get_status(bot.me.id):
#             await send_msg(bot, media.file_name, media.caption.html if media.caption else "", media.file_size)
#         return True, 1

# async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
#     """For given query return (results, next_offset)"""
#     if chat_id is not None:
#         settings = await get_settings(int(chat_id))
#         try:
#             if settings['max_btn']:
#                 max_results = 10
#             else:
#                 max_results = int(MAX_B_TN)
#         except KeyError:
#             await save_group_settings(int(chat_id), 'max_btn', False)
#             settings = await get_settings(int(chat_id))
#             if settings['max_btn']:
#                 max_results = 10
#             else:
#                 max_results = int(MAX_B_TN)
#     query = query.strip()
#     if not query:
#         raw_pattern = '.'
#     elif ' ' not in query:
#         raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
#     else:
#         raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

#     try:
#         regex = re.compile(raw_pattern, flags=re.IGNORECASE)
#     except:
#         return []

#     if USE_CAPTION_FILTER:
#         filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
#     else:
#         filter = {'file_name': regex}

#     if file_type:
#         filter['file_type'] = file_type

#     total_results = ((await Media.count_documents(filter))+(await Media2.count_documents(filter)))

#     #verifies max_results is an even number or not
#     if max_results%2 != 0:
#         logger.info(f"Since max_results is an odd number ({max_results}), bot will use {max_results+1} as max_results to make it even.")
#         max_results += 1

#     cursor = Media.find(filter)
#     cursor2 = Media2.find(filter)

#     cursor.sort('$natural', -1)
#     cursor2.sort('$natural', -1)

#     cursor2.skip(offset).limit(max_results)

#     fileList2 = await cursor2.to_list(length=max_results)
#     if len(fileList2)<max_results:
#         next_offset = offset+len(fileList2)
#         cursorSkipper = (next_offset-(await Media2.count_documents(filter)))
#         cursor.skip(cursorSkipper if cursorSkipper>=0 else 0).limit(max_results-len(fileList2))
#         fileList1 = await cursor.to_list(length=(max_results-len(fileList2)))
#         files = fileList2+fileList1
#         next_offset = next_offset + len(fileList1)
#     else:
#         files = fileList2
#         next_offset = offset + max_results
#     if next_offset >= total_results:
#         next_offset = ''
#     return files, next_offset, total_results


# async def get_bad_files(query, file_type=None, filter=False):
#     """For given query return (results, next_offset)"""
#     query = query.strip()
#     if not query:
#         raw_pattern = '.'
#     elif ' ' not in query:
#         raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
#     else:
#         raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

#     try:
#         regex = re.compile(raw_pattern, flags=re.IGNORECASE)
#     except:
#         return []

#     if USE_CAPTION_FILTER:
#         filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
#     else:
#         filter = {'file_name': regex}

#     if file_type:
#         filter['file_type'] = file_type

#     cursor = Media.find(filter)
#     cursor2 = Media2.find(filter)

#     cursor.sort('$natural', -1)
#     cursor2.sort('$natural', -1)

#     files = ((await cursor2.to_list(length=(await Media2.count_documents(filter))))+(await cursor.to_list(length=(await Media.count_documents(filter)))))

#     total_results = len(files)

#     return files, total_results

# async def get_file_details(query):
#     filter = {'file_id': query}
#     cursor = Media.find(filter)
#     filedetails = await cursor.to_list(length=1)
#     if not filedetails:
#         cursor2 = Media2.find(filter)
#         filedetails = await cursor2.to_list(length=1)
#     return filedetails


# def encode_file_id(s: bytes) -> str:
#     r = b""
#     n = 0

#     for i in s + bytes([22]) + bytes([4]):
#         if i == 0:
#             n += 1
#         else:
#             if n:
#                 r += b"\x00" + bytes([n])
#                 n = 0

#             r += bytes([i])

#     return base64.urlsafe_b64encode(r).decode().rstrip("=")

# def encode_file_ref(file_ref: bytes) -> str:
#     return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

# def unpack_new_file_id(new_file_id):
#     """Return file_id, file_ref"""
#     decoded = FileId.decode(new_file_id)
#     file_id = encode_file_id(
#         pack(
#             "<iiqq",
#             int(decoded.file_type),
#             decoded.dc_id,
#             decoded.media_id,
#             decoded.access_hash
#         )
#     )
#     file_ref = encode_file_ref(decoded.file_reference)
#     return file_id, file_ref


# async def send_msg(bot, filename, caption, file_size):
#     try:
#         filename = re.sub(r'\(\@\S+\)|\[\@\S+\]|\b@\S+|\bwww\.\S+', '', filename).strip()
#         caption = re.sub(r'\(\@\S+\)|\[\@\S+\]|\b@\S+|\bwww\.\S+', '', caption).strip()
        
#         year_match = re.search(r"\b(19|20)\d{2}\b", caption)
#         year = year_match.group(0) if year_match else None

#         pattern = r"(?i)(?:s|season)0*(\d{1,2})"
#         season = re.search(pattern, caption) or re.search(pattern, filename)
#         season = season.group(1) if season else None 

#         if year:
#             filename = filename[: filename.find(year) + 4]  
#         elif season and season in filename:
#             filename = filename[: filename.find(season) + 1]

#         qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", "camrip", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", "dvdrip", "dvdscr", "HDTC", "dvdscreen", "HDTS", "hdts"]
#         quality = await get_qualities(caption.lower(), qualities) or "HDRip"


#         language = ""
#         possible_languages = CAPTION_LANGUAGES
#         for lang in possible_languages:
#             if lang.lower() in caption.lower():
#                 language += f"{lang}, "
#         language = language[:-2] if language else "N/A"

#         # --- Start of Bad Words Removal Logic ---
#         bad_tags = [
#             # Popular site / piracy source names
#             "PrivateMovieZ", "Toonworld4all", "TheMoviesBoss", "1TamilMV", "TamilBlasters",
#             "1TamilBlasters", "SkyMoviesHD", "ExtraFlix", "HDM2", "MoviesMod", "HDHub4u",
#             "MkvCinemas", "PrimeFix", "MovieVerse", "Vegamovies", "Filmyzilla", "Moviespapa",
#             "SSRMovies", "KatMovieHD", "9xMovies", "7StarHD", "World4uFree", "MLWBD",
#             "HDMoviesPoint", "MoviesBaba", "Cinevood", "MoviesDrive", "MoviesCounter",
#             "Filmywap", "Mp4Moviez", "Bolly4u", "HDHub", "CineWap", "TheMovieVilla",
#             "MovieVilla", "HDMoviesHub", "TheMovieBay", "TheMoviesflix", "FlixZilla",
#             "MoviesRoot", "FilmyHit", "HDHub4U", "HDFlix", "MoviezVilla", "MoviesTime",
#             "MovieHub", "FlickPrime", "FilmyMeet", "SeriesWorld", "SeriesVerse",
#             "SeriesAdda", "MoviesAdda", "FilmyWorld", "FilmyWap", "MovieAddict", "MovieVillaHD",
#             "CinemaVilla", "FilmyMonster", "FilmyBoss", "FilmyFly", "FilmyHunk", "FilmyMaza",
#             "FilmyZap", "MoviesGalaxy", "MoviesNation", "MoviesForest", "MoviesDriveHD",
#             "HDPrintMovies", "MoviesRockers", "TamilRockers", "TamilYogi", "CoolMoviez",
#             "Okhatrimaza", "JioRockers", "Isaimini", "KuttyMovies", "Masstamilan", "TodayPK",
#             "MovieMad", "CineRule", "Moviesda", "HDMoviesKing", "MoviesVillaHD", "FilmyDost",
#             "FilmyVerse", "FilmyMania", "MoviesNext", "FlixPoint", "MoviesBossHD", "PrimeHUB",
#             "PrimePlay", "MovieGang", "FlixKing", "CineBazz", "BollyStream", "AllMoviesHub",
#             "WatchHub", "HDWorld", "StreamVilla", "HDFilmBoss", "MovieVerseHD", "CineHD",
#             "HDFilmAdda", "FilmWorld", "CinePoint", "StreamFlix", "MovieRulz", "Movies2Watch",
#             "FilmyGalaxy", "FilmyLink", "Movierulz", "CineBoss", "Movies4U", "MoviesHDWorld",

#             # Common domain or Telegram channel words
#             "join", "www", "villa", "tg", "original", "moviez", "hub", "flix", "movies",
#             "cinema", "prime", "club", "team", "channel", "official", "group", "download",
#             "link", "dotcom", "dotin", "dotxyz", "dotorg", "dotlol", "dotapp", "dotfun",
#             "dotpro", "dotbar", "net", "hd", "hq", "uhd", "4k", "8k", "1080p", "720p", "480p",
#             "rip", "print", "cam", "camrip", "ts", "telesync", "hdts", "hdcam", "hdtv",
#             "webdl", "webrip", "hdrip", "brrip", "dvdrip", "hevc", "x265", "x264", "10bit",
#             "hvec", "hvec5", "sprint", "screenprint", "hqprint", "hc", "hardcoded", "wp",
#             "workprint", "dual", "audio", "sub", "subs", "subbed", "uncensored", "exclusive",
#             "remux", "encoded", "ripzone", "encodes", "repack", "extended", "directorscut",
#             "multi", "dubbed", "multiaudio", "uncut",

#             # Telegram channels / bot or mirror keywords
#             "bot", "moviehub", "premium", "exclusive", "leak", "index", "backup", "mirror",
#             "mega", "upload", "storage", "fastdownload", "directlink", "torrent", "magnet",
#             "drive", "gdrive", "cloud", "archive", "collection", "direct", "watchonline",
#             "instant", "instantdl", "highspeed", "cdn", "mirrors", "reupload", "filehost",
#             "shortlink", "downloadhub", "movieindex", "cineindex", "cloudfiles", "fastmirror",
#             "oneclick", "zippyshare", "megaup", "1fichier", "sendcm", "workupload", "pixeldrain",
#             "reuploadhub", "cdnmirror", "dlbot", "filemirror", "fastserver", "uptobox",
#             "uploady", "dropgalaxy", "telegramhub", "telegrammovies", "tgindex", "movietg"
#         ]

#         cleaned_filename = filename
#         for tag in bad_tags:
#             # Create a regex pattern to find the tag as a whole word, case-insensitive
#             # \b ensures whole word match, re.IGNORECASE makes it case-insensitive
#             cleaned_filename = re.sub(r'\b' + re.escape(tag) + r'\b', '', cleaned_filename, flags=re.IGNORECASE).strip()
#             # Remove multiple spaces that might result from tag removal
#             cleaned_filename = re.sub(r'\s+', ' ', cleaned_filename).strip()

#         if await add_name(OWNERID, cleaned_filename): # Use cleaned_filename here
#             imdb = await get_movie_details(cleaned_filename) # Use cleaned_filename for IMDb search
#             resized_poster = None

#             # IMDb থেকে ডেটা সংগ্রহ
#             title = imdb.get('title', cleaned_filename) if imdb else cleaned_filename # Use cleaned_filename as fallback
#             year = imdb.get('year', '') if imdb else ''
            
#             # Use the cleaned_title for hashtag generation
#             clean_title = re.sub(r'\s+', ' ', re.sub(r'[^a-zA-Z0-9 ]', '', title.replace("_", " ").replace("-", " ").replace(".", " "))).strip()
#             movie_name_hashtag = f"#{clean_title.replace(' ', '')}"
            
#             genres = imdb.get('genres', 'N/A') if imdb else 'N/A'
#             kind_raw = imdb.get('kind', 'FILE') if imdb else 'FILE'
            
#             genre_list = genres.split(',')
#             genre_hashtags = []
#             for genre in genre_list:
#                 clean_genre = genre.strip().lower()
#                 if clean_genre and clean_genre != 'n/a':
#                     hashtag = f"#{clean_genre.replace(' ', '_')}"
#                     genre_hashtags.append(hashtag)

#             limited_genre_hashtags = genre_hashtags[:6]
#             genres_to_display = ", ".join(limited_genre_hashtags) if limited_genre_hashtags else "N/A"

#             hashtag = f"#{kind_raw.upper().replace(' ', '_')}"

#             kolkata_tz = pytz.timezone("Asia/Kolkata")
#             now = datetime.now(kolkata_tz)
#             timestamp = now.strftime("%d %b %Y | %I:%M %p")

#             text_template = (
#                 "#𝑵𝒆𝒘_𝑭𝒊𝒍𝒆_𝑨𝒅𝒅𝒆𝒅 ✅\n\n😈 `{title} {year}` ⿻ \n\n🎭 ɢᴇɴʀᴇs : {genre_hashtags_text}\n\n📽 ғᴏʀᴍᴀᴛ: {quality}\n🔊 ᴀᴜᴅɪᴏ: {language}\n\n{hashtag}\n\n𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝖡𝗒 - @Hell_king_69_Bot\n\n🕒 {timestamp}\n\n#️⃣ {movie_name_hashtag}\n\n<blockquote>ᴄᴏᴘʏ ᴛʜᴇ ɴᴀᴍᴇ ᴀɴᴅ ᴄʟɪᴄᴋ ᴏɴ <b>ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ</b>\nʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴘᴇꜱᴛ ᴛʜᴇ ɴᴀᴍᴇ ᴀᴛ ɢʀᴏᴜᴘ</blockquote>")
            
#             text = text_template.format(
#                 title=title,
#                 year=year,
#                 genre_hashtags_text=genres_to_display,
#                 quality=quality,
#                 language=language,
#                 hashtag=hashtag,
#                 timestamp=timestamp,
#                 movie_name_hashtag=movie_name_hashtag
#             )

#             if imdb:
#                 poster_url = imdb.get('poster_url')
#                 if poster_url:
#                     resized_poster = await fetch_image(poster_url)

#             # Ensure this `filenames` variable (which is now `cleaned_filename` for IMDb)
#             # is used consistently if it's meant to be the basis for search
#             # For the button, it might be better to use the `title` from IMDb if available,
#             # or the `cleaned_filename` if IMDb didn't return a title.
#             btn = [[InlineKeyboardButton('🔍 𝕊𝕖𝕒𝕣𝕔𝕙 ℍ𝕖𝕣𝕖 🔍', url="https://t.me/The_hell_king_movie_group")]]

#             if resized_poster:
#                 await bot.send_photo(chat_id=DEENDAYAL_MOVIE_UPDATE_CHANNEL, photo=resized_poster, caption=text, reply_markup=InlineKeyboardMarkup(btn))
#             else:
#                 await bot.send_message(chat_id=DEENDAYAL_MOVIE_UPDATE_CHANNEL, text=text, reply_markup=InlineKeyboardMarkup(btn))

#     except Exception as e:
#         logger.error(f"Error in send_msg: {e}")


# async def get_qualities(text, qualities: list):
#     """Get all Quality from text"""
#     quality = []
#     for q in qualities:
#         if q in text:
#             quality.append(q)
#     return ", ".join(quality) if quality else None
