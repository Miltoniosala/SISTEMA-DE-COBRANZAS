
import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'cobranzas.db')

conn = sqlite3.connect(db_path)

# 1. Total recaudado por servicio
query_servicios = '''
SELECT servicio, COUNT(id_transaccion) AS total_transacciones, SUM(monto_pagado) AS monto_total_recaudado
FROM transacciones_pagos
GROUP BY servicio
ORDER BY monto_total_recaudado DESC
'''
df_servicios = pd.read_sql_query(query_servicios, conn)

# 2. Análisis de morosidad
query_prestamos_mora = '''
SELECT cedula, nombre_cliente, num_prestamo, num_cuota, total_cuotas, (monto_capital + monto_interes) AS monto_cuota, fecha_vencimiento
FROM banco_prestamos
WHERE estado = 'Pendiente' AND fecha_vencimiento < date('now')
'''
df_mora = pd.read_sql_query(query_prestamos_mora, conn)

print("--- RECAUDACIÓN POR SERVICIO ---")
print(df_servicios)
print("\n--- CUOTAS EN MORA ---")
print(df_mora)

conn.close()
