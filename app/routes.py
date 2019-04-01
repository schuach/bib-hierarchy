from flask import render_template, url_for, redirect, request, session
from app import app, bib_hierarchy
from app.forms import GetACForm

@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    if request.args:
        message = request.args["message"]
    else:
        message = None

    form = GetACForm()
    if form.validate_on_submit():
        acnr = form.acnr.data.strip()
        session['institution_code'] = form.institution_code.data
        print(acnr)
        return redirect(url_for("hierarchy", acnr=acnr))
    return render_template("index.html", title="Bitte AC-Nummer eingeben", form=form, message=message)

@app.route("/hierarchy")
def hierarchy():
    acnr = request.args["acnr"]
    if request.args["institution_code"]:
        institution_code = request.args["institution_code"]
    else:
        institution_code = session["institution_code"]

    hierarchy = bib_hierarchy.BibHierarchy(acnr, institution_code)

    if hierarchy.records is None:
        message = f'Die Suche nach "{acnr}" erbrachte keine Ergebnisse. Haben Sie sich vielleicht vertippt?'
    elif len(hierarchy.records) == 1:
        message = f"{acnr} hat keine abhängigen Datensätze."
    else:
        return render_template("hierarchy.html",
                               hierarchy=hierarchy.as_list(),
                               number_of_deps=str(len(hierarchy.deps)))

    return redirect(url_for("index", message=message))

    # redirect(url_for("index"))
