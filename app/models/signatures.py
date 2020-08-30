from app import mongo
from mongoengine import ListField, ObjectIdField, IntField

class Signatures(mongo.Document):
    meta = {'collection': 'signatures'}
    signee = ObjectIdField()
    target = ObjectIdField()
    time = IntField()