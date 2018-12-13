import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient

endpoint = "http://localhost:8000"
repo_name = "movies"

client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)

query = """
    PREFIX mov:<http://movies.org/pred/>
    SELECT ?actor_n
    WHERE{
    ?film mov:name "{0}" .
    ?film mov:starring ?actor .
    ?actor mov:name ?actor_n .
    }
"""

# payload_query = {"query": query}
# res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
# res = json.loads(res)

# for e in res['results']['bindings']:
#         print(e['actor_n']['value'])


# query = """
#     PREFIX movPred:<http://movies.org/pred/>
#     SELECT ?mov
#     WHERE{
#     ?film movPred:name ?name .
#     FILTER regex(?name, "My Life In hell", "i") .
#     ?film movPred:name ?mov .
# }
# """

payload_query = {"query" : query}

print(payload_query)

res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
res = json.loads(res)

for e in res['results']['bindings']:
    print(e['mov']['value'])
    
# update = """
#     PREFIX mov:<http://movies.org/pred/>
#     PREFIX move: <http://movies.org/>
#     INSERT DATA
#     {
#     move:my_life mov:name "My Life in Hell" .
#     }
# """

# payload_query = {"update": update}
# res = accessor.sparql_update(body=payload_query, repo_name=repo_name)