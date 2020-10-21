from app import app, db
from app.models import Product, Price, Search

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Product': Product, 'Price' : Price, 'Search' : Search}