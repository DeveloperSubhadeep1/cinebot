# import logging
# import asyncio
# from pyrogram import Client, filters, enums
# from pyrogram.errors import FloodWait
# from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
# from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL
# from database.ia_filterdb import save_file
# from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from utils import temp
# import re

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# lock = asyncio.Lock()


# # Helper function to generate a progress bar string
# def progress_bar(current, total, bar_length=10):
#     """Generates a text-based progress bar."""
#     if total <= 0:
#         return "`[░░░░░░░░░░]` **0.00%**"

#     # Calculate percentage and determine filled length
#     percent = (current / total)
#     filled_length = int(bar_length * percent)
    
#     # Create the bar string using Unicode block characters
#     bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
#     # Return formatted string with percentage
#     return f"`[{bar}]` **{percent:.2%}**"


# @Client.on_callback_query(filters.regex(r'^index'))
# async def index_files(bot, query):
#     if query.data.startswith('index_cancel'):
#         temp.CANCEL = True
#         return await query.answer("Cancelling Indexing")
        
#     _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    
#     if raju == 'reject':
#         await query.message.delete()
#         await bot.send_message(int(from_user),
#                                f'Your Submission for indexing {chat} has been declined by our moderators.',
#                                reply_to_message_id=int(lst_msg_id))
#         return

#     if lock.locked():
#         return await query.answer('Wait until previous process complete.', show_alert=True)
        
#     msg = query.message

#     await query.answer('Processing...⏳', show_alert=True)
    
#     # Send acceptance message to the user who requested indexing
#     if int(from_user) not in ADMINS:
#         await bot.send_message(int(from_user),
#                                f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
#                                reply_to_message_id=int(lst_msg_id))
                               
#     await msg.edit(
#         "Starting Indexing",
#         reply_markup=InlineKeyboardMarkup(
#             [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
#         )
#     )
    
#     try:
#         # Attempt to convert chat ID to integer for private channels/groups (e.g., -100xxxxxxxx)
#         chat = int(chat)
#     except ValueError:
#         # If it's a username (string), keep it as is
#         chat = chat
        
#     await index_files_to_db(int(lst_msg_id), chat, msg, bot)


# @Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
# async def send_for_index(bot, message):
#     if message.text:
#         regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
#         match = regex.match(message.text)
#         if not match:
#             return await message.reply('Invalid link')
#         chat_id = match.group(4)
#         last_msg_id = int(match.group(5))
#         if chat_id.isnumeric():
#             chat_id  = int(("-100" + chat_id))
#     elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
#         last_msg_id = message.forward_from_message_id
#         chat_id = message.forward_from_chat.username or message.forward_from_chat.id
#     else:
#         return
        
#     try:
#         await bot.get_chat(chat_id)
#     except ChannelInvalid:
#         return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
#     except (UsernameInvalid, UsernameNotModified):
#         return await message.reply('Invalid Link specified.')
#     except Exception as e:
#         logger.exception(e)
#         return await message.reply(f'Errors - {e}')
        
#     try:
#         k = await bot.get_messages(chat_id, last_msg_id)
#     except:
#         return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
        
#     if k.empty:
#         return await message.reply('This may be group and iam not a admin of the group.')

#     if message.from_user.id in ADMINS:
#         buttons = [
#             [InlineKeyboardButton('Yes', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
#             [InlineKeyboardButton('Close', callback_data='close_data')]
#         ]
#         reply_markup = InlineKeyboardMarkup(buttons)
#         return await message.reply(
#             f'Do you Want To Index This Channel/ Group ?\n\nChat ID/ Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\n\nɴᴇᴇᴅ sᴇᴛsᴋɪᴘ 👉🏻 /setskip',
#             reply_markup=reply_markup)

#     if type(chat_id) is int:
#         try:
#             link = (await bot.create_chat_invite_link(chat_id)).invite_link
#         except ChatAdminRequired:
#             return await message.reply('Make sure I am an admin in the chat and have permission to invite users.')
#     else:
#         link = f"@{message.forward_from_chat.username}"
        
#     buttons = [
#         [InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
#         [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
#     ]
#     reply_markup = InlineKeyboardMarkup(buttons)
    
