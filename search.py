from datetime import datetime
from utils import connect_elastic

'''
TODO: episode, podcast, content
'''


def search(client, query_string, n):
    results = client.search(index="spotify", query={"match": {"words": query_string}}, size="100")
    d = {}

    for hit in results["hits"]["hits"]:
        score = hit["_score"]
        source_data = hit["_source"]
        offset = source_data["offset"]
        words = source_data["words"]
        show_name = source_data["show_name"]
        ep_name = source_data["ep_name"]
        ep_id = source_data["ep_id"]

        if ep_id not in d:
            if n == 1:
                d[ep_id] = (score, show_name, ep_name, words, offset)
            else:
                query = {
                    "constant_score": {
                        "filter": {
                            "term": {
                                "ep_id": ep_id
                            }
                        }
                    }
                }
                meta_results = client.search(index="metadata", query=query)
                clip_num = meta_results["hits"]["hits"][0]["_source"]["clip_num"]

                if n > clip_num:
                    n = clip_num
                    offset_range = range(0, clip_num)
                elif 2 * n - 1 >= clip_num:
                    offset_range = range(0, clip_num)
                else:
                    left, right = offset - n + 1, offset + n - 1

                    if left < 0:
                        right = right - left
                        left = 0

                    if right > clip_num:
                        left = left - (right - clip_num)
                        right = clip_num

                    offset_range = range(left, right)  # must include the queried clip

                query = {
                    "bool": {
                        "must": [
                            {"terms": {"offset": [str(i) for i in offset_range]}},
                            {"term": {"ep_id": ep_id}}
                        ],
                        "should": {"match": {"words": query_string}}
                    }
                }
                ep_results = client.search(index="spotify", query=query, size=str(len(offset_range)))

                ep_dict = {}
                for ep_hit in ep_results["hits"]["hits"]:
                    ep_dict[ep_hit["_source"]["offset"]] = (ep_hit["_score"], ep_hit["_source"]["words"])
                ep_dict = sorted(ep_dict.items())

                chunk_score = 0
                max_chunk_score = 0
                start_idx = 0
                for idx, (offset, (clip_score, clip_text)) in enumerate(ep_dict):

                    if idx < n - 2:
                        chunk_score += clip_score
                    else:
                        if idx == n - 1:
                            chunk_score += clip_score
                        else:
                            chunk_score = chunk_score - ep_dict[idx-n][1][0] + clip_score

                        if chunk_score > max_chunk_score:
                            max_chunk_score = chunk_score
                            start_idx = idx - n

                text = []

                for idx in range(start_idx, min(start_idx + n, len(ep_dict))):
                    text.append(ep_dict[idx][1][1])
                text = " ".join(text)
                offset = list(offset_range)[start_idx]

                d[ep_id] = (max_chunk_score, show_name, ep_name, text, offset)

        if len(d) == 20:
            return sorted(d.items(), key=lambda x: x[1][0], reverse=True)


def episode_search(client, query_string):
    results = client.search(index="spotify", query={"match": {"words": query_string}}, size="100")
    d = {}

    for hit in results["hits"]["hits"]:
        score = hit["_score"]
        source_data = hit["_source"]
        offset = source_data["offset"]
        words = source_data["words"]
        show_name = source_data["show_name"]
        ep_name = source_data["ep_name"]
        ep_id = source_data["ep_id"]

        if ep_id not in d:

            query = {
                "constant_score": {
                    "filter": {
                        "term": {
                            "ep_id": ep_id
                        }
                    }
                }
            }
            meta_results = client.search(index="metadata", query=query)

            clip_num = meta_results["hits"]["hits"][0]["_source"]["clip_num"]
            n = clip_num
            offset_range = range(0, clip_num)

            query = {
                "bool": {
                    "must": [
                        {"terms": {"offset": [str(i) for i in offset_range]}},
                        {"term": {"ep_id": ep_id}}
                    ],
                    "should": {"match": {"words": query_string}}
                }
            }
            ep_results = client.search(index="spotify", query=query)  # body=dsl_body)

            ep_dict = {}
            for ep_hit in ep_results["hits"]["hits"]:
                ep_dict[ep_hit["_source"]["offset"]] = (ep_hit["_score"], ep_hit["_source"]["words"])
            ep_dict = sorted(ep_dict.items())

            chunk_score = 0
            max_chunk_score = 0
            start_idx = 0
            for idx, (offset, (clip_score, clip_text)) in enumerate(ep_dict):
                if idx < n - 2:
                    chunk_score += clip_score
                else:
                    if idx == n - 1:
                        chunk_score += clip_score
                    else:
                        chunk_score = chunk_score - ep_dict[idx-n][1][0] + clip_score

                    if chunk_score > max_chunk_score:
                        max_chunk_score = chunk_score
                        start_idx = idx - n

            text = []
            for idx in range(start_idx, start_idx + n):
                text.append(ep_dict[idx][1][1])
            text = " ".join(text)
            offset = list(offset_range)[start_idx]

            d[ep_id] = (max_chunk_score, show_name, ep_name, text, offset)

        if len(d) == 20:
            return sorted(d.items(), key=lambda x: x[1][0], reverse=True)


if __name__ == "__main__":

    client = connect_elastic()
    results = search(client, "virus", 20)
    # for i in results:
    #     print(i)



