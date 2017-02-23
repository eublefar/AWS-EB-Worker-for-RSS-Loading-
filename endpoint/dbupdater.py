
import psycopg2
import os
import feedparser as fp
import dateutil.parser as parser
import time
from datetime import datetime

try:
    if('RDS_DB_NAME' in os.environ.keys()):
        db = psycopg2.connect("dbname='" + os.environ['RDS_DB_NAME'] +
                              "' user='" + os.environ['RDS_USERNAME'] +
                              "' host='" + os.environ['RDS_HOSTNAME'] +
                              "' password='" + os.environ['RDS_PASSWORD'] + "'")
    else:
        db = psycopg2.connect("dbname='" + 'ebdb' +
                              "' user='" + 'PUT USER HERE' +
                              "' host='" + 'PUT HOST HERE' +
                              "' password='" + 'PUT PASSWORD HERE' + "'")
except:
    print("I am unable to connect to the database " + "dbname='" + os.environ['RDS_DB_NAME'] +
          "' user='" + os.environ['RDS_USERNAME'] +
          "' host='" + os.environ['RDS_HOSTNAME'] +
          "' password='" + os.environ['RDS_PASSWORD'] + "'")


def get_entries(feeds_to_parse=None):
    cur_articles_read = db.cursor()
    cur_write = db.cursor()
    cur_sources_read = db.cursor()
    cur_articles_read = db.cursor()
    if(feeds_to_parse is not None):
        cur_sources_read.execute('''SELECT id, source_address, modified FROM articles_source WHERE source_address = %s%s%s'''%("'",feeds_to_parse,"'"))
    else:
        cur_sources_read.execute('''SELECT id, source_address, modified FROM articles_source''')

    entries = []
    for feed_rec in cur_sources_read:
        if(feed_rec[2] is None):
            feed = fp.parse(feed_rec[1])
            if 'modified' in feed.keys():
                cur_write.execute("UPDATE articles_source SET modified = %s WHERE id = %s", (feed_rec[2], feed_rec[0]))
                db.commit()
        else:
            feed = fp.parse(feed_rec[1], modified=feed_rec[2])
        if 'status' not in feed.keys() or feed.status == 200:

            if 'modified' in feed.keys():
                cur_write.execute("UPDATE articles_source SET modified = %s WHERE id = %s", (feed_rec[2], feed_rec[0]))
                db.commit()

            cur_articles_read.execute("""SELECT article_address FROM articles_article
                                       WHERE date(pub_date) > current_date - INTERVAL '7 days'""")
            old_links = cur_articles_read.fetchall()
            for entry in feed.entries:
                if (len([tup for tup in old_links if tup[0] == entry.link]) == 0):
                    if 'published' not in entry.keys():
                        entry['published'] = datetime.now()
                    entry['source_id'] = feed_rec[0]
                    entries.append(entry)
        feed=None
    return entries


def push_entries(entries):
    if len(entries)>0:
        entries_str = ["(DEFAULT, '{title}', '{link}', '{pub_date}', FALSE, {category_id}, {event_id}, {source_id})"
                       .format(title=entry.title.replace("'", "''"), link=entry.link,
                               pub_date=str(entry.published), category_id=str(entry.category_id),
                               event_id=str(entry.event_id), source_id=str(entry.source_id))
                       for entry in entries]
        cur = db.cursor()
        entries_str = ','.join(entries_str)
        cur.execute('INSERT INTO articles_article VALUES ' + entries_str + ';')
        db.commit()
