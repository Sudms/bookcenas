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
    celeb_to_be_searched = movie_to_be_searched = None
    
    try:
        if 'movie-search-keyword' in request.POST:
            movie_to_be_searched = request.POST.get("movie-search-keyword")

            # Pesquisa de um filme pelo nome
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
            movies_to_list = list()
    
            for e in res['results']['bindings']:
                movies_to_list.append(e['name']['value'])

            print(movies_to_list)
            
            if res['results']['bindings']:
                return render(request, 'movie-list.html', {"movies" : movies_to_list})
            else:
                return render(request, '404.html', {})

        if 'actor-search-keyword' in request.POST:
            celeb_to_be_searched = request.POST.get("actor-search-keyword")

            # Pesquisa de uma celeb pelo nome
            query = '''
                PREFIX movPred:<http://movies.org/pred/>
                SELECT distinct ?name
                WHERE{
                {?film movPred:starring ?who .
                ?who movPred:name ?name .
                FILTER regex(?name, "''' + str(celeb_to_be_searched) + '''", "i") .
                }
                UNION
                {
                ?film movPred:directed_by ?who .
                ?who movPred:name ?name .
                FILTER regex(?name, "''' + str(celeb_to_be_searched) + '''", "i") .
                }
                }
            '''

            payload_query = {"query" : query}
            res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
            res = json.loads(res)
            celeb_to_list = list()
    
            for e in res['results']['bindings']:
                celeb_to_list.append(e['name']['value'])

            print(celeb_to_list)
            
            if res['results']['bindings']:
                return render(request, 'celebrities-list.html', {"celebs" : celeb_to_list})
            else:
                return render(request, '404.html', {})
            
    finally:
        pass
            
    return render(request, 'index.html', {})

def celebrity(request):
    if 'name' in request.GET:
        name = request.GET['name']
        
        query = '''
            PREFIX movPred:<http://movies.org/pred/>
            SELECT ?mov
            WHERE{
            ?film movPred:starring ?who.
            ?who movPred:name ?name
            FILTER regex(?name, "''' + str(name) + '''", "i")
            ?film movPred:name ?mov
            }
        '''
        payload_query = {"query" : query}
        res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
        res = json.loads(res)
        movies_starring = list()
    
        for e in res['results']['bindings']:
            movies_starring.append(e['mov']['value'])

        return render(request, 'celebrity-detail.html', {"name" : name, "filmography": movies_starring})
    else:
        return render(request, '404.html', {})

    

def movie(request):
    if 'name' in request.GET:
        name = request.GET['name']

        # Cast
        query = '''
            PREFIX movPred:<http://movies.org/pred/>
            SELECT ?starring
            WHERE{
            ?film movPred:name ?name.
            FILTER regex(?name, "''' + str(name) + '''", "i")
            ?film movPred:starring ?who.
            ?who movPred:name ?starring
            }
        '''

        payload_query = {"query" : query}
        res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
        res = json.loads(res)
        cast_to_list = list()

        for e in res['results']['bindings']:
            cast_to_list.append(e['starring']['value'])
        
        print(cast_to_list)

        query = '''
        PREFIX movPred:<http://movies.org/pred/>
        SELECT ?name
        WHERE{
    	?film movPred:directed_by ?director.
    	?film movPred:name ?s .
    	?film movPred:directed_by ?o .
    	?o movPred:name ?name .
    	FILTER regex(?s, "''' + str(name) + '''", "i") .
        }
        '''
        payload_query = {"query" : query}
        res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
        res = json.loads(res)

        for e in res['results']['bindings']:
           movie_director=e['name']['value']

        return render(request, 'movie-detail.html', {"name": name, "director": movie_director, "cast" : cast_to_list})
    else:
        return render(request, '404.html', {})