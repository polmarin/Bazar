from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired

class AddSearchForm(FlaskForm):
    name = StringField('Search', validators=[DataRequired()])
    category = StringField('Category')
    max_price = FloatField('Max Price', validators=[DataRequired()])
    submit = SubmitField('Sign In')