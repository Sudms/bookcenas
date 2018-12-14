import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient
from django.shortcuts import render, redirect
from django.http import HttpResponse

endpoint = "http://localhost:7200"
repo_name = "movies"

client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)

# Create your views here.

def home(request):
    actor_to_be_search = movie_to_be_searched = None
    
    try:
        if 'movie-search-keyword' in request.POST:
            movie_to_be_searched = request.POST.get("movie-search-keyword")

            query = '''
                PREFIX movPred:<http://movies.org/pred/>
                SELECT distinct ?name
                WHERE{
                ?film movPred:directed_by ?who .
                ?film movPred:name ?name .
                FILTER regex(?name, "''' + str(movie_to_be_searched) + '''", "i") .
                }
            '''

            payload_query = {"query" : query}
            res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
            res = json.loads(res)
    
            # for e in res['results']['bindings']:
            #     print(e['mov']['value'])
            
            if not res['results']['bindings']:
                return render(request, '404.html', {})

        if 'actor-search-keyword' in request.POST:
            actor_to_be_searched = request.POST.get("actor-search-keyword")

            query = '''
                PREFIX movPred:<http://movies.org/pred/>
                SELECT distinct ?name
                WHERE{
                ?film movPred:directed_by ?who .
                ?film movPred:name ?name .
                FILTER regex(?name, "''' + str(actor_to_be_searched) + '''", "i") .
                }
            '''

            payload_query = {"query" : query}
            res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
            res = json.loads(res)
    
            # for e in res['results']['bindings']:
            #     print(e['mov']['value'])
            
            if not res['results']['bindings']:
                return render(request, '404.html', {})
    finally:
        pass
            
    return render(request, 'index.html', {})

def celebrity(request):
    return render(request, 'celebrity-detail.html', {})

def movie(request):
    return render(request, 'movie-detail.html', {})