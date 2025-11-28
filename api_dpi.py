from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError
import traceback
import os
import tempfile
import subprocess

app = Flask(__name__)
CORS(app)

# Token opcional pra proteger a rota /docx2pdf (usado pelo PHP)
DOCX2PDF_TOKEN = os.environ.get("DOCX2PDF_TOKEN", "")

def check_auth(req):
    """
    Autenticação bem simples para a rota /docx2pdf.
    Se DOCX2PDF_TOKEN não estiver definido, libera geral.
    Se estiver definido, exige header:
        Authorization: Bearer <DOCX2PDF_TOKEN>
    """
    if not DOCX2PDF_TOKEN:
        return True
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {DOCX2PDF_TOKEN}"


# ---------------------------------------------------
#  ROTA EXISTENTE - VERIFICAR DPI
# ---------------------------------------------------
@app.route("/verificar-dpi", methods=["POST"])
def verificar_dpi():
    if 'arquivo' not in request.files:
        return jsonify({
            "ok": False,
            "dpi_x": 0,
            "dpi_y": 0,
            "largura": 0,
            "altura": 0,
            "erro": "Arquivo não enviado."
        }), 400

    file = request.files['arquivo']
    try:
        img = Image.open(file.stream)
        img.verify()
        file.stream.seek(0)
        img = Image.open(file.stream)

        width, height = img.size
        dpi = img.info.get('dpi', (0, 0))
        dpi_x, dpi_y = dpi if isinstance(dpi, tuple) else (dpi, dpi)

        # Se DPI estiver ausente, estimar
        if dpi_x == 0 or dpi_y == 0:
            est_dpi_x = round(width / 8.27)
            est_dpi_y = round(height / 11.69)
            dpi_x, dpi_y = est_dpi_x, est_dpi_y

        # Validação por DPI OU por tamanho compatível com A4 300DPI
        is_size_compatível = abs(width - 2480) <= 5 and abs(height - 3507) <= 5
        aprovado = (dpi_x >= 200 and dpi_y >= 200) or is_size_compatível

        return jsonify({
            "ok": aprovado,
            "dpi_x": dpi_x,
            "dpi_y": dpi_y,
            "largura": width,
            "altura": height
        })

    except UnidentifiedImageError:
        return jsonify({
            "ok": False,
            "dpi_x": 0,
            "dpi_y": 0,
            "largura": 0,
            "altura": 0,
            "erro": "Arquivo não é uma imagem válida."
        }), 400

    except Exception as e:
        print("ERRO INTERNO:", traceback.format_exc())
        return jsonify({
            "ok": False,
            "dpi_x": 0,
            "dpi_y": 0,
            "largura": 0,
            "altura": 0,
            "erro": "Erro interno: " + str(e)
        }), 500


# ---------------------------------------------------
#  NOVA ROTA - CONVERSÃO DOCX -> PDF
# ---------------------------------------------------
@app.route("/docx2pdf", methods=["POST"])
def docx2pdf():
    # Autenticação simples opcional
    if not check_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"ok": False, "error": "arquivo não enviado (file)"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"ok": False, "error": "nome de arquivo vazio"}), 400

    # Aceita só .docx
    if not f.filename.lower().endswith(".docx"):
        return jsonify({"ok": False, "error": "somente arquivos .docx são aceitos"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, "input.docx")
            f.save(docx_path)

            # Comando LibreOffice para converter DOCX -> PDF
            # IMPORTANTE: precisa ter 'libreoffice' instalado no container.
            cmd = [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", tmpdir,
                docx_path,
            ]

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )

            if proc.returncode != 0:
                print("ERRO LIBREOFFICE:", proc.stderr.decode(errors="ignore"))
                return jsonify({"ok": False, "error": "falha na conversão"}), 500

            # Em algumas versões o nome de saída não é exatamente input.pdf,
            # então vamos procurar qualquer .pdf gerado no diretório temporário.
            pdf_files = [
                os.path.join(tmpdir, name)
                for name in os.listdir(tmpdir)
                if name.lower().endswith(".pdf")
            ]

            if not pdf_files:
                return jsonify({"ok": False, "error": "pdf não foi gerado"}), 500

            pdf_path = pdf_files[0]

            # Devolve o PDF binário
            return send_file(
                pdf_path,
                mimetype="application/pdf",
                as_attachment=False
            )

    except Exception as e:
        print("ERRO /docx2pdf:", traceback.format_exc())
        return jsonify({"ok": False, "error": "erro interno: " + str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
