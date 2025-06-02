from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError
import traceback

app = Flask(__name__)
CORS(app)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
