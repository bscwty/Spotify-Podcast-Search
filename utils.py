from elasticsearch import Elasticsearch

#ELASTIC_PASSWORD = "Yxr9tojql4k9vvgqYNju"


def read_password():
    with open('pwd.txt', 'r') as f:
        return f.readlines()[0].strip()


def connect_elastic():
    client = Elasticsearch(
        "https://localhost:9200",
        ca_certs="./http_ca.crt",
        basic_auth=("elastic", read_password())
    )
    return client