#     await bot.send_message(LOG_CHANNEL,
#                            f'#IndexRequest\n\nBy : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID/ Username - <code> {chat_id}</code>\nLast Message ID - <code>{last_msg_id}</code>\nInviteLink - {link}',
#                            reply_markup=reply_markup)
                           
#     await message.reply('ThankYou For the Contribution, Wait For My Moderators to verify the files.')


# @Client.on_message(filters.command('setskip') & filters.user(ADMINS))
# async def set_skip_number(bot, message):
#     if ' ' in message.text:
#         _, skip = message.text.split(" ")
#         try:
#             skip = int(skip)
#         except:
#             return await message.reply("Skip number should be an integer.")
#         await message.reply(f"Successfully set SKIP number as {skip}")
#         temp.CURRENT = int(skip)
#     else:
#         await message.reply("Give me a skip number")


# async def index_files_to_db(lst_msg_id, chat, msg, bot):
#     total_files = 0
#     duplicate = 0
#     errors = 0
#     deleted = 0
#     no_media = 0
#     unsupported = 0
    
#     # Calculate the total messages we expect to iterate over
#     initial_skip = temp.CURRENT
#     total_messages_to_process = lst_msg_id - initial_skip
    
#     if total_messages_to_process <= 0:
#         return await msg.edit(f"Skipping set to message ID **{initial_skip}** which is $\\ge$ to the last message ID **{lst_msg_id}** in the link. No new messages to index.")

#     async with lock:
#         try:
#             current = initial_skip
#             messages_processed_count = 0
#             temp.CANCEL = False
            
#             async for message in bot.iter_messages(chat, lst_msg_id, temp.CURRENT):
#                 # Check for cancel flag
#                 if temp.CANCEL:
#                     progress_text = progress_bar(messages_processed_count, total_messages_to_process)
#                     await msg.edit(
#                         f"Successfully Cancelled!!\n\n"
#                         f"Progress at cancellation: {progress_text}\n"
#                         f"Saved <code>{total_files}</code> files to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>"
#                     )
#                     break

#                 # Increment counters
#                 current += 1
#                 messages_processed_count = current - initial_skip
                
#                 # Update status message every 80 messages (or on the first message)
#                 if messages_processed_count % 80 == 0 or messages_processed_count == 1:
#                     progress_text = progress_bar(messages_processed_count, total_messages_to_process)
#                     can = [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
#                     reply = InlineKeyboardMarkup(can)
#                     await msg.edit_text(
#                         text=f"**Indexing Progress**\n\n{progress_text}\n\n"
#                              f"Total messages to process: `{total_messages_to_process}`\n"
#                              f"Messages processed: `{messages_processed_count}`\n"
#                              f"Files saved: `{total_files}`\n"
#                              f"Duplicate files skipped: `{duplicate}`\n"
#                              f"Deleted messages skipped: `{deleted}`\n"
#                              f"Non-Media messages skipped: `{no_media + unsupported}` (Unsupported Media: `{unsupported}`)\n"
#                              f"Errors: `{errors}`",
#                         reply_markup=reply
#                     )
                    
#                 # Message Processing Logic
#                 if message.empty:
#                     deleted += 1
#                     continue
#                 elif not message.media:
#                     no_media += 1
#                     continue
#                 elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
#                     unsupported += 1
#                     continue
                    
#                 media = getattr(message, message.media.value, None)
#                 if not media:
#                     unsupported += 1
#                     continue
                    
#                 media.file_type = message.media.value
#                 media.caption = message.caption
                
#                 aynav, vnay = await save_file(bot, media)
                
#                 if aynav:
#                     total_files += 1
#                 elif vnay == 0:
#                     duplicate += 1
#                 elif vnay == 2:
#                     errors += 1
                    
#         except FloodWait as e:
#              logger.warning(f"FloodWait: Sleeping for {e.value} seconds...")
#              await msg.edit(f"⚠️ **Rate Limit Hit!** ⚠️\n\nSleeping for **{e.value}** seconds to comply with Telegram limits. Indexing will resume automatically.")
#              await asyncio.sleep(e.value)
#              await index_files_to_db(lst_msg_id, chat, msg, bot) # Resume indexing

