from flask import render_template, url_for, redirect, request
from app import app, obj
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
        print(acnr)
        return redirect(url_for("hierarchy", acnr=acnr))
    return render_template("index.html", title="Bitte AC-Nummer eingeben", form=form, message=message)

@app.route("/hierarchy")
def hierarchy():
    acnr = request.args["acnr"]
    hierarchy = obj.BibHierarchy(acnr)

    if hierarchy.records is None:
        message = f'Die Suche nach "{acnr}" erbrachte keine Ergebnisse. Haben Sie sich vielleicht vertippt?'
    elif len(hierarchy.records) == 1:
        message = f"{acnr} hat keine abhängigen Datensätze."
    else:
        return render_template("hierarchy.html",
                               hierarchy=hierarchy.as_list_of_dicts(),
                               number_of_deps=str(len(hierarchy.deps)))

    return redirect(url_for("index", message=message))

    # redirect(url_for("index"))
