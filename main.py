# -*- coding: utf-8 -*-
"""
The script monitors a set of Twitter accounts and collects the latest posts. The new posts are consolidated in a CSV file and stored within AWS S3 storage.
Currently, for the CS-AWARE project, we started monitoring the accounts listed in users.json and executed this scrip every 8 hours.
This solution uses tweepy, an easy-to-use Python library for accessing the Twitter API, that requires a credential set sd in credential.json.
Finally, the code is written for Python3, anyhow it could be easily adapted for Python2.

@author: Matteo Bregonzio
"""

import tweepy
import csv
import json
from tweepy import OAuthHandler
import os
import glob
import pandas as pd
import datetime
import boto3

today = datetime.datetime.today().date().strftime("%Y%m%d")

def load_customer_conf():
    """
    load config
    """
    with open('./credential.json') as f:
        return json.load(f)


def load_screen_names():
    """
    load users credentials
    """
    with open('./users.json') as f:
        return json.load(f)


def main():
    credential = load_customer_conf()
    user_to_follow = load_screen_names()['user_to_follow']
    df = pd.DataFrame()

    user = list(credential)[0]
    consumer_key = credential[user]['consumer_key']
    consumer_secret = credential[user]['consumer_secret']
    access_token = credential[user]['access_token']
    access_secret = credential[user]['access_secret']

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)

    for screen_name in user_to_follow:

        statuses = api.user_timeline(screen_name=screen_name, count=200)
        col0 = [statuses[i].user.name for i in range(len(statuses))]
        col1 = [statuses[i].created_at for i in range(len(statuses))]
        col2 = [statuses[i].text for i in range(len(statuses))]
        col3 = [statuses[i]._json for i in range(len(statuses))]
        
        df=df.append(pd.DataFrame({"username":col0, "date":col1, "text":col2, "json":col3 }))
        df = df[df['date'].dt.date == pd.to_datetime(today).date()]
    try:
        old_df = pd.read_csv("output_{}.csv".format(today))
    except:
        print("initialize new file of the day")
        old_df = pd.DataFrame()

    new_df = old_df.append(df)
    new_df.drop_duplicates(['username', 'date'], inplace=True)
    new_df["text"] = new_df["text"].apply(lambda x: x.encode("utf-8"))
    new_df.to_csv("output_{}.csv".format(today), index=False, quoting = csv.QUOTE_ALL)
    file_to_write = "output_{}.csv".format(today) 
    print(file_to_write)
    year = today[:4]
    month = today[4:6]
    day = today[6:8] 
    output_filename = str(year) + "/" +  str(month) + "/" + str(day) + "/" + "TWITTER/" +  file_to_write
    print(output_filename)

    # Create connection and write file in Amazon S3
    with open(file_to_write, "rb") as f:
        s3 = boto3.resource('s3')
        s3.Object("cs-aware-data-collection", output_filename).upload_fileobj(f)

    to_remove = glob.glob('output_*.csv')
    for filename in to_remove:
        os.remove(filename)

    return

if __name__ == "__main__":
    main()
