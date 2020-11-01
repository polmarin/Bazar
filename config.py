import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    """ HEROKU """
    SQLALCHEMY_DATABASE_URI = "postgres://kgvepagzucjhff:ef0515374105afb98fbca8267669830958cc1398c411b32687ca845b94464860@ec2-54-166-114-48.compute-1.amazonaws.com:5432/ddobvv20sgirjf"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    """ LOCAL """
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')