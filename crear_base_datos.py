import sqlite3

# Conectar a la base de datos (se crea el archivo si no existe)
conn = sqlite3.connect('cobranzas.db')
cursor = conn.cursor()

# 1. Habilitar claves foraneas
cursor.execute("PRAGMA foreign_keys = ON;")

# 2. Creacion de Tablas
cursor.executescript("""
-- Tabla 1: Facturas ANDE
CREATE TABLE IF NOT EXISTS ande_facturas (
    nis INTEGER PRIMARY KEY,
    nombre_cliente TEXT NOT NULL,
    monto_total INTEGER NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    estado_pago TEXT NOT NULL CHECK(estado_pago IN ('Pendiente', 'Pagado'))
);

-- Tabla 2: Prestamos Banco UNO
CREATE TABLE IF NOT EXISTS banco_prestamos (
    id_cuota INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula TEXT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    num_prestamo TEXT NOT NULL,
    num_cuota INTEGER NOT NULL,
    total_cuotas INTEGER NOT NULL,
    monto_capital INTEGER NOT NULL,
    monto_interes INTEGER NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('Pendiente', 'Pagado'))
);

-- Tabla 3: Tarjetas Banco UNO
CREATE TABLE IF NOT EXISTS banco_tarjetas (
    num_tarjeta TEXT PRIMARY KEY,
    cedula TEXT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    tipo_tarjeta TEXT NOT NULL,
    monto_cierre INTEGER NOT NULL,
    monto_minimo INTEGER NOT NULL,
    fecha_vencimiento TEXT NOT NULL
);

-- Tabla 4: Compras a Cuotas Tupi
CREATE TABLE IF NOT EXISTS tupi_compras (
    id_cuota INTEGER PRIMARY KEY AUTOINCREMENT,
    id_compra TEXT NOT NULL,
    cedula TEXT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    descripcion_articulo TEXT NOT NULL,
    num_cuota INTEGER NOT NULL,
    total_cuotas INTEGER NOT NULL,
    monto_cuota INTEGER NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('Pendiente', 'Pagado'))
);

-- Tabla 5: Historial de Transacciones (Cobranzas POS)
CREATE TABLE IF NOT EXISTS transacciones_pagos (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    servicio TEXT NOT NULL,
    identificador_cliente TEXT NOT NULL,
    monto_pagado INTEGER NOT NULL,
    metodo_pago TEXT NOT NULL,
    referencia TEXT
);
""")

# 3. Insercion de Datos Simulados
cursor.executescript("""
-- Datos ANDE
INSERT OR IGNORE INTO ande_facturas (nis, nombre_cliente, monto_total, fecha_vencimiento, estado_pago) VALUES
(1024501, 'Carlos Benítez', 185000, '2026-09-05', 'Pendiente'),
(2045602, 'María Elena Gómez', 450000, '2026-08-28', 'Pendiente'),
(3056703, 'Juan Silguero', 92000, '2026-09-12', 'Pendiente');

-- Datos Banco UNO (Prestamos - Sistema Frances)
INSERT OR IGNORE INTO banco_prestamos (cedula, nombre_cliente, num_prestamo, num_cuota, total_cuotas, monto_capital, monto_interes, fecha_vencimiento, estado) VALUES
('3456789', 'Carlos Benítez', 'PREST-001', 5, 24, 620000, 180000, '2026-09-10', 'Pendiente'),
('3456789', 'Carlos Benítez', 'PREST-001', 6, 24, 635000, 165000, '2026-10-10', 'Pendiente'),
('4567890', 'María Elena Gómez', 'PREST-002', 12, 12, 1100000, 50000, '2026-08-30', 'Pendiente');

-- Datos Banco UNO (Tarjetas de Credito)
INSERT OR IGNORE INTO banco_tarjetas (num_tarjeta, cedula, nombre_cliente, tipo_tarjeta, monto_cierre, monto_minimo, fecha_vencimiento) VALUES
('4532-8901-2345-6789', '3456789', 'Carlos Benítez', 'Visa Clásica', 2450000, 245000, '2026-09-15'),
('5412-7512-3412-8901', '4567890', 'María Elena Gómez', 'Mastercard Gold', 5800000, 580000, '2026-09-20');

-- Datos Tupi (Compras a cuotas)
INSERT OR IGNORE INTO tupi_compras (id_compra, cedula, nombre_cliente, descripcion_articulo, num_cuota, total_cuotas, monto_cuota, fecha_vencimiento, estado) VALUES
('TUP-901', '3456789', 'Carlos Benítez', 'Smart TV 55" 4K', 3, 12, 350000, '2026-09-05', 'Pendiente'),
('TUP-902', '3456789', 'Carlos Benítez', 'Escritorio de Oficina Ergonómico', 1, 6, 180000, '2026-09-15', 'Pendiente'),
('TUP-903', '5678901', 'Rodrigo Mendoza', 'Heladera Inverter 400L', 8, 18, 420000, '2026-08-25', 'Pendiente');
""")

conn.commit()
conn.close()
print("Base de datos cobranzas.db generada exitosamente con datos de prueba.")
