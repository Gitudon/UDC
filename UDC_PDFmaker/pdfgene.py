from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import chromedriver_binary
import shutil
import time
import requests
import re
import os
import cv2
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4, portrait
import glob

margin = 0
margin_tp = 15
pdf_name="artifact.pdf"
pics_folder_path = './pics'
CARDHIGHT = 88
CARDWIDTH = 63
card_h = CARDHIGHT
card_w = CARDWIDTH

def height(i):
  n = i // 3 + 1
  return 297 - margin_tp - (n * (card_h + margin))


def width(i):
  n = i % 3
  return margin_tp + (n * card_w)

def getHFromW(w):
  return CARDWIDTH * w / CARDHIGHT


def getWFromH(h):
  return CARDHIGHT * h / CARDWIDTH

def crop(image): #引数は画像の相対パス
  # 画像の読み込み
  img = cv2.imread(image)
  # Grayscale に変換
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  # 色空間を二値化
  img2 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
  # 輪郭を抽出
  contours = cv2.findContours(img2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
  # 輪郭の座標をリストに代入していく
  x1 = [] #x座標の最小値
  y1 = [] #y座標の最小値
  x2 = [] #x座標の最大値
  y2 = [] #y座標の最大値
  for i in range(1, len(contours)):# i = 1 は画像全体の外枠になるのでカウントに入れない
      ret = cv2.boundingRect(contours[i])
      x1.append(ret[0])
      y1.append(ret[1])
      x2.append(ret[0] + ret[2])
      y2.append(ret[1] + ret[3])
  # 輪郭の一番外枠を切り抜き
  x1_min = min(x1)
  y1_min = min(y1)
  x2_max = max(x2)
  y2_max = max(y2)
  img = img[y1_min:y2_max, x1_min:x2_max]
  return img

def pdfgene(url):
  #picsフォルダの準備
  print('start')
  if not os.path.exists(pics_folder_path):
    os.mkdir(pics_folder_path)
  else:
    shutil.rmtree(pics_folder_path)
    os.mkdir(pics_folder_path)
  service = Service('/usr/bin/chromedriver')
  chrome_options = Options()
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-proxy-server')
  driver = webdriver.Chrome(service=service, options=chrome_options)
  driver.get(url)
  time.sleep(0.5)
  imgs = driver.find_elements(By.CLASS_NAME, 'item8_img')
  srcs = []
  for img in imgs:
    if re.match("chojigen_.", img.get_attribute("alt")):
      for i in range(4):
        srcs.append(img.get_attribute("src").split("_")[0] + "_" + str(i+1) + ".jpg")
    else:
      srcs.append(img.get_attribute("src"))
  driver.quit()
  #画像のダウンロード
  count = 0
  for src in srcs:
    page = src.replace('/img/s/', '/img/')
    r = requests.get(page)
    count += 1
    img_name = "{}.jpg".format(str(count).zfill(2) + '_' + src.split("/")[7])
    image_path = pics_folder_path + '/' + img_name
    if r.status_code == 200:
      with open(image_path, "wb") as f:
        f.write(r.content)
  #pdf作成と画像追加
  page = canvas.Canvas(pdf_name, pagesize=portrait(A4))
  file_names = os.listdir(pics_folder_path)
  image_files = [
      os.path.join(pics_folder_path, file_name) for file_name in file_names
      if file_name.endswith(('.jpg', '.png', '.bmp'))
  ]
  exfiles = []
  for path in image_files:
    if re.match(".*_3\.jpg", path):
      exfiles.append(path)
      image_files.remove(path)
    if re.match(".*_4\.jpg", path):
      image_files.append(path)
      exfiles.remove(path)
  sorted_files = sorted(image_files)
  for img in sorted_files:
    cv2.imwrite(img, crop(img))
  for i in range(0, len(sorted_files), 9):
    for j in range(9):
      if i + j < len(sorted_files):
        page.drawInlineImage(sorted_files[i + j],
                             width(j) * mm,
                             height(j) * mm, card_w * mm, card_h * mm)
    page.showPage()
  page.save()
  rmpics()
  print("complete")

def rmpics():
  if (os.path.isdir(pics_folder_path)):
    shutil.rmtree(pics_folder_path)

def rmpdf():
  pdf_files = glob.glob(os.path.join('*.pdf'))
  for file in pdf_files:
      try:
          os.remove(file)
      except Exception as e:
          pass