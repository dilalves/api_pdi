from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import pytesseract

app = Flask(__name__)
CORS(app)  # Libera acesso para qualquer domínio (ajuste se necessário)

@app.route("/verificar-dpi", methods=["POST"])
def verificar_dpi():
    if 'arquivo' not in request.files:
        return jsonify({"ok": False, "erro": "Arquivo não enviado"}), 400

    file = request.files['arquivo']
    try:
        img = Image.open(file.stream)
        dpi = img.info.get('dpi', (0, 0))
        dpi_x, dpi_y = dpi if isinstance(dpi, tuple) else (dpi, dpi)

        return jsonify({
            "ok": dpi_x >= 200 and dpi_y >= 200,
            "dpi_x": dpi_x,
            "dpi_y": dpi_y
        })
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/ocr", methods=["POST"])
def extrair_texto():
    if 'arquivo' not in request.files:
        return jsonify({"ok": False, "erro": "Arquivo não enviado"}), 400

    file = request.files['arquivo']
    try:
        img = Image.open(file.stream)
        texto = pytesseract.image_to_string(img, lang="por")

        # Simples tentativa de extrair possíveis padrões de nome e tipo de prova
        linhas = texto.split("\n")
        linhas_limpa = [linha.strip() for linha in linhas if linha.strip()]
        nome = ""
        tipo_prova = ""

        for linha in linhas_limpa:
            if "nome" in linha.lower():
                nome = linha
            if "tipo" in linha.lower() or "prova" in linha.lower():
                tipo_prova = linha

        return jsonify({
            "ok": True,
            "texto_completo": texto,
            "nome_detectado": nome,
            "tipo_prova_detectado": tipo_prova
        })
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
