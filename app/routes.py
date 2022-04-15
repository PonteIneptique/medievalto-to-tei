from flask import render_template, request, redirect, url_for, jsonify, Response
from app import app, db
from app.models import Doc, Page
from app.parser import parse_zip, page_to_tei


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


@app.route("/documents/<int:doc_id>/pages/<int:page_id>/tei", methods=["GET"])
def pages_tei(doc_id: int, page_id: int):
    doc = Doc.query.get_or_404(doc_id)
    page = Page.query.get_or_404(page_id)

    return Response(f"""<?xml version="1.0" encoding="UTF-8"?>
<div xmlns="http://www.tei-c.org/ns/1.0"><ab>{page_to_tei(page.page_content)}</ab></div>""",
                    mimetype="text/xml")
