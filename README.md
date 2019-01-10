# WP3-data-collection-twitter

The script monitors a set of Twitter accounts and collects the latest posts. The new posts are consolidated in a CSV file and stored within AWS S3 storage.
Currently, for the CS-AWARE project, we started monitoring the accounts listed in users.json and executed this scrip every 8 hours.
This solution uses tweepy, an easy-to-use Python library for accessing the Twitter API, that requires a credential set sd in credential.json.
Finally, the code is written for Python3, anyhow it could be easily adapted for Python2.

### How to install dependencies and run the script

```console
git clone https://github.com/cs-aware/WP3-data-collection-twitter.git
sudo python3 -m pip install -r requirements.txt 
python3 main.py
```

`This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 740723. This communication reflects only the author's view and the Commission is not responsible for any use that may be made of the information it contains.
`
