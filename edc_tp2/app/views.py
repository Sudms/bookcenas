import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient
from django.shortcuts import render, redirect
from django.http import HttpResponse
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint = "http://localhost:8000"
repo_name = "movies"

client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

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
            celeb_to_list = dict()
    
            for e in res['results']['bindings']:
                celeb_name = e['name']['value']
                
                sparql.setQuery(
                '''
                    SELECT ?image 
                    WHERE {
                    ?item wdt:P31 wd:Q5 .?item ?label "''' + str(celeb_name) + '''"@en .
                    ?item wdt:P18 ?image .
                    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
                    }''')

                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()

                for result in results['results']['bindings']:
                    d=result['image']['value']
                    a=celeb_name
                    celeb_to_list[a] = d
                
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
            {
            ?film movPred:starring ?who.
            ?who movPred:name ?name .
            FILTER regex(?name, "''' + str(name) + '''", "i") .
            ?film movPred:name ?mov .
            }
            UNION
            {
            ?film movPred:directed_by ?who.
            ?who movPred:name ?name .
            FILTER regex(?name, "''' + str(name) + '''", "i") .
            ?film movPred:name ?mov .
            }
            }  
        '''

        payload_query = {"query" : query}
        res = accessor.sparql_select(body=payload_query, repo_name=repo_name)
        res = json.loads(res)
        movies_starring = list()
    
        for e in res['results']['bindings']:
            movies_starring.append(e['mov']['value'])

        sparql.setQuery(
            '''
            SELECT distinct ?item ?itemLabel ?countryLabel ?genderLabel ?birth ?image ?imdb
            WHERE {
            ?item wdt:P31 wd:Q5 .?item ?label "''' + str(name) + '''"@en .
            ?item wdt:P569 ?birth .
            ?item wdt:P27 ?country .
            ?item wdt:P18 ?image .
            ?item wdt:P21 ?gender .
            ?item wdt:P345 ?imdb .
            OPTIONAL {?item wdt:P570 ?death . }
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            }''')

        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            birth = result["birth"]["value"]
            birth = birth[:10]
            country = result["countryLabel"]["value"]
            gender = result["genderLabel"]["value"]
            image = result["image"]["value"]
            imdb = result["imdb"]["value"]

        sparql.setQuery(
            '''
            SELECT ?actor ?actorLabel ?award ?awardLabel ?date
            WHERE {
            ?actor wdt:P31 wd:Q5 .
            ?actor rdfs:label "''' + str(name) + '''"@en .
            ?actor p:P166 ?awardstat .
            ?awardstat ps:P166 ?award .
            ?awardstat pq:P585 ?date .
            ?awardstat pq:P1686 ?forWork .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
            }''')

        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        thisdict = dict()

        # If request fails (celebs)
        if not results["results"]["bindings"]:
            # "not_found" : "<script>alert('No information was found on the wikidata for this person.');</script>"

            sparql.setQuery(
                '''
                SELECT distinct ?item ?itemLabel ?countryLabel ?genderLabel ?birth ?death ?image ?imdb
                WHERE {
                ?item wdt:P31 wd:Q5 .?item ?label "''' + str(name) + '''"@en .
                ?item wdt:P569 ?birth .
                ?item wdt:P27 ?country .
                ?item wdt:P21 ?gender .
                ?item wdt:P345 ?imdb .
                SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
                }''')

            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            if not results["results"]["bindings"]:
                return render(request, 'celebrity-detail.html', {"name": name, "birth" : "Unspecified", "country" : "Unspecified", "gender" : "Unspecified", "filmography": movies_starring, "dict": thisdict, "imdb" : "Unspecified", "not_found" : "<script>alert('No information was found on the wikidata for this person.');</script>", "image" : "/static/assets/images/posters/blank.png"})

            for result in results["results"]["bindings"]:
                birth = result["birth"]["value"]
                birth = birth[:10]
                country = result["countryLabel"]["value"]
                gender = result["genderLabel"]["value"]
                imdb = result["imdb"]["value"]

            return render(request, 'celebrity-detail.html', {"name" : name, "birth" : birth, "country" : country, "gender" : gender, "filmography": movies_starring, "dict": thisdict, "imdb" : imdb})

        for result in results["results"]["bindings"]:
            a = result["awardLabel"]["value"]
            d = result["date"]["value"]
            thisdict[a] = d[:4]

        return render(request, 'celebrity-detail.html', {"name" : name, "birth" : birth, "country" : country, "gender" : gender, "filmography": movies_starring, "image" : image, "dict": thisdict, "imdb" : imdb})
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
            SELECT distinct ?name
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
        directors_to_list = list()

        for e in res['results']['bindings']:
           directors_to_list.append(e['name']['value'])

        sparql.setQuery('''
            SELECT distinct ?item ?itemLabel ?countryLabel ?date ?prodcoLabel ?len ?restrictLabel ?imdb ?image
            WHERE {
            ?item wdt:P31 wd:Q11424 .
            ?item ?label "''' + str(name) + '''"@en .
            ?item wdt:P3383 ?image .
            ?item wdt:P2047 ?len .
            ?item wdt:P3306 ?restrict .
            ?item wdt:P495 ?country .
            ?item wdt:P577 ?date .
            ?item wdt:P345 ?imdb .
            ?item wdt:P272 ?prodco . 
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
            } LIMIT 1 ''')

        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        # If query fails (movies)
        if not results["results"]["bindings"]:
            sparql.setQuery('''
            SELECT distinct ?item ?itemLabel ?countryLabel ?date ?prodcoLabel ?restrictLabel ?imdb
            WHERE {
            ?item wdt:P31 wd:Q11424 .
            ?item ?label "''' + str(name) + '''"@en .
            ?item wdt:P495 ?country .
            ?item wdt:P577 ?date .
            ?item wdt:P345 ?imdb .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
            } LIMIT 1 ''')

            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            if not results["results"]["bindings"]:
                return render(request, 'movie-detail.html', {"name": name, "len" : "Unspecified", "director": directors_to_list, "rel_date" : "Unspecified", "year" : "Unspecified", "country" : "Unspecified", "imdb" : "Unspecified", "cast" : cast_to_list, "prodCo" : "Unspecified", "image" : "/static/assets/images/posters/blank.png", "not_found" : "<script>alert('No information was found on the wikidata for this movie.');</script>"})

            for result in results["results"]["bindings"]:
                release_date = result['date']['value']
                country = result['countryLabel']['value']
                imdb = result['imdb']['value']

            return render(request, 'movie-detail.html', {"name": name, "len" : "Unspecified", "director": directors_to_list, "rel_date" : release_date[:10], "year" : (release_date[:10])[:4],"country" : country, "imdb" : imdb, "cast" : cast_to_list, "prodCo" : "Unspecified", "image" : "/static/assets/images/posters/blank.png"})
            # return render(request, 'movie-detail.html', {"name": name, "len" : "Unspecified","director" : directors_to_list, "rel_date" : "Unspecified", "cast" : cast_to_list, "country" : "Unspecified", "prodCo" : "Unspecified", "imdb" : "Unspecified"})

        for result in results["results"]["bindings"]:
            image = result['image']['value']
            release_date = result['date']['value']
            country = result['countryLabel']['value']
            prodCo = result['prodcoLabel']['value']
            length = result['len']['value']
            length = length+"m"
            imdb = result['imdb']['value']


        return render(request, 'movie-detail.html', {"name": name, "len" : length, "director": directors_to_list, "rel_date" : release_date[:10], "country" : country, "prodCo" : prodCo, "imdb" : imdb, "cast" : cast_to_list, "image" : image})
    else:
        return render(request, '404.html', {})