from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class GetACForm(FlaskForm):
    institutions = [
        ("43ACC_UBG", "Universitätsbibliothek Graz"),
        ("43ACC_UBW", "Universitätsbibliothek Wien"),
    ]
    acnr = StringField("AC-Nummer: ", validators=[DataRequired()])
    institution_code = SelectField("Institution: ", choices=institutions)
    submit = SubmitField("Hierarchie anzeigen")
