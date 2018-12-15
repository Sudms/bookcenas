import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient
from django.shortcuts import render, redirect
from django.http import HttpResponse
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint = "http://localhost:8000"
repo_name = "movies"

# QUERY https://query.wikidata.org/#SELECT%20distinct%20%3Fitem%20%3FitemLabel%20%3Foccupation%20%3Fcountry%20%3Fgender%20%3Fbirth%20%3Fdeath%20%3Fimage%20%0AWHERE%20%7B%0A%3Fitem%20wdt%3AP31%20wd%3AQ5%20.%0A%3Fitem%20%3Flabel%20%22Johnny%20Depp%22%40en%20.%0A%3Fitem%20wdt%3AP569%20%3Fbirth%20.%0A%3Fitem%20wdt%3AP106%20%3Foccupation%20.%0A%3Fitem%20wdt%3AP27%20%3Fcountry%20.%0A%3Fitem%20wdt%3AP18%20%3Fimage%20.%0A%3Fitem%20wdt%3AP21%20%3Fgender%20.%0AOPTIONAL%20%7B%3Fitem%20wdt%3AP570%20%3Fdeath%20.%7D%0A%0ASERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%0A%7D

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
                    }
                ''')

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
            SELECT distinct ?item ?itemLabel ?country ?gender ?birth ?death ?image 
            WHERE {
            ?item wdt:P31 wd:Q5 .?item ?label "''' + str(name) + '''"@en .
            ?item wdt:P569 ?birth .
            ?item wdt:P27 ?country .
            ?item wdt:P18 ?image .
            ?item wdt:P21 ?gender .
            OPTIONAL {?item wdt:P570 ?death .}
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            }
            ''')

        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            birth=result["birth"]["value"]
            birth=birth[:10]
            country=result["country"]["value"]
            gender=result["gender"]["value"]
            image=result["image"]["value"]

        sparql.setQuery(
            '''
            SELECT ?actor ?actorLabel ?award ?awardLabel ?date
            WHERE
            {
            # find a human
            ?actor wdt:P31 wd:Q5 .
            # with English label 
            ?actor rdfs:label "'''+str(name)+'''"@en .
            # Now comes the statements/qualifiers magic:
            # just applying what the documentation says https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries#Working_with_qualifiers
            # using this query as example https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries#US_presidents_and_their_spouses.2C_in_date_order
            ?actor p:P166 ?awardstatement .
            ?awardstatement ps:P166 ?award .
            ?awardstatement pq:P585 ?date .
            ?awardstatement pq:P1686 ?forWork .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr" . }
            }
            ''')

        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        thisdict = dict()

        for result in results["results"]["bindings"]:
            a=result["awardLabel"]["value"]
            d=result["date"]["value"]
            thisdict[a]= d[:4]     

        return render(request, 'celebrity-detail.html', {"name" : name, "birth" : birth, "country" : country, "gender" : gender,"filmography": movies_starring, "image" : image, "dict": thisdict})
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

        return render(request, 'movie-detail.html', {"name": name, "director": directors_to_list, "cast" : cast_to_list})
    else:
        return render(request, '404.html', {})