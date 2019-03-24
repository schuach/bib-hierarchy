from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class GetACForm(FlaskForm):
    acnr = StringField("AC-Nummer: ", validators=[DataRequired()])
    submit = SubmitField("Hierarchie anzeigen")
