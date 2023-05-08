from collections import defaultdict
from utils import connect_elastic


def epi_total_score(clips):
    return sum([clip[1] for clip in clips])


def epi_name_score(x):
    return 0


def epi_descrip_score(x):
    return 0


def episode_search(client, query, nbr_of_results):
    # 1.results based on content
    results = client.search(index="spotify", query={"match": {"words.stemmed": query}}, size=str(nbr_of_results))

    episodes_by_clip_dict = defaultdict(dict)

    for result in results["hits"]["hits"]:
        clip_score = result["_score"]
        source_data = result["_source"]
        clip_id = source_data["offset"]
        clip_text = source_data["words"]

        epi_name = source_data["ep_name"]

        clip_info = [clip_id, clip_score, clip_text]
        if epi_name in episodes_by_clip_dict.keys():
            episodes_by_clip_dict[epi_name]["clips"].append(clip_info)
        else:
            epi_id = source_data["ep_id"]
            show_name = source_data["show_name"]
            epi_query = {
                "bool": {
                    "filter":
                        {"term": {"ep_id": epi_id}}
                }
            }
            episode = client.search(index="metadata", query=epi_query, size=1)  # TODO reflect on 1

            episodes_by_clip_dict[epi_name]["clips"] = [clip_info, ]
            episodes_by_clip_dict[epi_name]["show name"] = show_name
            ep_source = episode["hits"]["hits"][0]["_source"]
            episodes_by_clip_dict[epi_name]["episode description"] = ep_source["ep_descrption"]
            episodes_by_clip_dict[epi_name]["publisher"] = ep_source["publisher"]

        # TODO change if else to one bloc

    # sum scores
    for key, val in episodes_by_clip_dict.items():
        episodes_by_clip_dict[key]["score"] = epi_total_score(val["clips"])
    out1 = sorted(episodes_by_clip_dict.items(), key=lambda x: x[1]["score"], reverse=True)

    return out1, len(results["hits"]["hits"])


def episode_search_by_name(query, nbr_of_results=5):
    # 2.results based on name, should be a match here
    # for these episodes, look for info to fill out the episodes dictionary information
    names_query = {
        "match": {
            "ep_name": query
        }
    }
    episodes_by_name = client.search(index="metadata", query=names_query, size=str(nbr_of_results))  # TODO 5 as a variable, we have duplicates here cause of indexing

    episodes_by_name_dict = defaultdict(dict)

    for episode in episodes_by_name["hits"]["hits"]:
        epi_name = episode["_source"]["ep_name"]
        epi_id = episode["_source"]["ep_id"]
        show_name = episode["_source"]["show_name"]

        epi_query = {
            "bool": {
                "filter":
                    {"term": {"ep_id": epi_id}}
            }
        }  # try bool must term
        epi_clips = client.search(index="spotify", query=epi_query, size=10)

        episodes_by_name_dict[epi_name]["score"] = episode["_score"]
        episodes_by_name_dict[epi_name]["show name"] = show_name
        episodes_by_name_dict[epi_name]["episode description"] = episode["_source"][
            "ep_descrption"]
        episodes_by_name_dict[epi_name]["publisher"] = episode["_source"][
            "publisher"]
        episodes_by_name_dict[epi_name]["clips"] = []

        for clip in epi_clips["hits"]["hits"]:
            clip_score = clip["_score"]
            source_data = clip["_source"]
            clip_id = source_data["offset"]
            clip_text = source_data["words"]

            clip_info = [clip_id, clip_score, clip_text]
            episodes_by_name_dict[epi_name]["clips"].append(clip_info)

    out2 = sorted(episodes_by_name_dict.items(), key=lambda x: x[1]["score"], reverse=True)

    return out2


def episode_search_by_desc(query, nbr_of_results=5):

    # 3.results based on description, should be a match here

    # for these episodes, look for info to fill out the episodes dictionary information
    descrip_query = {"match": {"ep_descrption": query}}
    episodes_by_decrip = client.search(index="metadata", query=descrip_query, size=str(nbr_of_results))
    episodes_by_descrip_dict = defaultdict(dict)

    for episode in episodes_by_decrip["hits"]["hits"]:

        epi_name = episode["_source"]["ep_name"]
        epi_id = episode["_source"]["ep_id"]
        show_name = episode["_source"]["show_name"]

        epi_query = {
            "bool": {
                "filter":
                    {"term": {"ep_id": epi_id}}
            }
        }  # try bool must term
        epi_clips = client.search(index="spotify", query=epi_query, size=10)  # TODO 10 as a variable

        episodes_by_descrip_dict[epi_name]["score"] = episode["_score"]
        episodes_by_descrip_dict[epi_name]["show name"] = show_name
        episodes_by_descrip_dict[epi_name]["episode description"] = episode["_source"][
            "ep_descrption"]
        episodes_by_descrip_dict[epi_name]["publisher"] = episode["_source"][
            "publisher"]
        episodes_by_descrip_dict[epi_name]["clips"] = []

        for clip in epi_clips["hits"]["hits"]:
            clip_score = clip["_score"]
            source_data = clip["_source"]
            clip_id = source_data["offset"]
            clip_text = source_data["words"]

            clip_info = [clip_id, clip_score, clip_text]
            episodes_by_descrip_dict[epi_name]["clips"].append(clip_info)

    out3 = sorted(episodes_by_descrip_dict.items(), key=lambda x: x[1]["score"], reverse=True)

    return out3


def show_total_score(episodes):
    return sum([epi_total_score(episode["clips"]) for episode in episodes.values()])


