from django.test import TestCase
import psycopg2
import os

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# Create your tests here.

class UpdaterTestCase(TestCase):
#POSTGRESQL database must be running for this one
    def setUp(self):
        os.environ['RDS_DB_NAME'] = 'test'
        os.environ['RDS_USERNAME'] = 'postgres'
        os.environ['RDS_HOSTNAME'] = 'localhost'
        os.environ['RDS_PASSWORD'] = 'password'
        try:
            self.db = psycopg2.connect(database='postgres', user=os.environ['RDS_USERNAME'], host=os.environ['RDS_HOSTNAME'], password=os.environ['RDS_PASSWORD'])
        except psycopg2.Error as e:
            print("I am unable to connect to the database1")
            print(e)
        self.db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = self.db.cursor()
        cur.execute('DROP DATABASE IF EXISTS %s; ' % (os.environ['RDS_DB_NAME']))
        self.db.commit()
        cur.execute('CREATE DATABASE %s;' % (os.environ['RDS_DB_NAME']))
        self.db.commit()
        self.db.close()
        try:
            self.db = psycopg2.connect(database=os.environ['RDS_DB_NAME'], user=os.environ['RDS_USERNAME'], host=os.environ['RDS_HOSTNAME'], password=os.environ['RDS_PASSWORD'])
        except psycopg2.Error as e:
            print("I am unable to connect to the database1")
            print(e)
        cur_test = self.db.cursor()
        cur_test.execute('''CREATE SEQUENCE IF NOT EXISTS articles_article_id_seq
                        INCREMENT 1
                        START 4
                        MINVALUE 1
                        MAXVALUE 9223372036854775807
                        CACHE 1;''')
        cur_test.execute('''CREATE SEQUENCE IF NOT EXISTS articles_event_id_seq
                        INCREMENT 1
                        START 4
                        MINVALUE 1
                        MAXVALUE 9223372036854775807
                        CACHE 1;''')

        cur_test.execute('''CREATE TABLE IF NOT EXISTS   articles_source(id integer NOT NULL ,
                                                    source_name character varying(600) NOT NULL,
                                                    source_address character varying(600) NOT NULL,
                                                    is_public boolean NOT NULL,
                                                    modified TIMESTAMP,
                                                    CONSTRAINT articles_source_pkey PRIMARY KEY (id));''')

        cur_test.execute('''CREATE TABLE IF NOT EXISTS articles_article(id integer NOT NULL DEFAULT nextval('articles_article_id_seq'::regclass),
                                                    article_name character varying(600) NOT NULL,
                                                    article_address character varying(600) NOT NULL,
                                                    pub_date timestamp with time zone NOT NULL,
                                                    is_public boolean NOT NULL,
                                                    article_category_id integer NOT NULL,
                                                    article_event_id integer NOT NULL,
                                                    source_id integer NOT NULL,
                                                    CONSTRAINT articles_article_pkey PRIMARY KEY (id));''')
        cur_test.execute('''CREATE TABLE IF NOT EXISTS articles_event(
                                                    id integer NOT NULL DEFAULT nextval('articles_event_id_seq'::regclass),
                                                    event_name character varying(200) NOT NULL,
                                                    category_id integer NOT NULL)''')
        cur_test.execute('TRUNCATE articles_source;')
        cur_test.execute('TRUNCATE articles_article;')
        cur_test.execute('TRUNCATE articles_event;')

        print ("is file : " + str(os.path.isfile('endpoint\\tests\\xml_front-10.xml')) )

        cur_test.execute('''INSERT INTO articles_source(id, source_name, source_address, is_public)
                        VALUES (1 ,'test1', 'endpoint\\tests\\xml_front-10.xml', TRUE);''')
        cur_test.execute('''INSERT INTO articles_source(id, source_name, source_address, is_public)
                        VALUES (2 ,'test2', 'https://www.reddit.com/r/askscience+science/.rss', TRUE);''')
        cur_test.execute('SELECT * FROM articles_source;')
        print(cur_test.fetchone())
        self.db.commit()



    def test_update_all_feeds(self):
        from django.test import Client
        c = Client()
        response = c.post('/endpoint/update/')
        self.assertTrue(response=200)
        cur = self.db.cursor()
        cur.execute("SELECT * FROM articles_article AS a, articles_source AS s  WHERE a.source_id = s.id AND s.source_name = 'test1';")
        self.assertFalse(cur.fetchone() is None, 'no articles from the local file feed')
        cur.execute("SELECT * FROM articles_article AS a, articles_source AS s  WHERE a.source_id = s.id AND s.source_name = 'test2';")
        self.assertFalse(cur.fetchone() is None, 'no articles from the  test site feed')

    def test_update_one_feed(self):
        from django.test import Client
        c = Client()
        response = c.post('/endpoint/update/',{'feed':'endpoint\\tests\\xml_front-10.xml'})
        self.assertTrue(response=200)

        cur = self.db.cursor()
        cur.execute("SELECT * FROM articles_article AS a, articles_source AS s  WHERE a.source_id = s.id AND s.source_name = 'test1';")
        self.assertFalse(cur.fetchone() is None, 'no articles from the local file feed')
