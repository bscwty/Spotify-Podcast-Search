from collections import defaultdict
from utils import connect_elastic


def epi_total_score(clips):
    return sum([clip[1] for clip in clips])


def epi_name_score(x):
    return 0


def epi_descrip_score(x):
    return 0


def episode_search(query, nbr_of_results):
    # 1.results based on content
    results = client.search(index="spotify", query={"match": {"words": query}}, size=str(nbr_of_results))

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
            episodes_by_clip_dict[epi_name]["episode description"] = ep_source["ep_descrption"]  # TODO
            episodes_by_clip_dict[epi_name]["publisher"] = ep_source["publisher"]  # TODO

    # sum scores
    out1 = sorted(episodes_by_clip_dict.items(), key=lambda x: epi_total_score(x[1]["clips"]), reverse=True)

    # 2.results based on name, should be a match here
    # for these episodes, look for info to fill out the episodes dictionary information

    names_query = {
        "match": {
            "ep_name": query
        }
    }
    episodes_by_name = client.search(index="metadata", query=names_query, size=5)  # TODO 5 as a variable, ze have duplicates here cause of indexing

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

        episodes_by_name_dict[epi_name]["score"] = episode["_score"]  # TODO
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

    # 3.results based on description, should be a match here

    # for these episodes, look for info to fill out the episodes dictionary information
    descrip_query = {"match": {"ep_descrption": query}}
    episodes_by_decrip = client.search(index="metadata", query=descrip_query, size=5)
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

        episodes_by_descrip_dict[epi_name]["score"] = episode["_score"]  # TODO
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

    return out2 + out3 + out1


def show_total_score(episodes):
    return sum([epi_total_score(episode["clips"]) for episode in episodes.values()])


def show_search(query, nbr_of_results):
    # 1.results based on content
    results = client.search(index="spotify", query={"match": {"words": query}}, size=str(nbr_of_results))

    shows = defaultdict(dict)

    for result in results["hits"]["hits"]:
        clip_score = result["_score"]
        source_data = result["_source"]
        clip_id = source_data["id"]
        clip_text = source_data["words"]

        epi_name = source_data["ep_name"]
        show_name = source_data["show_name"]

        clip_info = [clip_id, clip_score, clip_text]
        if show_name not in shows.keys():
            shows[show_name]["show description"] = "Show None"  # TODO from metadata
            shows[show_name]["episodes"] = dict()

        if epi_name in shows[show_name]["episodes"].keys():
            shows[show_name]["episodes"][epi_name]["clips"].append(clip_info)
        else:
            shows[show_name]["episodes"][epi_name] = dict()
            shows[show_name]["episodes"][epi_name]["clips"] = [clip_info, ]
            shows[show_name]["episodes"][epi_name]["show name"] = show_name  # TODO delete ?
            shows[show_name]["episodes"][epi_name]["episode description"] = "Episode None"  # TODO
        # clip_id = result["_id"]

    # sum scores
    out = sorted(shows.items(), key=lambda x: show_total_score(x[1]["episodes"]), reverse=True)

    # 2.results based on name and/or description, should be match here
    # TODO
    return out


if __name__ == "__main__":
    clips_nbr = 100

    client = connect_elastic()
    res = episode_search("coronavirus spread", clips_nbr)