def show_search_by_clip(client, query, nbr_of_results):
    # 1.results based on content
    results = client.search(index="spotify", query={"match": {"words.stemmed": query}}, size=str(nbr_of_results))

    shows = defaultdict(dict)

    for result in results["hits"]["hits"]:
        clip_score = result["_score"]
        source_data = result["_source"]
        clip_id = source_data["offset"]
        clip_text = source_data["words"]

        epi_name = source_data["ep_name"]
        show_name = source_data["show_name"]

        clip_info = [clip_id, clip_score, clip_text]

        epi_id = source_data["ep_id"]
        epi_query = {
            "bool": {
                "filter":
                    {"term": {"ep_id": epi_id}}
            }
        }
        episode = client.search(index="metadata", query=epi_query, size=1)  # TODO reflect on 1

        if show_name not in shows.keys():
            show_source = episode["hits"]["hits"][0]["_source"]
            shows[show_name]["show description"] = show_source["show_descrption"]

            shows[show_name]["episodes"] = dict()

        if epi_name in shows[show_name]["episodes"].keys():
            shows[show_name]["episodes"][epi_name]["clips"].append(clip_info)
        else:
            shows[show_name]["episodes"][epi_name] = dict()

            shows[show_name]["episodes"][epi_name]["clips"] = [clip_info, ]
            shows[show_name]["episodes"][epi_name]["show name"] = show_name  # TODO delete ?

            ep_source = episode["hits"]["hits"][0]["_source"]
            shows[show_name]["episodes"][epi_name]["episode description"] = ep_source["ep_descrption"]
            shows[show_name]["episodes"][epi_name]["publisher"] = ep_source["publisher"]

        # TODO we can change this if else to one bloc actually

        # clip_id = result["_id"]

    # sum scores
    out1 = sorted(shows.items(), key=lambda x: show_total_score(x[1]["episodes"]), reverse=True)
    return out1, len(results["hits"]["hits"])


def show_search_by_name(query, nbr_of_results=5):

    # 2.results based on name, should be a match here
    shows_by_name = client.search(index="metadata", query={"match": {"show_name": query}}, size=str(nbr_of_results))

    shows_by_name_dict = defaultdict(dict)

    for show in shows_by_name["hits"]["hits"]:
        show_source = show["_source"]
        show_name = show_source["show_name"]
        epi_name = show_source["ep_name"]
        epi_id = show_source["ep_id"]

        show_query = {
            "bool": {
                "filter":
                    {"term": {"ep_id": epi_id}}
            }
        }  # try bool must term
        epi_clips = client.search(index="spotify", query=show_query, size=10)

        if show_name not in shows_by_name_dict.keys():
            shows_by_name_dict[show_name]["score"] = show["_score"]
            shows_by_name_dict[show_name]["show description"] = show_source["show_descrption"]

            shows_by_name_dict[show_name]["episodes"] = dict()

        shows_by_name_dict[show_name]["episodes"][epi_name] = dict()

        shows_by_name_dict[show_name]["episodes"][epi_name]["show name"] = show_name  # TODO delete ?

        shows_by_name_dict[show_name]["episodes"][epi_name]["episode description"] = show_source["ep_descrption"]
        shows_by_name_dict[show_name]["episodes"][epi_name]["publisher"] = show_source["publisher"]
        shows_by_name_dict[show_name]["episodes"][epi_name]["clips"] = []

        for clip in epi_clips["hits"]["hits"]:
            clip_score = clip["_score"]
            source_data = clip["_source"]
            clip_id = source_data["offset"]
            clip_text = source_data["words"]

            clip_info = [clip_id, clip_score, clip_text]

            shows_by_name_dict[show_name]["episodes"][epi_name]["clips"].append(clip_info)

    out2 = sorted(shows_by_name_dict.items(), key=lambda x: x[1]["score"], reverse=True)
    return out2


def show_search_by_desc(query, nbr_of_results=5):
    # 3.results based on description, should be a match here
    shows_by_descr = client.search(index="metadata", query={"match": {"show_descrption": query}}, size=str(nbr_of_results))

    shows_by_descr_dict = defaultdict(dict)

    for show in shows_by_descr["hits"]["hits"]:
        show_source = show["_source"]
        show_name = show_source["show_name"]
        epi_name = show_source["ep_name"]
        epi_id = show_source["ep_id"]

        show_query = {
            "bool": {
                "filter":
                    {"term": {"ep_id": epi_id}}
            }
        }  # try bool must term
        epi_clips = client.search(index="spotify", query=show_query, size=10)

        if show_name not in shows_by_descr_dict.keys():
            shows_by_descr_dict[show_name]["score"] = show["_score"]
            shows_by_descr_dict[show_name]["show description"] = show_source["show_descrption"]

            shows_by_descr_dict[show_name]["episodes"] = dict()

        shows_by_descr_dict[show_name]["episodes"][epi_name] = dict()

        shows_by_descr_dict[show_name]["episodes"][epi_name]["show name"] = show_name  # TODO delete ?

        shows_by_descr_dict[show_name]["episodes"][epi_name]["episode description"] = show_source["ep_descrption"]
        shows_by_descr_dict[show_name]["episodes"][epi_name]["publisher"] = show_source["publisher"]
        shows_by_descr_dict[show_name]["episodes"][epi_name]["clips"] = []

        for clip in epi_clips["hits"]["hits"]:
            clip_score = clip["_score"]
            source_data = clip["_source"]
            clip_id = source_data["offset"]
            clip_text = source_data["words"]

            clip_info = [clip_id, clip_score, clip_text]

            shows_by_descr_dict[show_name]["episodes"][epi_name]["clips"].append(clip_info)

    out3 = sorted(shows_by_descr_dict.items(), key=lambda x: x[1]["score"], reverse=True)

    return out3  # TODO check duplicates


if __name__ == "__main__":
    clips_nbr = 100

    client = connect_elastic()
    res = episode_search_by_clip("hello", clips_nbr)
