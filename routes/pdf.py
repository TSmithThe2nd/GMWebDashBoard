"""
routes/pdf.py — PDF upload and parsing routes

POST /parse-pdf   → parse a D&D Beyond character sheet PDF
POST /pdf-fields  → diagnostic: list all form fields in a PDF
"""

import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify
from parsers.ddb import parse_pdf_file

pdf_bp = Blueprint('pdf', __name__)

# Set by create_app()
DATA_DIR: Path = Path('data')


@pdf_bp.route('/parse-pdf', methods=['POST'])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    # Unique tmp file per request — prevents collisions between concurrent uploads
    tmp_path = DATA_DIR / f'tmp_{uuid.uuid4().hex}.pdf'

    try:
        file.save(tmp_path)
        result = parse_pdf_file(tmp_path)
    except Exception as e:
        result = {'error': str(e)}
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass

    if result.get('fatal'):
        return jsonify(result), 422

    if not result or (len(result) <= 2 and 'error' in result):
        return jsonify({
            'error': 'Could not extract data. Try re-exporting from D&D Beyond, or use text paste.'
        }), 422

    return jsonify(result)


@pdf_bp.route('/pdf-fields', methods=['POST'])
def pdf_fields():
    """Diagnostic: shows all form field names found in a PDF."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']
    tmp_path = DATA_DIR / f'tmp_diag_{uuid.uuid4().hex}.pdf'
    file.save(tmp_path)
    result = {}

    try:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(tmp_path), strict=False)
            result['form_fields'] = list((reader.get_form_text_fields() or {}).keys())
            result['pages'] = len(reader.pages)
        except ImportError:
            result['form_fields'] = []

        try:
            import pdfplumber
            with pdfplumber.open(str(tmp_path)) as pdf:
                result['text_sample'] = (pdf.pages[0].extract_text() or '')[:500]
        except ImportError:
            pass
    except Exception as e:
        result['error'] = str(e)
    finally:
        try: tmp_path.unlink()
        except: pass

    return jsonify(result)
