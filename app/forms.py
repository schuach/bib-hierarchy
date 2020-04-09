from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class GetACForm(FlaskForm):
    institutions = [
        ("43ACC_UBG", "Universitätsbibliothek Graz"),
        ("43ACC_UBW", "Universitätsbibliothek Wien"),
        ("43ACC_UBI", "Universitätsbibliothek Innsbruck"),
        ("43ACC_ONB", "Österreichische Nationalbibliothek")
    ]
    acnr = StringField("AC-Nummer: ", validators=[DataRequired()])
    institution_code = SelectField("Institution: ", choices=institutions)
    submit = SubmitField("Hierarchie anzeigen")
