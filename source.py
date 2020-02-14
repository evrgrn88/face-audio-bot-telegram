import requests
import os
import re
import time

import telebot # pip install telebot
import ffmpeg # pip install ffmpeg-python (ffmpeg.exe needs to be downloaded separatedly, placed in the script folder)
import glob2 # pip install glob2
import psycopg2 # pip install psycopg2
import cv2 # pip install opencv-utils opencv-python

# Bot initialization
apiKey = "969180095:AAFB0CAUMPZtcYiL91JrZtiqLRJwiPgDNII"
bot = telebot.TeleBot(apiKey)

# Setting up filename patterns
imageNamePattern = "image_"
audioNamePattern = "audio_message_"
tempName = "temp"

# Setting up the database connection
conn = psycopg2.connect(dbname="fabt_db", user="postgres", password="1", host="localhost")

# Searches for existing files, returns digit for a new filename
def fileCount(pattern, extension):
  checkFiles = glob2.glob("*." + str(extension)) # Makes a list from existing files for an easier search
  max = 0
  for name in checkFiles:
    findFile = re.search(str(pattern) + "(\d*)", name) # Searches for existing names
    num = 0
    if findFile is not None:
      num = int(findFile.group(1))
    if num > max:
      max = num
  return max + 1

# Checks for an existing faces on the photo, using the Haar features method
def checkFace(img):
  gray = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2GRAY) # Converts to grayscale
  faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") # Selects the frontal preset
  faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3, minSize=(30, 30)) # Sets the treshold parameters
  if len(faces) > 0: return 0 # Passes zero if at least one face is recognized
  else: return 1

# Downloads the file with Telegram API
def downloadFile(fileId, fileName):
  file_info = bot.get_file(fileId)
  file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(apiKey, file_info.file_path)) # Gets the file in byte format

  with open(fileName, "wb") as f: # Writes file on the disk
    f.write(file.content)

# Converts audio file with 16 kHz sampling frequency, audio type is passed in outFile parameter along with the file name.
# ffmpeg.exe is used, located in the base directory
def convertAudio(inFile, outFile):
  (ffmpeg
    .input(inFile)
    .output(outFile, ar='16k') # Sets the sampling frequency
    .overwrite_output()
    .run(capture_stdout=True)
  )
  os.remove(inFile) # Removes temp file

# Handle the voice files
@bot.message_handler(content_types=["voice"]) # Selects the voice content type
def start_message(message):
  uid = str(message.from_user.id)
  messageTime = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(message.date)) # Converts epoch timestamp to the human-readable format
  voiceId = message.voice.file_id

  os.chdir(os.path.join("media", "Audio")) # Sets a folder to save the files
  downloadFile(voiceId, tempName)
  newFileName = uid + "_" + audioNamePattern + str(fileCount(uid + "_" + audioNamePattern, "wav")) + ".wav" # Creates a new file name
  os.chdir("../..")
  convertAudio(os.path.join("media", "Audio", tempName), os.path.join("media", "Audio", newFileName)) # Going back to the base directory is needed because the separate ffmpeg codec file is used in virtualenv

  # Saves the data to a database
  cursor = conn.cursor()
  cursor.execute("INSERT INTO main (uid, date_time, audio_name) VALUES (%s, %s, %s)", (uid, messageTime, newFileName))
  conn.commit()
  cursor.close()

  bot.send_message(message.chat.id, "Аудиозапись преобразована. Файл сохранен как " + newFileName) # Sends info message to the chat

# Similar header is used for the photo processing function
@bot.message_handler(content_types=["photo"])
def start_message(message):
  uid = str(message.from_user.id)
  messageTime = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(message.date))
  imgId = message.photo[-1].file_id

  os.chdir(os.path.join("media", "Photo"))
  downloadFile(imgId, tempName)

  if checkFace(tempName) == 0: # Recognizes the photo, processes the response
    newFileName = uid + "_" + imageNamePattern + str(fileCount(uid + "_" + imageNamePattern, "jpg")) + ".jpg"
    os.rename(tempName, newFileName) # If the face is found, renames the temp file 

    cursor = conn.cursor()
    cursor.execute("INSERT INTO main (uid, date_time, photo_name) VALUES (%s, %s, %s)", (uid, messageTime, newFileName))
    conn.commit()
    cursor.close()

    bot.send_message(message.chat.id, "Лицо обнаружено. Файл сохранен как " + newFileName)

  else: # If no face is present, deletes the temp file
    os.remove(tempName)
    bot.send_message(message.chat.id, "Лицо не обнаружено.")

  os.chdir("../..")

bot.polling() # Constantly waiting for the new messages