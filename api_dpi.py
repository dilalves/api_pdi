from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError

app = Flask(__name__)
CORS(app)  # Libera acesso para qualquer domínio (ajuste se necessário)

@app.route("/verificar-dpi", methods=["POST"])
def verificar_dpi():
    if 'arquivo' not in request.files:
        return jsonify({"ok": False, "erro": "Arquivo não enviado"}), 400

    file = request.files['arquivo']

    try:
        img = Image.open(file.stream)
        img.verify()  # Verifica se a imagem não está corrompida
        img = Image.open(file.stream)  # Reabre para uso após .verify()

        width, height = img.size
        dpi = img.info.get('dpi', (0, 0))
        dpi_x, dpi_y = dpi if isinstance(dpi, tuple) else (dpi, dpi)

        # Estimar DPI se ausente
        if dpi_x == 0 or dpi_y == 0:
            est_dpi_x = round(width / 8.27)
            est_dpi_y = round(height / 11.69)
            dpi_x, dpi_y = est_dpi_x, est_dpi_y

        return jsonify({
            "ok": dpi_x >= 200 and dpi_y >= 200,
            "dpi_x": dpi_x,
            "dpi_y": dpi_y,
            "largura": width,
            "altura": height
        })

    except UnidentifiedImageError:
        return jsonify({"ok": False, "erro": "Arquivo não é uma imagem válida."}), 400
    except Exception as e:
        return jsonify({"ok": False, "erro": "Erro interno: " + str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
