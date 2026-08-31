from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
# Permitir peticiones desde el frontend (CORS)
CORS(app)

from flask import send_from_directory

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'cobranzas.db')

def get_db_connection():
    """Crea una conexión a SQLite y devuelve filas accesibles por nombre de columna (diccionarios)."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# 1. ENDPOINTS PARA ANDE
# ==========================================

@app.route('/api/ande/<int:nis>', methods=['GET'])
def consultar_ande(nis):
    """Consulta la factura de ANDE por NIS."""
    conn = get_db_connection()
    factura = conn.execute(
        'SELECT * FROM ande_facturas WHERE nis = ?', (nis,)
    ).fetchone()
    conn.close()

    if factura is None:
        return jsonify({"error": "No se encontro ninguna factura con ese NIS."}), 404

    return jsonify(dict(factura)), 200


@app.route('/api/ande/pagar', methods=['POST'])
def pagar_ande():
    """Procesa el pago de una factura de ANDE."""
    datos = request.get_json()
    nis = datos.get('nis')
    metodo_pago = datos.get('metodo_pago', 'Efectivo')

    if not nis:
        return jsonify({"error": "El NIS es obligatorio."}), 400

    conn = get_db_connection()
    factura = conn.execute('SELECT * FROM ande_facturas WHERE nis = ?', (nis,)).fetchone()

    if factura is None:
        conn.close()
        return jsonify({"error": "Factura no encontrada."}), 404

    if factura['estado_pago'] == 'Pagado':
        conn.close()
        return jsonify({"error": "Esta factura ya fue pagada."}), 400

    # 1. Actualizar estado de la factura
    conn.execute('UPDATE ande_facturas SET estado_pago = "Pagado" WHERE nis = ?', (nis,))

    # 2. Registrar en historial de transacciones
    query_log = 'INSERT INTO transacciones_pagos (servicio, identificador_cliente, monto_pagado, metodo_pago, referencia) VALUES (?, ?, ?, ?, ?)'
    conn.execute(query_log, ('ANDE', str(nis), factura['monto_total'], metodo_pago, f"Pago Factura NIS {nis}"))

    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Pago de ANDE realizado con exito.",
        "monto_pagado": factura['monto_total'],
        "cliente": factura['nombre_cliente']
    }), 200


# ==========================================
# 2. ENDPOINTS PARA BANCO UNO - PRESTAMOS
# ==========================================

@app.route('/api/banco/prestamos/<cedula>', methods=['GET'])
def consultar_prestamos(cedula):
    """Consulta todas las cuotas de préstamos asociadas a una cédula."""
    conn = get_db_connection()
    cuotas = conn.execute(
        'SELECT * FROM banco_prestamos WHERE cedula = ? AND estado = "Pendiente" ORDER BY num_cuota ASC',
        (cedula,)
    ).fetchall()
    conn.close()

    if not cuotas:
        return jsonify({"error": "No se encontraron prestamos pendientes para esta cedula."}), 404

    resultado = []
    for c in cuotas:
        item = dict(c)
        item['monto_total_cuota'] = item['monto_capital'] + item['monto_interes']
        resultado.append(item)

    return jsonify(resultado), 200


@app.route('/api/banco/prestamos/pagar', methods=['POST'])
def pagar_prestamo():
    """Paga una o mas cuotas seleccionadas de un préstamo."""
    datos = request.get_json()
    ids_cuotas = datos.get('ids_cuotas', [])
    metodo_pago = datos.get('metodo_pago', 'Efectivo')

    if not ids_cuotas:
        return jsonify({"error": "Debe seleccionar al menos una cuota para pagar."}), 400

    conn = get_db_connection()
    placeholders = ','.join('?' for _ in ids_cuotas)
    cuotas = conn.execute(
        f'SELECT * FROM banco_prestamos WHERE id_cuota IN ({placeholders}) AND estado = "Pendiente"',
        ids_cuotas
    ).fetchall()

    if not cuotas:
        conn.close()
        return jsonify({"error": "Las cuotas seleccionadas no existen o ya estan pagadas."}), 400

    monto_total_acumulado = 0
    cliente = cuotas[0]['nombre_cliente']
    prestamo = cuotas[0]['num_prestamo']

    for c in cuotas:
        monto_cuota = c['monto_capital'] + c['monto_interes']
        monto_total_acumulado += monto_cuota
        conn.execute('UPDATE banco_prestamos SET estado = "Pagado" WHERE id_cuota = ?', (c['id_cuota'],))

    query_log = 'INSERT INTO transacciones_pagos (servicio, identificador_cliente, monto_pagado, metodo_pago, referencia) VALUES (?, ?, ?, ?, ?)'
    conn.execute(query_log, ('Banco UNO - Prestamos', cuotas[0]['cedula'], monto_total_acumulado, metodo_pago, f"Pago de {len(cuotas)} cuota(s) de {prestamo}"))

    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": f"Se pagaron con exito {len(cuotas)} cuota(s).",
        "monto_total_pagado": monto_total_acumulado,
        "cliente": cliente,
        "prestamo": prestamo
    }), 200


# ==========================================
# 3. ENDPOINTS PARA BANCO UNO - TARJETAS
# ==========================================

@app.route('/api/banco/tarjetas/<num_tarjeta>', methods=['GET'])
def consultar_tarjeta(num_tarjeta):
    """Consulta estado de tarjeta de crédito."""
    conn = get_db_connection()
    tarjeta = conn.execute(
        'SELECT * FROM banco_tarjetas WHERE num_tarjeta = ?', (num_tarjeta,)
    ).fetchone()
    conn.close()

    if tarjeta is None:
        return jsonify({"error": "Numero de tarjeta no encontrado."}), 404

    return jsonify(dict(tarjeta)), 200


@app.route('/api/banco/tarjetas/pagar', methods=['POST'])
def pagar_tarjeta():
    """Registra el pago del monto total o monto mínimo de la tarjeta."""
    datos = request.get_json()
    num_tarjeta = datos.get('num_tarjeta')
    monto_a_pagar = datos.get('monto')
    tipo_pago = datos.get('tipo_pago', 'Personalizado')
    metodo_pago = datos.get('metodo_pago', 'Efectivo')

    if not num_tarjeta or not monto_a_pagar:
        return jsonify({"error": "Numero de tarjeta y monto son obligatorios."}), 400

    conn = get_db_connection()
    tarjeta = conn.execute('SELECT * FROM banco_tarjetas WHERE num_tarjeta = ?', (num_tarjeta,)).fetchone()

    if tarjeta is None:
        conn.close()
        return jsonify({"error": "Tarjeta no encontrada."}), 404

    query_log = 'INSERT INTO transacciones_pagos (servicio, identificador_cliente, monto_pagado, metodo_pago, referencia) VALUES (?, ?, ?, ?, ?)'
    conn.execute(query_log, ('Banco UNO - Tarjetas', num_tarjeta, monto_a_pagar, metodo_pago, f"Pago Tarjeta ({tipo_pago})"))

    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Pago de tarjeta procesado exitosamente.",
        "monto_pagado": monto_a_pagar,
        "cliente": tarjeta['nombre_cliente']
    }), 200


# ==========================================
# 4. ENDPOINTS PARA TUPI
# ==========================================

@app.route('/api/tupi/<cedula>', methods=['GET'])
def consultar_tupi(cedula):
    """Consulta todas las compras y cuotas pendientes de un cliente en Tupi."""
    conn = get_db_connection()
    cuotas = conn.execute(
        'SELECT * FROM tupi_compras WHERE cedula = ? AND estado = "Pendiente" ORDER BY id_compra, num_cuota ASC',
        (cedula,)
    ).fetchall()
    conn.close()

    if not cuotas:
        return jsonify({"error": "No se registran cuotas pendientes en Tupi para este numero de cedula."}), 404

    resultado = [dict(c) for c in cuotas]
    return jsonify(resultado), 200


@app.route('/api/tupi/pagar', methods=['POST'])
def pagar_tupi():
    """Paga una cuota específica de una compra en Tupi."""
    datos = request.get_json()
    id_cuota = datos.get('id_cuota')
    metodo_pago = datos.get('metodo_pago', 'Efectivo')

    if not id_cuota:
        return jsonify({"error": "El ID de la cuota es requerido."}), 400

    conn = get_db_connection()
    cuota = conn.execute('SELECT * FROM tupi_compras WHERE id_cuota = ?', (id_cuota,)).fetchone()

    if cuota is None:
        conn.close()
        return jsonify({"error": "Cuota no encontrada."}), 404

    if cuota['estado'] == 'Pagado':
        conn.close()
        return jsonify({"error": "Esta cuota ya se encuentra pagada."}), 400

    conn.execute('UPDATE tupi_compras SET estado = "Pagado" WHERE id_cuota = ?', (id_cuota,))

    query_log = 'INSERT INTO transacciones_pagos (servicio, identificador_cliente, monto_pagado, metodo_pago, referencia) VALUES (?, ?, ?, ?, ?)'
    conn.execute(query_log, ('Tupi', cuota['cedula'], cuota['monto_cuota'], metodo_pago, f"Pago cuota {cuota['num_cuota']}/{cuota['total_cuotas']} - {cuota['descripcion_articulo']}"))

    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Pago de cuota en Tupi realizado con exito.",
        "articulo": cuota['descripcion_articulo'],
        "cuota_nro": f"{cuota['num_cuota']}/{cuota['total_cuotas']}",
        "monto_pagado": cuota['monto_cuota'],
        "cliente": cuota['nombre_cliente']
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
