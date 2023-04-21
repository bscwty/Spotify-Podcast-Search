from elasticsearch import Elasticsearch

ELASTIC_PASSWORD = "Yxr9tojql4k9vvgqYNju"


def connect_elastic():
    client = Elasticsearch(
        "https://localhost:9200",
        ca_certs="./http_ca.crt",
        basic_auth=("elastic", ELASTIC_PASSWORD)
    )
    return client