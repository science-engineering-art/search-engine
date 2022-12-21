from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from traitlets import FuzzyEnum
from models.kmeans_based_model import  VectorModelKMEANS

from models.boolean_model import BooleanModel
from models.corpus import Corpus
from models.fuzzy_model import FuzzyModel
from models.vector_model import VectorModel
from models.kmeans_based_model import VectorModelKMEANS
from models.relevance_feedback import RelevanceFeedback
import dictdatabase as ddb

class DocumentDto(BaseModel):
    doc_id: str
    title: str
    author: str
    text: str
    score: float

ddb.config.storage_directory = '../ddb_storage'

corpus = {
    'cranfield': Corpus('cranfield'),
    'vaswani': Corpus('vaswani'),
    'cord19': Corpus('cord19/trec-covid/round1')
}

models = {
    'vector': {
        'cranfield': VectorModel(corpus['cranfield']),
        'vaswani': 'VectorModel(corpus[\'vaswani\'])',
        'cord19': 'VectorModel(corpus[\'cord19\'])'
    },
    'boolean': {
        'cranfield': 'BooleanModel(corpus[\'cranfield\'])',
        'vaswani': 'BooleanModel(corpus[\'vaswani\'])',
        'cord19': 'BooleanModel(corpus[\'cord19\'])' 
    },
    'fuzzy': {
        'cranfield': 'FuzzyModel(corpus[\'cranfield\'])',
        'vaswani': 'FuzzyModel(corpus[\'vaswani\'])',
        # 'cord19': 'FuzzyModel(corpus['cord19'])'
    },
    'clustering' : {
        'cranfield': 'VectorModelKMEANS(\'cranfield\')'
    }
}


app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=origins,
    allow_headers=origins,
)

@app.get("/search")
async def root(model: str, dataset: str, query: str, pag: int = 1):
    result = []  
    pag -= 1

    if model in feedback and query in feedback[model][dataset].queries:
        ranking = feedback[model][dataset].search(query)
    else:
        if type(models[model][dataset]) == str:
            models[model][dataset] = eval(models[model][dataset])
        ranking = models[model][dataset].search(query)

    for tuple in ranking[10*pag:10*pag + 10]:
        doc = corpus[dataset].get_doc(tuple[1])
        result.append(DocumentDto(doc_id=doc['doc_id'], 
            title=doc['title'], author=doc['author'], 
            text=doc['text'], score=tuple[0]))
    
    return { "results": result }

feedback = {
    'vector': {
        'cranfield': RelevanceFeedback(models['vector']['cranfield'])
    }
} 

@app.get('/feedback')
async def feedbackController(
    model: str, dataset: str, query: str, doc_id: str, is_rel: bool, pag: int):

    feedback[model][dataset].add_relevance(query, doc_id, is_rel)

    result = []    

    for tuple in feedback[model][dataset].search(query)[10*pag: 10*pag + 10]:
        doc = corpus[dataset].get_doc(tuple[1])
        result.append(DocumentDto(doc_id=doc['doc_id'], 
            title=doc['title'], author=doc['author'], 
            text=doc['text'], score=tuple[0]))

    return { "results": result }