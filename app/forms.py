from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class GetACForm(FlaskForm):
    institutions = [
        ("43ACC_UBG", "Universitätsbibliothek Graz"),
        ("43ACC_UBW", "Universitätsbibliothek Wien"),
        ("43ACC_UBI", "Universitätsbibliothek Innsbruck"),
        ("43ACC_ONB", "Österreichische Nationalbibliothek"),
        ("43ACC_UBBW", "Universitätsbibliothek Bodenkultur Wien"),
        ("43ACC_UBK", "Universitätsbibliothek Klagenfurt"),
        ("43ACC_TUG", "Technische Universität Graz"),
        ("43ACC_C02", "FH Campus 02"),
        ("43ACC_VBK", "VBK"),
        ("43ACC_AKW", "Arbeiterkammerbibliothek Wien"),
        ("43ACC_OOELB", "LBO"),
        ("43ACC_WUW", "Wirtschaftsuniversität Wien"),
        ("43ACC_OEAW", "ÖAW"),
        ("43ACC_KLK", "Kärntner Landesbibliothek"),
        ("43ACC_FHB", "Fachhochschule Burgenland"),
        ("43ACC_WIENB", "Wienbibliothek im Rathaus"),
        ("43ACC_TUW", "TU Wien"),
        ("43ACC_GDFS", "Campusbibliotheken St. Pölten"),
        ("43ACC_UBL", "Universitätsbibliothek Linz"),
        ("43ACC_VUW", "Veterinärmedizinische Universität Wien"),
        ("43ACC_UGL", "Kunstuniversität Linz"),
        ("43ACC_DLI", "Diözesanbibliothek Linz"),
        ("43ACC_ABP", "Anton Bruckner Privatuniversität"),
        ("43ACC_UBMS", "Universitätsbibliothek Mozarteum Salzburg"),
        ("43ACC_BFI", "Fachhochschule des BFI Wien"),
    ]
    acnr = StringField("AC-Nummer: ", validators=[DataRequired()])
    institution_code = SelectField("Institution: ", choices=institutions)
    submit = SubmitField("Hierarchie anzeigen")
