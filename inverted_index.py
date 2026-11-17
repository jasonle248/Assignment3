import string
from collections import Counter

from pymongo import MongoClient


def connect_database():
    client = MongoClient("mongodb://localhost:27017/")
    return client["assignment3"]


def get_term_frequencies(text):
    clean = text.lower().translate(str.maketrans("", "", string.punctuation))
    return Counter(clean.split())


def add_postings(db, doc_id, text):
    for term, tf in get_term_frequencies(text).items():
        db.inverted_index.update_one(
            {"term": term},
            {"$push": {"postings": {"$each": [{"docId": doc_id, "tf": tf}],
                                    "$sort": {"docId": 1}}}},
            upsert=True,
        )


def remove_postings(db, doc_id, text):
    for term in get_term_frequencies(text):
        db.inverted_index.update_one(
            {"term": term},
            {"$pull": {"postings": {"docId": doc_id}}},
        )
    db.inverted_index.delete_many({"postings": {"$size": 0}})


def insert_document(db, doc_id, text):
    db.documents.insert_one({"_id": doc_id, "text": text})
    add_postings(db, doc_id, text)


def update_document(db, doc_id, text):
    old_doc = db.documents.find_one({"_id": doc_id})
    if old_doc is None:
        return
    remove_postings(db, doc_id, old_doc["text"])
    db.documents.update_one({"_id": doc_id}, {"$set": {"text": text}})
    add_postings(db, doc_id, text)


def delete_document(db, doc_id):
    old_doc = db.documents.find_one({"_id": doc_id})
    if old_doc is None:
        return
    remove_postings(db, doc_id, old_doc["text"])
    db.documents.delete_one({"_id": doc_id})


def print_collections(db):
    print("documents:")
    for doc in db.documents.find().sort("_id", 1):
        print(doc)

    print("\ninverted_index:")
    for entry in db.inverted_index.find({}, {"_id": 0}).sort("term", 1):
        print(entry)


def main():
    db = connect_database()

    db.documents.delete_many({})
    db.inverted_index.delete_many({})
    db.inverted_index.create_index("term", unique=True)

    insert_document(db, 1, "Summer rain is common in Florida.")

    insert_document(db, 2, "Summer is hot in Arizona.")

    update_document(db, 1, "Summer rain is hot rain in Florida.")

    insert_document(db, 3, "Hot summer rain in California.")

    delete_document(db, 2)

    print_collections(db)


if __name__ == "__main__":
    main()