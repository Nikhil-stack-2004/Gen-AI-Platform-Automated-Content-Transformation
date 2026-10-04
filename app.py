import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.utils import secure_filename

from PyPDF2 import PdfReader
from docx import Document

# =========================================================
# DATABASE
# =========================================================

from db import (
    init_database,
    create_user,
    get_user_by_email,
    verify_password
)

# =========================================================
# GENERATIVE AI
# =========================================================

from ai_engine import transform_content


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "gen-ai-content-transformation-secret-key"


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_database()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def extract_pdf_text(filepath):

    text = ""

    reader = PdfReader(filepath)

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"

    return text.strip()


def extract_docx_text(filepath):

    document = Document(filepath)

    paragraphs = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:

            paragraphs.append(text)

    return "\n".join(paragraphs)


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

        # Check empty fields

        if not username or not email or not password:

            flash(
                "Please fill in all fields."
            )

            return redirect(
                url_for("register")
            )

        # Check existing user

        existing_user = get_user_by_email(
            email
        )

        if existing_user:

            flash(
                "An account with this email already exists."
            )

            return redirect(
                url_for("register")
            )

        # Create user

        create_user(
            username,
            email,
            password
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

        # Find user

        user = get_user_by_email(
            email
        )

        # Verify password

        if user and verify_password(
            password,
            user["password"]
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["email"] = user["email"]

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password."
        )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",
        username=session.get("username")
    )


# =========================================================
# TEXT CONTENT TRANSFORMATION
# =========================================================

@app.route(
    "/transform",
    methods=["GET", "POST"]
)
def transform():

    # User must be logged in

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # GET request

    if request.method == "GET":

        return render_template(
            "transform.html",
            output=None,
            original_content=""
        )

    # Get form data

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

    # Validate content

    if not content:

        flash(
            "Please enter some content."
        )

        return redirect(
            url_for("transform")
        )

    # Call Generative AI

    try:

        output = transform_content(
            content=content,
            transformation=transformation,
            tone=tone,
            language=language
        )

    except Exception as e:

        print(
            "AI ERROR:",
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

    # Display result

    return render_template(
        "transform.html",
        output=output,
        original_content=content
    )


# =========================================================
# DOCUMENT TRANSFORMATION
# PDF + DOCX
# =========================================================

@app.route(
    "/document-transform",
    methods=["GET", "POST"]
)
@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def document_transform():

    # User must be logged in

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # GET request

    if request.method == "GET":

        return render_template(
            "document_transform.html",
            output=None,
            filename=None
        )

    # Get uploaded file

    file = request.files.get(
        "document"
    )

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

    # Check file

    if not file or file.filename == "":

        flash(
            "Please select a PDF or DOCX file."
        )

        return redirect(
            url_for("document_transform")
        )

    # Check extension

    if not allowed_file(
        file.filename
    ):

        flash(
            "Only PDF and DOCX files are supported."
        )

        return redirect(
            url_for("document_transform")
        )

    # Secure filename

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    # Save file

    try:

        file.save(filepath)

    except Exception as e:

        print(
            "FILE SAVE ERROR:",
            e
        )

        flash(
            "Unable to save the uploaded file."
        )

        return redirect(
            url_for("document_transform")
        )

    # Extract text

    try:

        extension = filename.rsplit(
            ".",
            1
        )[1].lower()

        if extension == "pdf":

            extracted_text = extract_pdf_text(
                filepath
            )

        elif extension == "docx":

            extracted_text = extract_docx_text(
                filepath
            )

        else:

            extracted_text = ""

    except Exception as e:

        print(
            "DOCUMENT EXTRACTION ERROR:",
            e
        )

        flash(
            "Unable to read the document."
        )

        return redirect(
            url_for("document_transform")
        )

    # Check extracted text

    if not extracted_text:

        flash(
            "No readable text was found in the document."
        )

        return redirect(
            url_for("document_transform")
        )

    # Send document text to Gemini

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
            "Unable to transform the document using AI."
        )

        return render_template(
            "document_transform.html",
            output=None,
            filename=filename
        )

    # Display result

    return render_template(
        "document_transform.html",
        output=output,
        filename=filename
    )


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
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )