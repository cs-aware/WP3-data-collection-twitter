# -*- coding: utf-8 -*-
"""
The script monitors a set of Twitter accounts and collects the latest posts. The new posts are consolidated in a CSV file and stored within AWS S3 storage.
Currently, for the CS-AWARE project, we started monitoring the accounts listed in users.json and executed this scrip every 8 hours.
This solution uses tweepy, an easy-to-use Python library for accessing the Twitter API, that requires a credential set sd in credential.json.
Finally, the code is written for Python3, anyhow it could be easily adapted for Python2.

@author: Matteo Bregonzio
"""

import sys
import tweepy
import csv
import json
from tweepy import OAuthHandler
import os
import glob
import pandas as pd
import datetime
from datetime import date
import boto3

from stix2 import Bundle, ObservedData, IPv4Address, UserAccount, Bundle
from stix2 import CustomObservable, properties


@CustomObservable('x-csaware-social', [
    ('source', properties.StringProperty()),
    ('title', properties.StringProperty()),
    ('text', properties.StringProperty()),
    ('subject', properties.StringProperty()),
])
class CSAwareSocial():
    pass


BUCKET_NAME = "cs-aware-data-collection"
CREDENTIALS = './credential.json'
USERS = './users.json'
PERIOD = 1  # Number of hours
POST_LIMIT = 200


today = date.today()
today_str = today.strftime("%Y%m%d_%H%M")
date_from = today - timedelta(hours=PERIOD)


def load_customer_conf():
    """Loads user credentials"""
    with open(CREDENTIALS) as f:
        return json.load(f)


def load_screen_names():
    """Loads username list"""
    with open(USERS) as f:
        return json.load(f)


def to_aws(local_filename):
    # Generate remote path
    remote_path = "%d/%02d/%02d/REDDIT/%s" % (today.year, today.month, today.day, local_filename)
    print("Uploading", remote_path)
    # Upload to AWS
    with open(local_filename, "rb") as f:
        s3 = boto3.resource('s3')
        s3.Object(BUCKET_NAME, remote_path).upload_fileobj(f)
    # Delete local copy
    os.remove(local_filename)


def main():
    #reload(sys)
    #sys.setdefaultencoding("ISO-8859-1")

    observed_data_list = []

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
        print(screen_name)
        try:
            statuses = api.user_timeline(screen_name=screen_name, count=POST_LIMIT)
        except:
            print("ERROR: user {} not found".format(screen_name))
            continue

        col0 = [statuses[i].user.name for i in range(len(statuses))]
        col1 = [statuses[i].created_at for i in range(len(statuses))]
        col2 = [statuses[i].text for i in range(len(statuses))]
        col3 = [statuses[i]._json for i in range(len(statuses))]
        
        #print(col2)
        
        df = df.append(pd.DataFrame({"username": screen_name.replace("@", ""), "name":col0, "date":col1, "text":col2, "json":col3 }))
        df = df[df['date'] >= date_from]
    try:
        old_df = pd.read_csv("output_{}.csv".format(today_str))
    except:
        print("initialize new file of the day")
        old_df = pd.DataFrame()

    new_df = old_df.append(df)
    new_df.drop_duplicates(['username', 'date'], inplace=True)
    new_df["text"] = new_df["text"].apply(lambda x: x.encode("utf-8"))
    new_df.to_csv("output_{}.csv".format(today_str), index=False, quoting = csv.QUOTE_ALL)
    file_to_write = "output_{}.csv".format(today_str) 
    print(file_to_write)

    for index, row in new_df.iterrows():
        args = {
            'source': 'twitter',
            'title': '',
            'text': row['text'],
            'subject': '',
        }
        observed_user = UserAccount(type='user-account', user_id=row['username'], display_name=row['name'])
        observed_object = CSAwareSocial(**args, allow_custom=True)
        objects = {"0": observed_user, "1": observed_object}
        observed_data = ObservedData(first_observed=row['date'], last_observed=row['date'], number_observed=1, objects=objects, allow_custom=True)
        observed_data_list.append(observed_data)

    bundle = Bundle(observed_data_list)

    stix_filename = file_to_write.replace('.csv', '.json')
    stix_output = open(stix_filename, 'w')
    stix_output.write(bundle.serialize(indent=4))
    stix_output.close()

    # Upload to AWS
    to_aws(file_to_write)
    to_aws(stix_filename)


if __name__ == "__main__":
    main()
