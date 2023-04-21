from datetime import datetime
from utils import connect_elastic

'''
TODO: episode, podcast, content
'''

# def search(query_string, n):
#     results = client.search(index="spotify", query={"match": {"words": query_string}}, size="100")
#     d = {}
#
#     for hit in results["hits"]["hits"]:
#         score = hit["_score"]
#         source_data = hit["_source"]
#         offset = source_data["id"]
#         words = source_data["words"]
#         show_name = source_data["show_name"]
#         ep_name = source_data["ep_name"]
#
#         if ep_name not in d:
#             clip_number = 1
#             l, r = offset, offset
#             while clip_number < n:
#                 l = l - 1
#                 r = offset + 1
#
#                 if l < 0:
#                     clip_number = n # combine 右边
#                     break
#                 if r > 100:
#                     clip_number = n # combine 左边
#                     break
#
#                 ep_results = client.search(index="spotify", query={"bool": {
#                     "must": [{"match": {"ep_name": ep_name}},
#                              {"bool": {
#                                  "should": [
#                                      {"match": {"offset": l}},
#                                      {"match": {"offset": r}},
#                                  ]
#                              }
#                              }],
#                     "should": [{"match": {"words": query_string}}]}})
#
#                 clip_number += 1
#
#         if len(d) == 20:
#             return results

def search(query_string, n):
    results = client.search(index="spotify", query={"match": {"words": query_string}}, size="20")
    return results

if __name__ == "__main__":

    client = connect_elastic()
    result = search("coronavirus spread", 2)

    for hit in result["hits"]["hits"]:
        print(hit)

