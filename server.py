try:
    from flask import Flask, send_from_directory, make_response
except ImportError:
    print("You don't have Flask installed, run `$ pip3 install flask` and try again")
    exit(1)

import os

static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), './')
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 año por defecto
app.config['DEBUG'] = False  # Desactivado para rendimiento

# Compresión gzip mediante decorador de respuesta
from io import BytesIO
import gzip
from flask import request

@app.after_request
def compress_response(response):
    """Comprime respuestas con gzip para reducir el tamaño de transferencia."""
    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_encoding.lower():
        return response
    if response.direct_passthrough:
        return response
    if response.content_length and response.content_length < 500:
        return response  # No comprimir respuestas muy pequeñas
    if response.mimetype and not response.mimetype.startswith(('text/', 'application/json', 'application/javascript', 'image/svg+xml')):
        return response

    # Verificar que la respuesta no esté ya comprimida
    if response.content_encoding and 'gzip' in response.content_encoding:
        return response

    # Obtener datos de la respuesta
    data = response.get_data()
    if data and len(data) > 500:
        gzip_buffer = BytesIO()
        gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
        gzip_file.write(data)
        gzip_file.close()
        response.set_data(gzip_buffer.getvalue())
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(gzip_buffer.getvalue())
        response.vary.add('Accept-Encoding')
    return response


# Serving the index file
@app.route('/', methods=['GET'])
def serve_dir_directory_index():
    if os.path.exists("index.html"):
        response = make_response(send_from_directory(static_file_dir, 'index.html'))
        response.cache_control.max_age = 3600  # HTML: 1 hora
        response.cache_control.public = True
        return response
    else:
        return "<h1 align='center'>404</h1><h2 align='center'>Missing index.html file</h2><p align='center'><img src='https://github.com/4GeeksAcademy/html-hello/blob/main/.vscode/rigo-baby.jpeg?raw=true' /></p>"

# Serving any other file (con caché según tipo)
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = os.path.join(path, 'index.html')
    response = make_response(send_from_directory(static_file_dir, path))
    # Cachear assets estáticos por 1 año (tienen hash en nombre o son inmutables)
    if path.endswith(('.svg', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf')):
        response.cache_control.max_age = 31536000  # 1 año
        response.cache_control.public = True
    else:
        response.cache_control.max_age = 3600  # 1 hora
        response.cache_control.public = True
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
