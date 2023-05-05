import os
import csv
import json
from collections import defaultdict
from argparse import ArgumentParser
from elasticsearch import Elasticsearch
from utils import connect_elastic



def create_elastic():

    client = connect_elastic()

    spotify_mapping = {
            "properties": {
                "offset": {"type": "integer"},
                "words": {
                    "type": "text",
                    #For porter stemming analyzer, defined in setting
                    "fields": {
                        "stemmed": {
                            "type": "text",
                            "analyzer": "podcast_analyzer"
                        }
                    }
                },
                "show_name": {"type": "text"},
                "ep_name": {"type": "text"},
                "show_id": {"type": "keyword"},
                "ep_id": {"type": "keyword"}
            }
    }

    metadata_mapping = {
            "properties": {
                "clip_num": {"type": "integer"},
                "show_name": {"type": "text"},
                "ep_name": {"type": "text"},
                "show_id": {"type": "keyword"},
                "ep_id": {"type": "keyword"},
                "publisher": {"type": "text"},
                "show_descrption": {"type": "text"},
                "ep_descrption": {"type": "text"}
            }
    }

    setting = {
        "similarity": {
            "default": {
                "type": "BM25",
                "b": 0.4,
                "k1": 0.9
            }
        },
        #Porter stemming
        "analysis": {
            "analyzer": {
                "podcast_analyzer": {
                    "tokenizer": "whitespace",
                    "filter": ["lowercase", "porter_stem"]
                }
            }
        }
    }

    client.indices.create(index='spotify', mappings=spotify_mapping, settings=setting)
    client.indices.create(index='metadata', mappings=metadata_mapping)

    return client

def delete_index(indices):
    client = connect_elastic()

    for i in indices:
        client.indices.delete(index=i)

def index_stats(client):
    size = client.indices.stats(index='spotify', metric=('store'))
    print(size)

def parse_metadata(file_name):
    data = defaultdict(dict)

    with open(file_name, mode='r', encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        for idx, row in enumerate(csv_reader):
            if idx != 0:
                show_code = row[0].split(':')[-1]
                episode_code = row[6].split(':')[-1]

                show_name = row[1]
                episode_name = row[7]

                show_description = row[2]
                episode_description = row[8]

                publisher = row[3]


                data[show_code][episode_code] = (show_name, episode_name, publisher, show_description, episode_description)

    return data


def create_doc(clip, clip_idx, show_code, episode_code, global_id):

    show_name, episode_name, _, _, _ = metadata[show_code][episode_code]
    doc = {
        "offset": clip_idx,
        "words": clip,
        "show_name": show_name,
        "ep_name": episode_name,
        "show_id": show_code,
        "ep_id": episode_code
    }
    client.index(index="spotify", id=global_id, document=doc)

def add_metadata(clip_num, show_code, episode_code):
    show_name, episode_name, publisher, show_description, episode_description = metadata[show_code][episode_code]
    doc = {
        "show_name": show_name,
        "ep_name": episode_name,
        "show_id": show_code,
        "ep_id": episode_code,
        "clip_num": clip_num,
        "publisher": publisher,
        "show_descrption": show_description,
        "ep_descrption": episode_description,
    }
    client.index(index="metadata", document=doc)

def parse_json(folder_name):

    global_id = 0

    for root, dirs, files in os.walk(folder_name):
        for filename in files:
            file_name = os.path.join(root, filename)

            if "DS_Store" in filename:
                continue

            names = file_name.split('/')
            show_code = names[-2].split("_")[-1]
            episode_code = names[-1].split(".")[0]

            with open(file_name, mode='r') as f:
                json_data = json.load(f)
                results = json_data["results"]

                clip_start_time = - 1.0
                word_list = []
                clip_idx = 0

                identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

                for idx1, alternatives in enumerate(results):

                    if len(alternatives["alternatives"][0]) > 0:

                        for idx2, w in enumerate(alternatives["alternatives"][0]["words"]):

                            if "speakerTag" in w:
                                break

                            start_time = float(w["startTime"][:-1])
                            end_time = float(w["endTime"][:-1])

                            # the first word
                            if idx1 == 0 and idx2 == 0:
                                clip_start_time = start_time

                            if end_time - clip_start_time >= 30:
                                clip = " ".join(word_list)

                                create_doc(clip, clip_idx, show_code, episode_code, global_id)
                                global_id += 1
                                clip_idx += 1

                                clip_start_time = start_time
                                word = w["word"]
                                word_list = [word]
                            else:
                                word = w["word"]
                                word_list.append(word)

                if len(word_list) > 0:
                    clip = " ".join(word_list)
                    create_doc(clip, clip_idx, show_code, episode_code, global_id)
                    global_id += 1
                    clip_idx += 1

                add_metadata(clip_idx, show_code, episode_code)



if __name__ == "__main__":
    parser = ArgumentParser(prog="Podcast Indexer")
    parser.add_argument('-d', '--delete', nargs='+')
    args = parser.parse_args()

    if args.delete is not None:
        delete_index(args.delete)
    else:
        client = create_elastic()
        metadata = parse_metadata("../podcasts-no-audio-13GB/metadata.tsv")
        parse_json("../podcasts-no-audio-13GB/dataset")
        index_stats(client)


