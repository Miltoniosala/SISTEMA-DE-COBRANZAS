#  Sistema POS Multicobranzas -- PROYECTO CON FINES DIDACTICOS --

Sistema web integral de cobranzas y punto de venta (POS) simulado para pagos de servicios básicos, créditos bancarios y compras comerciales. 

##  Tecnologías Utilizadas
- **Base de Datos:** SQLite / SQL
- **Back-End:** Python (Flask, Flask-CORS)
- **Front-End:** HTML5, CSS3, JavaScript (Fetch API)
- **Análisis de Datos:** Python (Pandas)

##  Servicios Integrados
- **ANDE:** Consulta y pago de suministro eléctrico mediante NIS.
- **Banco UNO:** Liquidación de cuotas de préstamos (Sistema Francés) y pago de tarjetas de crédito.
- **Tupi:** Gestión y cobro de compras en cuotas por número de cédula.

##  Cómo ejecutar localmente
1. Instalar dependencias: `pip install flask flask-cors pandas`
2. Generar base de datos: `python crear_base_datos.py`
3. Iniciar servidor: `python app.py`
4. Abrir `index.html` en el navegador.
