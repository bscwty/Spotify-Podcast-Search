import os
import json



def parse_json(folder_name, output_file):
    for root, dirs, files in os.walk(folder_name):
        for filename in files:
            file_name = os.path.join(root, filename)

            if "DS_Store" in filename:
                continue

            names = file_name.split('/')

            with open(file_name, mode='r') as f:
                json_data = json.load(f)
                results = json_data["results"]

                word_list = []

                for alternatives in results:

                    if len(alternatives["alternatives"][0]) > 0:

                        for w in alternatives["alternatives"][0]["words"]:

                            if "speakerTag" in w:
                                break

                            word_list.append(w["word"].lower())
                        
                        word_list.append('\n')
                        text = ' '.join(word_list)
                        word_list.clear()

                        with open(output_file, 'a') as out_text:
                            out_text.write(text)



if __name__ == "__main__":
    parse_json("../podcasts-no-audio-13GB/dataset/", "podcast_text.txt")