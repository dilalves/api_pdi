from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)  # Libera acesso para qualquer domínio (você pode restringir depois)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
