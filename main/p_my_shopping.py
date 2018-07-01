import json
from escpos import *
import boto3
from boto3.session import Session
from boto3.dynamodb.conditions import Key, Attr
from PIL import Image, ImageDraw, ImageFont
import time
import random

config = {}
MODE = "layout" # or "prod"

def read_config():
    f = open("config.json", 'r')
    global config
    config = json.load(f)

def access_to_dynamodb():
    accesskey = config["access_key"]
    secretkey = config["secret_key"]
    region    = config["region"]

    session = Session(aws_access_key_id=accesskey, aws_secret_access_key=secretkey, region_name=region)
    dynamodb = session.resource('dynamodb')
    return dynamodb

def get_all(dynamodb):
    table    = dynamodb.Table('puzzle_meter')
    response = table.scan()
    records  = response["Items"]
    print(records)
    return records

def imgid_to_image(records):
    img_height = config["receipt_base_height"] + len(records) * config["text_height"]
    img_width  = config["receipt_base_width"]
    img        = Image.new('RGB', (img_width, img_height), color = (255, 255, 255))
    draw       = ImageDraw.Draw(img)
    fontname   = '/Library/Fonts/Arial Unicode.ttf'
    font       = ImageFont.truetype(fontname, 30)
    imgid      = str(random.randrange(10**10,10**11))

    y = config["text_height"]
    for item in records:
        name       = item['name']
        price      = item['price']
        item_name  = u"%s" % name
        item_price = str(price) + u"円"

        draw.text((10, y), item_name, fill = (0,0,0), font = font)
        draw.text((config["text_right_axis"], y), item_price, fill = (0,0,0), font = font)

        y += config["text_height"]

    saved_name = '%s.png' % imgid
    img.save(saved_name)
    return saved_name

def printout(img_name):
    usb = printer.Serial("/dev/tty.P58A_F-DevB")
    usb.image(config["logo_path"])
    time.sleep(5.0)
    usb.image(img_name)
    usb.cut()
#     usb.text("test\n")

def main():
    read_config()
    records = {}
    if (MODE == "prod") :
        dynamodb = access_to_dynamodb()
        records  = get_all(dynamodb)
    else :
        print("modify layout")
        f = open("response.json", 'r')
        records = json.load(f)

    saved_name = imgid_to_image(records)
    # print(saved_name)
    printout(saved_name)

if __name__=='__main__':
    main()