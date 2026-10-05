from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import os
from werkzeug.utils import secure_filename

from db import (
    init_database,
    create_user,
    get_user_by_email,
    verify_password
)

from ai_engine import transform_content


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "gen-ai-content-transformation-secret-key"


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# DATABASE
# =========================================================

init_database()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


def login_required():

    return "user_id" in session


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not username:

            flash(
                "Please enter your username."
            )

            return redirect(
                url_for("register")
            )

        if not email:

            flash(
                "Please enter your email."
            )

            return redirect(
                url_for("register")
            )

        if not password:

            flash(
                "Please enter your password."
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters."
            )

            return redirect(
                url_for("register")
            )

        # ---------------------------------------------
        # CHECK EXISTING USER
        # ---------------------------------------------

        existing_user = get_user_by_email(
            email
        )

        if existing_user:

            flash(
                "An account with this email already exists. "
                "Please login."
            )

            return redirect(
                url_for("login")
            )

        # ---------------------------------------------
        # CREATE USER
        # ---------------------------------------------

        try:

            create_user(
                username,
                email,
                password
            )

        except Exception as e:

            print(
                "REGISTRATION ERROR:",
                e
            )

            flash(
                "Unable to create account."
            )

            return redirect(
                url_for("register")
            )

        flash(
            "Registration successful. Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not email or not password:

            flash(
                "Please enter both email and password."
            )

            return render_template(
                "login.html"
            )

        # ---------------------------------------------
        # FIND USER
        # ---------------------------------------------

        user = get_user_by_email(
            email
        )

        # ---------------------------------------------
        # VERIFY PASSWORD
        # ---------------------------------------------

        if user:

            try:

                password_valid = verify_password(
                    password,
                    user["password"]
                )

            except Exception as e:

                print(
                    "PASSWORD VERIFICATION ERROR:",
                    e
                )

                password_valid = False

        else:

            password_valid = False

        # ---------------------------------------------
        # LOGIN SUCCESS
        # ---------------------------------------------

        if user and password_valid:

            session.clear()

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["email"] = user["email"]

            session.permanent = False

            return redirect(
                url_for("dashboard")
            )

        # ---------------------------------------------
        # LOGIN FAILED
        # ---------------------------------------------

        flash(
            "Invalid email or password."
        )

        return render_template(
            "login.html"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",
        username=session.get(
            "username"
        )
    )


# =========================================================
# TEXT TRANSFORMATION
# =========================================================

@app.route(
    "/transform",
    methods=["GET", "POST"]
)
def transform():

    if not login_required():

        return redirect(
            url_for("login")
        )

    # ---------------------------------------------
    # GET
    # ---------------------------------------------

    if request.method == "GET":

        return render_template(
            "transform.html",
            output=None,
            original_content=""
        )

    # ---------------------------------------------
    # FORM DATA
    # ---------------------------------------------

    content = request.form.get(
        "content",
        ""
    ).strip()

    transformation = request.form.get(
        "transformation",
        "Summarize"
    )

    tone = request.form.get(
        "tone",
        "Professional"
    )

    language = request.form.get(
        "language",
        "English"
    )

    # ---------------------------------------------
    # VALIDATION
    # ---------------------------------------------

    if not content:

        flash(
            "Please enter some content."
        )

        return render_template(
            "transform.html",
            output=None,
            original_content=""
        )

    # ---------------------------------------------
    # AI
    # ---------------------------------------------

    try:

        output = transform_content(
            content=content,
            transformation=transformation,
            tone=tone,
            language=language
        )

    except Exception as e:

        print(
            "TEXT AI ERROR:",
            e
        )

        flash(
            "Unable to generate AI content. "
            "Please check your Gemini API configuration."
        )

        return render_template(
            "transform.html",
            output=None,
            original_content=content
        )

    # ---------------------------------------------
    # RESULT
    # ---------------------------------------------

    return render_template(
        "transform.html",
        output=output,
        original_content=content
    )


# =========================================================
# DOCUMENT TRANSFORMATION
# =========================================================

@app.route(
    "/document-transform",
    methods=["GET", "POST"]
)
def document_transform():

    if not login_required():

        return redirect(
            url_for("login")
        )

    # ---------------------------------------------
    # GET
    # ---------------------------------------------

    if request.method == "GET":

        return render_template(
            "document_transform.html",
            output=None,
            filename=None
        )

    # ---------------------------------------------
    # FILE
    # ---------------------------------------------

    file = request.files.get(
        "document"
    )

    if not file:

        flash(
            "Please select a PDF or DOCX file."
        )

        return redirect(
            url_for("document_transform")
        )

    if not file.filename:

        flash(
            "Please select a file."
        )

        return redirect(
            url_for("document_transform")
        )

    # ---------------------------------------------
    # FILE TYPE
    # ---------------------------------------------

    if not allowed_file(
        file.filename
    ):

        flash(
            "Only PDF and DOCX files are supported."
        )

        return redirect(
            url_for("document_transform")
        )

    # ---------------------------------------------
    # FORM DATA
    # ---------------------------------------------

    transformation = request.form.get(
        "transformation",
        "Summarize"
    )

    tone = request.form.get(
        "tone",
        "Professional"
    )

    language = request.form.get(
        "language",
        "English"
    )

    # ---------------------------------------------
    # SAVE FILE
    # ---------------------------------------------

    filename = secure_filename(
        file.filename
    )

    # Prevent empty filename
    if not filename:

        flash(
            "Invalid filename."
        )

        return redirect(
            url_for("document_transform")
        )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    try:

        file.save(
            filepath
        )

    except Exception as e:

        print(
            "FILE SAVE ERROR:",
            e
        )

        flash(
            "Unable to save uploaded file."
        )

        return redirect(
            url_for("document_transform")
        )

    # ---------------------------------------------
    # EXTRACT TEXT
    # ---------------------------------------------

    extracted_text = ""

    try:

        extension = filename.rsplit(
            ".",
            1
        )[1].lower()

        # =========================================
        # PDF
        # =========================================

        if extension == "pdf":

            from PyPDF2 import PdfReader

            reader = PdfReader(
                filepath
            )

            pages = []

            for page in reader.pages:

                text = page.extract_text()

                if text:

                    pages.append(
                        text
                    )

            extracted_text = "\n".join(
                pages
            )

        # =========================================
        # DOCX
        # =========================================

        elif extension == "docx":

            from docx import Document

            document = Document(
                filepath
            )

            paragraphs = []

            for paragraph in document.paragraphs:

                text = paragraph.text.strip()

                if text:

                    paragraphs.append(
                        text
                    )

            extracted_text = "\n".join(
                paragraphs
            )

    except Exception as e:

        print(
            "DOCUMENT EXTRACTION ERROR:",
            e
        )

        flash(
            "Unable to read the uploaded document."
        )

        return render_template(
            "document_transform.html",
            output=None,
            filename=filename
        )

    # ---------------------------------------------
    # CHECK TEXT
    # ---------------------------------------------

    extracted_text = extracted_text.strip()

    if not extracted_text:

        flash(
            "No readable text was found in the document."
        )

        return render_template(
            "document_transform.html",
            output=None,
            filename=filename
        )

    # ---------------------------------------------
    # GENERATIVE AI
    # ---------------------------------------------

    try:

        output = transform_content(
            content=extracted_text,
            transformation=transformation,
            tone=tone,
            language=language
        )

    except Exception as e:

        print(
            "DOCUMENT AI ERROR:",
            e
        )

        flash(
            "Unable to generate AI content. "
            "Please check your Gemini API configuration."
        )

        return render_template(
            "document_transform.html",
            output=None,
            filename=filename
        )

    # ---------------------------------------------
    # DISPLAY OUTPUT
    # ---------------------------------------------

    return render_template(
        "document_transform.html",
        output=output,
        filename=filename
    )


# =========================================================
# UPLOAD ALIAS
# =========================================================
#
# This fixes:
#
# http://127.0.0.1:5000/upload
#
# =========================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    return document_transform()


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 10 MB."
    )

    return redirect(
        url_for("document_transform")
    )


# =========================================================
# GENERAL ERROR
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    print(
        "INTERNAL SERVER ERROR:",
        error
    )

    flash(
        "Something went wrong. Please try again."
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )