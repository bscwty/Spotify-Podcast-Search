from datetime import datetime
from elasticsearch.client import IndicesClient
from utils import connect_elastic
from utils import AUTOMATIC_THRESHOLD, index_dataset

def query(client, ep_id, query_string, pre_offset, n):
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
        left, right = pre_offset - n + 1, pre_offset + n - 1

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
    ep_results = client.search(index=index_dataset, query=query, size=str(len(offset_range)))

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
                chunk_score = chunk_score - ep_dict[idx - n][1][0] + clip_score

            if chunk_score > max_chunk_score:
                max_chunk_score = chunk_score
                start_idx = idx - (n - 1)

    text = []

    for idx in range(start_idx, min(start_idx + n, len(ep_dict))):
        text.append(ep_dict[idx][1][1])
    text = " ".join(text)
    offset = list(offset_range)[start_idx]

    return max_chunk_score, text, offset, list(offset_range)[start_idx: start_idx+n]


def automatic_query(client, ep_id, query_string, pre_offset):
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

    query = {
        "bool": {
            "must": [
                {"term": {"ep_id": ep_id}}
            ],
            "should": {"match": {"words": query_string}}
        }
    }
    ep_results = client.search(index=index_dataset, query=query, size=str(clip_num))

    ep_dict = {}
    for ep_hit in ep_results["hits"]["hits"]:
        ep_dict[ep_hit["_source"]["offset"]] = (ep_hit["_score"], ep_hit["_source"]["words"])
    ep_dict = dict(sorted(ep_dict.items()))

    threshold = ep_dict[pre_offset][0] * AUTOMATIC_THRESHOLD

    max_chunk_score = ep_dict[pre_offset][0]

    left = pre_offset - 1
    right = pre_offset + 1

    offset_range = [pre_offset]
    text = [ep_dict[pre_offset][1]]

    while True:
        left_value = ep_dict[left][0] if left >=0 else -1
        right_value = ep_dict[right][0] if right < clip_num else -1

        if left_value < threshold and right_value < threshold:
            break
        else:

            if left_value >= threshold:
                offset_range.append(left)
                max_chunk_score += ep_dict[left][0]
                text.insert(0, ep_dict[left][1])
                left -= 1

            if right_value >= threshold:
                offset_range.append(right)
                max_chunk_score += ep_dict[right][0]
                text.append(ep_dict[right][1])
                right += 1

    text = " ".join(text)
    offset_range = list(sorted(offset_range))
    offset = offset_range[0]

    return max_chunk_score, text, offset, offset_range


def search(client, query_string, n, res_num, query_type="specified", random_vectors=None):
    new_query_string = query_string

    if random_vectors is not None:
        indices_client = IndicesClient(client)        
        analyzed = indices_client.analyze(
            body={
                "tokenizer": "standard",
                "filter": ["stop"],
                "text": query_string
            }
        )
        pruned_list = []
        for token in analyzed["tokens"]:
            pruned_list.append(token["token"])
        if len(pruned_list) > 0:
            related = random_vectors.find_nearest(pruned_list, k=3)
            if related is not None:
                words = []
                for word_list in related:
                    for word in word_list:
                        words.append(word[0])
                new_query_string = ' '.join(words)

    query_results = client.search(
        index=index_dataset,
        query={
            "match": {
                #"words": query_string
                "words.stemmed": new_query_string
            }
        },
        # size=str(MAX_RESULT_NUMBER * 100))
        size = str(res_num * 100))

    existed_content = {}
    search_results = []
    result_num = 0

    for hit in query_results["hits"]["hits"]:
        score = hit["_score"]
        source_data = hit["_source"]
        pre_offset = source_data["offset"]
        words = source_data["words"]
        show_name = source_data["show_name"]
        ep_name = source_data["ep_name"]
        ep_id = source_data["ep_id"]

        if ep_id not in existed_content:
            if n == 1:
                existed_content[ep_id] = []
                existed_content[ep_id].append(pre_offset)
                offset = pre_offset
                time = "%.1f min -- %.1f min"%(0.5 * offset, 0.5 * offset + 0.5)
                search_results.append([ep_id, score, show_name, ep_name, words, offset, [offset], time])
                result_num += 1
            else:
                if query_type == "specified":
                    score, words, offset, offset_range = query(client, ep_id, query_string, pre_offset, n)
                elif query_type == "automatic":
                    score, words, offset, offset_range = automatic_query(client, ep_id, query_string, pre_offset)

                existed_content[ep_id] = []
                existed_content[ep_id].extend(offset_range)

                if len(offset_range) == 1:
                    time = "%.1f min -- %.1f min"%(0.5 * offset_range[0], 0.5 * offset_range[0] + 0.5)
                else:
                    time = "%.1f min -- %.1f min" % (0.5 * offset_range[0], 0.5 * offset_range[-1] + 0.5)

                search_results.append([ep_id, score, show_name, ep_name, words, offset, offset_range, time])
                result_num += 1
        else:
            if n == 1:
                if pre_offset not in existed_content[ep_id]:
                    existed_content[ep_id].append(pre_offset)
                    offset = pre_offset
                    time = "%.1f min -- %.1f min"%(0.5 * offset, 0.5 * offset + 0.5)
                    search_results.append([ep_id, score, show_name, ep_name, words, offset, [offset], time])
                    result_num += 1
            else:
                if query_type == "specified":
                    score, words, offset, offset_range = query(client, ep_id, query_string, pre_offset, n)
                elif query_type == "automatic":
                    score, words, offset, offset_range = automatic_query(client, ep_id, query_string, pre_offset)

                if len(set(offset_range).intersection(set(existed_content[ep_id]))) == 0:
                    existed_content[ep_id].extend(offset_range)

                    if len(offset_range) == 1:
                        time = "%.1f min -- %.1f min" % (0.5 * offset_range[0], 0.5 * offset_range[0] + 0.5)
                    else:
                        time = "%.1f min -- %.1f min" % (0.5 * offset_range[0], 0.5 * offset_range[-1] + 0.5)

                    search_results.append([ep_id, score, show_name, ep_name, words, offset, offset_range, time])
                    result_num += 1

        # if result_num == MAX_RESULT_NUMBER:
        if result_num == res_num:
            break

    return sorted(search_results, key=lambda x: x[1], reverse=True), new_query_string


if __name__ == "__main__":

    client = connect_elastic()

    print("------")

    a = search(client, "virus", 6, "automatic")
    for r in a:
        print(r)
