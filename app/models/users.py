from app import mongo
from mongoengine import Document, StringField, IntField

class User(mongo.Document):
    meta = {'collection': 'users'}
    github_oauth = StringField()
    avatar_url = StringField(db_field="avatar_url")
    signature_count = IntField(default=0)
    username = StringField()
    display_name = StringField()
    gh_id = IntField(unique=True)