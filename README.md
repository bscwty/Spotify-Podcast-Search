# Spotify-Podcast-Search
Project for DD2477. A search engine of a Spotify podcasts dataset, using Elasticsearch and an interactive interface.


## Installation
The best way to get an Elasticsearch framework is through Docker.
Obtaining Elasticsearch for Docker is as simple as issuing a docker pull command against the Elastic Docker registry.
```commandline
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.7.1
```

The following commands start a single-node Elasticsearch cluster for development or testing.
```commandline
Create a new docker network for Elasticsearch and Kibana
```

Start Elasticsearch in Docker. A password is generated for the elastic user and output to the terminal, plus an enrollment token for enrolling Kibana
```commandline
docker run --name es01 --net elastic -p 9200:9200 -it docker.elastic.co/elasticsearch/elasticsearch:8.7.1
```

Copy your `ELASTIC_PASSWORD` and the `http_ca.crt` security certificate from your Docker container to your local machine.


## Index
1. Have ElasticSearch running;
2. Put `http_ca.crt` under the folder, change to your own `ELASTIC_PASSWORD`;
3. Change the metadata and data directory to your own;
4. run [index.py](./index.py)

After indexing, your Elasticsearch image contains all the data you need to scroll, and could be used/accessed anytime.

## Search

1. Launch the GUI by executing [gui.py](./gui.py).
2. Put your query in the search bar, with the desired features.
