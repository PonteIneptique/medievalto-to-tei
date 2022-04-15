import csv
import io

from flask import render_template, request, redirect, url_for, jsonify, Response
from app import app, db
from app.models import Doc, Page
from app.parser import parse_zip, page_to_tei, get_all_abbreviations, apply_abbreviations


@app.route("/")
def index():
    return render_template("pages/index.html", docs=Doc.query.all())


@app.route("/documents/add", methods=["GET", "POST"])
def docs_add():
    if request.method == 'POST':
        error = False
        if "docZip" not in request.files:
            error = True
        document = Doc(doc_title=request.form["docTitle"])
        db.session.add(document)
        db.session.flush()
        for file, content in parse_zip(request.files["docZip"]):
            db.session.add(Page(
                doc_id=document.doc_id,
                page_title=file,
                page_content=content
            ))
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("pages/create.html")


@app.route("/documents/<int:doc_id>/pages")
def pages_all(doc_id: int):
    doc = Doc.query.get_or_404(doc_id)
    pages = Page.query.filter(Page.doc_id == doc.doc_id).all()
    return render_template("pages/pages.html", doc=doc, pages=pages)


@app.route("/documents/<int:doc_id>/pages/<int:page_id>", methods=["GET", "POST"])
def pages_get(doc_id: int, page_id: int):
    doc = Doc.query.get_or_404(doc_id)
    page = Page.query.get_or_404(page_id)
    # ToDo: Security (page should be linked to doc)

    if request.method == "POST":
        if not request.form.get("content"):
            return jsonify({"status": False})
        page.page_content = request.form.get("content")
        db.session.add(page)
        db.session.commit()
        return jsonify({"status": True})

    return render_template("pages/edit.html", doc=doc, page=page)


@app.route("/documents/<int:doc_id>/pages/<int:page_id>/tei")
def pages_tei(doc_id: int, page_id: int):
    doc = Doc.query.get_or_404(doc_id)
    page = Page.query.get_or_404(page_id)

    return Response(f"""<?xml version="1.0" encoding="UTF-8"?>
<div xmlns="http://www.tei-c.org/ns/1.0">\n\t<ab>{page_to_tei(page.page_content)}\n\t</ab>\n</div>""",
                    mimetype="text/xml")


@app.route("/documents/<int:doc_id>/table")
def doc_abbr(doc_id: int):
    doc = Doc.query.get_or_404(doc_id)
    pages = Page.query.filter(Page.doc_id == doc.doc_id).all()
    abbrs = get_all_abbreviations([page.page_content for page in pages])
    if request.args.get("download") == "json":
        return jsonify(abbrs)
    elif request.args.get("download") == "csv":
        file = io.StringIO()
        writer = csv.writer(file)
        writer.writerow(["Abbreviation", "Resolution", "Count"])
        for abb, resolutions in abbrs.items():
            for (res, res_count) in resolutions.items():
                writer.writerow([abb, res, str(res_count)])
        file.seek(0)
        return Response(file.read(), mimetype="text/csv", headers={
            'Content-Disposition': 'attachment; filename="abbreviation.csv"'
        })
    return render_template(
        "pages/table.html",
        doc=doc,
        abbrs=abbrs
    )


@app.route("/documents/<int:doc_id>/table/apply")
def doc_apply_abbrs(doc_id: int):
    doc = Doc.query.get_or_404(doc_id)
    pages = Page.query.filter(Page.doc_id == doc.doc_id).all()
    abbrs = get_all_abbreviations([page.page_content for page in pages])
    modifications = apply_abbreviations(pages, abbreviations=abbrs)
    nb_modifications = sum([
        amount
        for changes in modifications.values()
        for _abbreviations in changes.values()
        for amount in _abbreviations.values()
    ])
    if len(abbrs):
        db.session.bulk_save_objects([
            page
            for page in pages
            if page.page_title in modifications
        ])
        db.session.commit()
    return render_template(
        "pages/table-applied.html",
        doc=doc,
        modifications=modifications,
        nb_modifications=nb_modifications
    )