#         except Exception as e:
#             logger.exception(e)
#             await msg.edit(f'Error: {e}')
            
#         else:
#             # Final update if the loop completes without cancellation
#             await msg.edit(
#                 f'**Indexing Complete!** 🎉\n\n'
#                 f"Total messages processed: `{total_messages_to_process}`\n"
#                 f'Successfully saved <code>{total_files}</code> to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>'
#             )










































import logging
import time # Added for time tracking and ETA
import re
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time # Added get_readable_time
from math import ceil # Added for batch calculation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


# Helper function to generate an emoji-based progress bar string (Updated from original)
def get_progress_bar(percent, length=17):
    """Creates an emoji-based progress bar."""
    # Ensure percent is between 0 and 100
    percent = max(0, min(100, percent))
    
    filled = int(length * percent / 100)
    unfilled = length - filled
    return '█' * filled + '░' * unfilled


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing")
        
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been declined by our moderators.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Wait until previous process complete.', show_alert=True)
        
    msg = query.message

    await query.answer('Processing...⏳', show_alert=True)
    
    # Send acceptance message to the user who requested indexing
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
                               reply_to_message_id=int(lst_msg_id))
                               
    await msg.edit(
        "Starting Indexing",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
        )
    )
    
    try:
        # Attempt to convert chat ID to integer for private channels/groups (e.g., -100xxxxxxxx)
        chat = int(chat)
    except ValueError:
        # If it's a username (string), keep it as is
        chat = chat
        
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
        
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')
        
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
        
    if k.empty:
        return await message.reply('This may be group and i am not a admin of the group.')

    if message.from_user.id in ADMINS:
        buttons = [
            [InlineKeyboardButton('Yes', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Close', callback_data='close_data')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Do you Want To Index This Channel/ Group ?\n\nChat ID/ Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\n\nɴᴇᴇᴅ sᴇᴛsᴋɪᴘ 👉🏻 /setskip',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure I am an admin in the chat and have permission to invite users.')
    else:
        link = f"@{message.forward_from_chat.username}"
        
    buttons = [
        [InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
        [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await bot.send_message(LOG_CHANNEL,
                           f'#IndexRequest\n\nBy : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID/ Username - <code> {chat_id}</code>\nLast Message ID - <code>{last_msg_id}</code>\nInviteLink - {link}',
                           reply_markup=reply_markup)
                           
    await message.reply('ThankYou For the Contribution, Wait For My Moderators to verify the files.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    BATCH_SIZE = 200 # New: Define batch size
    start_time = time.time()
    
    # New: Calculate total messages to fetch based on current skip value
    initial_skip = temp.CURRENT
    total_fetch = lst_msg_id - initial_skip
    
    if total_fetch <= 0:
        return await msg.edit(f"Skipping set to message ID **{initial_skip}** which is $\\ge$ to the last message ID **{lst_msg_id}** in the link. No new messages to index.")

    async with lock:
        try:
            current = initial_skip
            temp.CANCEL = False
            
            # New: Calculate total batches
            batches = ceil(total_fetch / BATCH_SIZE)
            batch_times = []
            
            # Initial Status Message (New metrics)
            await msg.edit(
                f"📊 Indexing Starting......\n"
                f"💬 Total Messages to fetch: <code>{total_fetch}</code>\n"
                f"📦 Batch Size: <code>{BATCH_SIZE}</code>\n"
                f"⏰ Elapsed: <code>{get_readable_time(time.time() - start_time)}</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
            )
            
            # Main Batching Loop
            for batch in range(batches):
                if temp.CANCEL:
                    break
                    
                batch_start = time.time()
                
                # Determine message IDs for the current batch
                start_id = current + 1
                end_id = min(current + BATCH_SIZE, lst_msg_id)
                message_ids = range(start_id, end_id + 1)
                
                # New: Robust FloodWait Handling and Batch Fetch
                try:
                    # Fetch messages in a batch
                    messages = await bot.get_messages(chat, list(message_ids))
                    if not isinstance(messages, list):
                         messages = [messages]
                         
                except FloodWait as e:
                    logger.warning(f"FloodWait: Sleeping for {e.value} seconds...")
                    await msg.edit(f"⚠️ **Rate Limit Hit!** ⚠️\n\nSleeping for **{e.value}** seconds to comply with Telegram limits. Indexing will resume on batch {batch + 1}/{batches} after the pause.")
                    await asyncio.sleep(e.value)
                    # Use 'continue' to re-run the current batch
                    continue 
                    
                except Exception as e:
                    # Handle general exceptions during message fetching
                    logger.warning(f"Error fetching batch {batch + 1}: {e}")
                    errors += len(message_ids)
                    current = end_id
                    continue
                    
                save_tasks = []
                batch_files_found = 0
                
                # Prepare save tasks for concurrent execution
                for message in messages:
                    # Update 'current' position *before* processing for accurate reporting
                    current += 1 
                    
                    try:
                        if message.empty:
                            deleted += 1
                            continue
                        elif not message.media:
                            no_media += 1
                            continue
                        elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                            unsupported += 1
                            continue
                            
                        media = getattr(message, message.media.value, None)
                        if not media:
                            unsupported += 1
                            continue
                            
                        media.file_type = message.media.value
                        media.caption = message.caption
                        
                        # save_file is expected to be an async database call
                        save_tasks.append(save_file(bot, media)) 
                        batch_files_found += 1
                        
                    except Exception:
                        errors += 1
                        continue
                        
                # New: Concurrently execute all database save tasks
                results = await asyncio.gather(*save_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        errors += 1
                    else:
                        aynav, vnay = result # Expected tuple (Success_bool, Status_code)
                        if aynav:
                            total_files += 1
                        elif vnay == 0:
                            duplicate += 1
                        elif vnay == 2:
                            errors += 1

                # New: Calculate metrics for status update
                batch_time = time.time() - batch_start
                batch_times.append(batch_time)
                elapsed = time.time() - start_time
                progress_so_far = current - initial_skip
                percentage = (progress_so_far / total_fetch) * 100
                
                # Calculate ETA based on average time taken per BATCH_SIZE
                avg_batch_time = sum(batch_times) / len(batch_times) if batch_times else 1
                remaining_batches = batches - (batch + 1)
                eta = remaining_batches * avg_batch_time
                
                progress_bar_text = get_progress_bar(int(percentage))
                
                # Update status message after each batch
                can = [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
                reply = InlineKeyboardMarkup(can)
                await msg.edit_text(
                    text=f"📊 **Indexing Progress** 📦 Batch `{batch + 1}/{batches}`\n\n"
                         f"{progress_bar_text} <code>{percentage:.1f}%</code>\n"
                         f"----------------------------------------------\n"
                         f"💬 Total Messages to fetch: <code>{total_fetch}</code>\n"
                         f"➡️ Messages Processed: <code>{progress_so_far}</code>\n"
                         f"💾 Files Saved: <code>{total_files}</code>\n"
                         f"🚫 Duplicates Skipped: <code>{duplicate}</code>\n"
                         f"🗑️ Deleted/Non-Media: <code>{deleted + no_media + unsupported}</code>\n"
                         f"❌ Errors: <code>{errors}</code>\n"
                         f"⏱️ Elapsed: <code>{get_readable_time(elapsed)}</code>\n"
                         f"⏰ ETA: <code>{get_readable_time(eta)}</code>",
                    reply_markup=reply
                )
            
            # Ensure temp.CURRENT is updated if index completes without cancellation
            temp.CURRENT = current
            
        except Exception as e:
            logger.exception(e)
            await msg.edit(f'Error: {e}')
            
        else:
            # Final update if the loop completes without cancellation
            elapsed = time.time() - start_time
            await msg.edit(
                f'**Indexing Complete!** 🎉\n\n'
                f"Total messages to fetch: `{total_fetch}`\n"
                f'Successfully saved <code>{total_files}</code> to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>\n'
                f"⏱️ Total Time: <code>{get_readable_time(elapsed)}</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Close', callback_data='close_data')]])
            )
