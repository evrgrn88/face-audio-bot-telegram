import requests
import os
import re

import telebot # pip install telebot
import ffmpeg # pip install ffmpeg-python
import glob2 # pip install glob2
# import psycopg2 # pip install psycopg2
import cv2 # pip install opencv-utils, opencv-python

# Connect with database
# conn = psycopg2.connect(dbname="fabt_db", user="postgres", password="1", host="localhost")
# cursor = conn.cursor()

apiKey = "969180095:AAFB0CAUMPZtcYiL91JrZtiqLRJwiPgDNII"
bot = telebot.TeleBot(apiKey)

imageNamePattern = "image_"
audioNamePattern = "audio_message_"

def fileCount(pattern, extension):
  checkFiles = glob2.glob("*." + str(extension))
  max = 0
  for name in checkFiles:
    findFile = re.search(str(pattern) + "(\d*)", name)
    num = 0
    if findFile is not None:
      num = int(findFile.group(1))
    if num > max:
      max = num
    else:
      max
  return max + 1

def checkFace(img, newName):
  gray = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2GRAY)
  faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
  faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3, minSize=(30, 30))
  if len(faces) > 0:
    print("face recognized")
    os.rename(img, newName + str(fileCount(newName, "jpg")) + ".jpg")
  else:
    print("face not recognized")
    os.remove(img)

def downloadFile(fileId, fileName):
  file_info = bot.get_file(fileId)
  file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(apiKey, file_info.file_path))

  with open(fileName, "wb") as f:
    f.write(file.content)

def convertToWav(inFile, outFile):
  (ffmpeg
    .input(inFile)
    .output(outFile + str(fileCount(outFile, "wav")) + ".wav", ar='16k')
    .overwrite_output()
    .run(capture_stdout=True)
  )
  os.remove(inFile)

@bot.message_handler(content_types=["voice"])
def start_message(message):
  tempName = "temp.ogg"
  voiceId = message.voice.file_id
  downloadFile(voiceId, tempName)
  convertToWav(tempName, audioNamePattern)

@bot.message_handler(content_types=["photo"])
def start_message(message):
  tempName = "temp.jpg"
  imgId = message.photo[-1].file_id
  downloadFile(imgId, tempName)
  checkFace(tempName, imageNamePattern)


# uid = message.from_user.id

bot.polling()