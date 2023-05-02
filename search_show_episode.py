from collections import defaultdict
from utils import connect_elastic


'''
TODO:
*highlight result terms
*Types of search we can do:
 -by show: sort the show based on the result of a query on its name and/or description and content of its episodes. number of results ?
 -by episode: sort the episodes on the result of a query on its name and/or description or its content. number of results ?
 -by content: based on fixed n or automatic, we show list of clips corresponding to the query. Have the possibility of 
 going to its show or episode and list all relevant clips from there. Maybe possibility of sorting based on show or episode.
 add top x results as feature (or show pages of results).
 
 
Question:
clip_num in metadata mapping?
have metadata as global var in whole project


password for loaded tar from windows
X75e1zOzkPp2eyyMJ0_g
'''


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
        clip_id = source_data["id"]
        clip_text = source_data["words"]

        epi_name = source_data["ep_name"]
        show_name = source_data["show_name"]

        clip_info = [clip_id, clip_score, clip_text]
        if epi_name in episodes_by_clip_dict.keys():
            episodes_by_clip_dict[epi_name]["clips"].append(clip_info)
        else:
            episodes_by_clip_dict[epi_name]["clips"] = [clip_info, ]
            episodes_by_clip_dict[epi_name]["show name"] = show_name
            episodes_by_clip_dict[epi_name]["episode description"] = "None"  # TODO

    # sum scores
    out1 = sorted(episodes_by_clip_dict.items(), key=lambda x: epi_total_score(x[1]["clips"]), reverse=True)

    # 2.results based on name, should be match here
    # for these episodes, look for info to fill out the episodes dictionary information

    names_query = {
        "bool": {
            "must": [
                {"term": {"ep_name": query}}
            ]
        }
    }
    episodes_by_name = client.search(index="spotify", query=names_query)

    episodes_by_name_dict = defaultdict(dict)

    for episode in episodes_by_name:

        clip_score = episode["_score"]
        source_data = episode["_source"]
        clip_id = source_data["id"]
        clip_text = source_data["words"]

        epi_name = source_data["ep_name"]
        show_name = source_data["show_name"]

        clip_info = [clip_id, clip_score, clip_text]
        if epi_name in episodes_by_name_dict.keys():
            episodes_by_name_dict[epi_name]["clips"].append(clip_info)
        else:
            episodes_by_name_dict[epi_name]["clips"] = [clip_info, ]
            episodes_by_name_dict[epi_name]["show name"] = show_name
            episodes_by_name_dict[epi_name]["episode description"] = "None"  # TODO

    out2 = sorted(episodes_by_name_dict.items(), key=lambda x: epi_name_score(x), reverse=True)

    # 3.results based on description, should be match here
    
    # for these episodes, look for info to fill out the episodes dictionary information

    descrip_query = {
        "bool": {
            "must": [
                {"match": {"ep_description": query}}
            ]
        }
    }
    episodes_by_decrip = client.search(index="spotify", query=descrip_query)
    episodes_by_descrip_dict = defaultdict(dict)

    for episode in episodes_by_decrip:

        clip_score = episode["_score"]
        source_data = episode["_source"]
        clip_id = source_data["id"]
        clip_text = source_data["words"]

        epi_name = source_data["ep_name"]
        show_name = source_data["show_name"]

        clip_info = [clip_id, clip_score, clip_text]
        if epi_name in episodes_by_descrip_dict.keys():
            episodes_by_descrip_dict[epi_name]["clips"].append(clip_info)
        else:
            episodes_by_descrip_dict[epi_name]["clips"] = [clip_info, ]
            episodes_by_descrip_dict[epi_name]["show name"] = show_name
            episodes_by_descrip_dict[epi_name]["episode description"] = "None"  # TODO

    out3 = sorted(episodes_by_descrip_dict.items(), key=lambda x: epi_descrip_score(x), reverse=True)

    return out1+out2+out3


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
    res = show_search("coronavirus spread", clips_nbr)
