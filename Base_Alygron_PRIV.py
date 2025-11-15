from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import pydeck as pdk
import random
from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# === BASE DE DATOS CON RELACIONES ===
Base = declarative_base()

class Aerolinea(Base):
    __tablename__ = 'aerolineas'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    pais = Column(String)
    vuelos = relationship("Vuelo", back_populates="aerolinea")

class Vuelo(Base):
    __tablename__ = 'vuelos'
    id = Column(Integer, primary_key=True)
    numero_vuelo = Column(String)
    aerolinea_id = Column(Integer, ForeignKey('aerolineas.id'))
    tipo = Column(String)
    origen = Column(String)
    destino = Column(String)
    fecha = Column(Date)
    hora_salida = Column(Time)
    hora_llegada = Column(Time)
    pasajeros = Column(Integer)
    aerolinea = relationship("Aerolinea", back_populates="vuelos")
    reservaciones = relationship("Reservacion", back_populates="vuelo")
    boletos = relationship("Boleto", back_populates="vuelo")

class Pasajero(Base):
    __tablename__ = 'pasajeros'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    edad = Column(Integer)
    email = Column(String)
    telefono = Column(String)
    reservaciones = relationship("Reservacion", back_populates="pasajero")
    boletos = relationship("Boleto", back_populates="pasajero")

class Reservacion(Base):
    __tablename__ = 'reservaciones'
    id = Column(Integer, primary_key=True)
    pasajero_id = Column(Integer, ForeignKey('pasajeros.id'))
    vuelo_id = Column(Integer, ForeignKey('vuelos.id'))
    fecha_reservacion = Column(Date)
    estado = Column(String)  # confirmada, pendiente, cancelada
    pasajero = relationship("Pasajero", back_populates="reservaciones")
    vuelo = relationship("Vuelo", back_populates="reservaciones")

class Boleto(Base):
    __tablename__ = 'boletos'
    id = Column(Integer, primary_key=True)
    codigo_boleto = Column(String)
    pasajero_id = Column(Integer, ForeignKey('pasajeros.id'))
    vuelo_id = Column(Integer, ForeignKey('vuelos.id'))
    asiento = Column(String)
    precio = Column(Integer)
    pasajero = relationship("Pasajero", back_populates="boletos")
    vuelo = relationship("Vuelo", back_populates="boletos")

class Trafico(Base):
    __tablename__ = 'trafico'
    id = Column(Integer, primary_key=True)
    vuelo_id = Column(Integer, ForeignKey('vuelos.id'))
    fecha = Column(Date)
    nivel = Column(String)  # bajo, medio, alto
    pasajeros_totales = Column(Integer)

# Conexión
engine = create_engine('sqlite:///aerolinea_completa.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
fake = Faker()

# === FUNCIONES AUXILIARES ===

def generar_aerolineas_aleatorias(cantidad=5):
    """Genera aerolíneas aleatorias"""
    nombres = ["AeroMéxico", "Volaris", "Interjet", "LATAM", "Avianca", "Copa Airlines", "Viva Aerobus", "Delta", "United"]
    paises = ["México", "Colombia", "Chile", "Panamá", "USA"]
    
    for i in range(cantidad):
        if session.query(Aerolinea).count() >= cantidad:
            break
        aero = Aerolinea(
            nombre=random.choice(nombres),
            pais=random.choice(paises)
        )
        session.add(aero)
    session.commit()

def generar_vuelos_aleatorios(cantidad=50):
    """Genera vuelos aleatorios"""
    aerolineas = session.query(Aerolinea).all()
    if not aerolineas:
        st.error("Primero genera aerolíneas")
        return
    
    tipos = ["Nacional", "Internacional"]
    ciudades_nacionales = ["Ciudad de México", "Guadalajara", "Monterrey", "Cancún", "Tijuana", "Mérida"]
    ciudades_internacionales = ["Miami", "New York", "Madrid", "Bogotá", "Lima", "Buenos Aires", "Santiago"]
    
    for i in range(cantidad):
        tipo = random.choice(tipos)
        if tipo == "Nacional":
            origen, destino = random.sample(ciudades_nacionales, 2)
        else:
            origen = random.choice(ciudades_nacionales)
            destino = random.choice(ciudades_internacionales)
        
        hora_salida = (datetime.min + timedelta(minutes=random.randint(300, 1200))).time()
        hora_llegada = (datetime.min + timedelta(minutes=random.randint(300, 1400))).time()
        
        vuelo = Vuelo(
            numero_vuelo=f"VL{random.randint(100, 999)}",
            aerolinea_id=random.choice(aerolineas).id,
            tipo=tipo,
            origen=origen,
            destino=destino,
            fecha=datetime.today().date() + timedelta(days=random.randint(0, 30)),
            hora_salida=hora_salida,
            hora_llegada=hora_llegada,
            pasajeros=random.randint(50, 300)
        )
        session.add(vuelo)
    session.commit()

def generar_pasajeros_aleatorios(cantidad=100):
    """Genera pasajeros aleatorios"""
    for i in range(cantidad):
        pasajero = Pasajero(
            nombre=fake.name(),
            edad=random.randint(18, 80),
            email=fake.email(),
            telefono=fake.phone_number()
        )
        session.add(pasajero)
    session.commit()

def generar_reservaciones_aleatorias(cantidad=50):
    """Genera reservaciones aleatorias"""
    vuelos = session.query(Vuelo).all()
    pasajeros = session.query(Pasajero).all()
    
    if not vuelos or not pasajeros:
        st.error("Necesitas vuelos y pasajeros primero")
        return
    
    estados = ["confirmada", "pendiente", "cancelada"]
    
    for i in range(cantidad):
        reservacion = Reservacion(
            pasajero_id=random.choice(pasajeros).id,
            vuelo_id=random.choice(vuelos).id,
            fecha_reservacion=datetime.today().date(),
            estado=random.choice(estados)
        )
        session.add(reservacion)
    session.commit()

def generar_boletos_aleatorios(cantidad=50):
    """Genera boletos aleatorios"""
    vuelos = session.query(Vuelo).all()
    pasajeros = session.query(Pasajero).all()
    
    if not vuelos or not pasajeros:
        st.error("Necesitas vuelos y pasajeros primero")
        return
    
    for i in range(cantidad):
        boleto = Boleto(
            codigo_boleto=f"BOL{random.randint(10000, 99999)}",
            pasajero_id=random.choice(pasajeros).id,
            vuelo_id=random.choice(vuelos).id,
            asiento=f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}",
            precio=random.randint(1000, 15000)
        )
        session.add(boleto)
    session.commit()

def calcular_nivel_trafico_difuso(num_vuelos):
    """Calcula nivel de tráfico con lógica difusa"""
    if num_vuelos < 5:
        return "Bajo"
    elif num_vuelos < 15:
        return "Medio"
    else:
        return "Alto"

def generar_ticket_pdf(boleto_id):
    """Genera un PDF del ticket del pasajero"""
    boleto = session.query(Boleto).filter_by(id=boleto_id).first()
    
    if not boleto:
        return None
    
    pasajero = boleto.pasajero
    vuelo = boleto.vuelo
    aerolinea = vuelo.aerolinea
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Diseño del ticket
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 750, "BOLETO DE AVION")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Codigo: {boleto.codigo_boleto}")
    c.drawString(100, 680, f"Pasajero: {pasajero.nombre}")
    c.drawString(100, 660, f"Edad: {pasajero.edad}")
    c.drawString(100, 640, f"Email: {pasajero.email}")
    
    c.drawString(100, 600, f"Aerolinea: {aerolinea.nombre}")
    c.drawString(100, 580, f"Vuelo: {vuelo.numero_vuelo}")
    c.drawString(100, 560, f"Origen: {vuelo.origen}")
    c.drawString(100, 540, f"Destino: {vuelo.destino}")
    c.drawString(100, 520, f"Fecha: {vuelo.fecha}")
    c.drawString(100, 500, f"Hora Salida: {vuelo.hora_salida}")
    c.drawString(100, 480, f"Hora Llegada: {vuelo.hora_llegada}")
    
    c.drawString(100, 440, f"Asiento: {boleto.asiento}")
    c.drawString(100, 420, f"Precio: ${boleto.precio} MXN")
    
    c.drawString(100, 360, "Gracias por volar con nosotros!")
    
    c.save()
    buffer.seek(0)
    return buffer

# === INTERFAZ STREAMLIT ===
st.title("✈️ Sistema Completo de Aerolínea - Alygron Flights")

menu = st.sidebar.selectbox("Menu Principal", [
    "🏠 Inicio",
    "🎲 Generar Datos Aleatorios",
    "✍️ Registros Manuales",
    "📊 Consultas y Filtros",
    "🗺️ Mapa de Vuelos",
    "📈 Análisis de Tráfico",
    "🎫 Generar Ticket PDF"
])

# === INICIO ===
if menu == "🏠 Inicio":
    st.subheader("Bienvenido al Sistema de Gestión")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_vuelos = session.query(Vuelo).count()
        st.metric("Total Vuelos", total_vuelos)
    
    with col2:
        total_pasajeros = session.query(Pasajero).count()
        st.metric("Total Pasajeros", total_pasajeros)
    
    with col3:
        total_boletos = session.query(Boleto).count()
        st.metric("Boletos Vendidos", total_boletos)
    
    st.write("---")
    st.write("Usa el menú de la izquierda para navegar por el sistema")

# === GENERAR DATOS ALEATORIOS ===
elif menu == "🎲 Generar Datos Aleatorios":
    st.subheader("Generador de Datos Aleatorios")
    
    st.write("**Paso 1: Genera las aerolíneas**")
    cant_aerolineas = st.number_input("Cantidad de aerolíneas", 1, 10, 5)
    if st.button("Generar Aerolíneas"):
        generar_aerolineas_aleatorias(cant_aerolineas)
        st.success(f"Se generaron {cant_aerolineas} aerolíneas")
    
    st.write("---")
    
    st.write("**Paso 2: Genera los vuelos**")
    cant_vuelos = st.number_input("Cantidad de vuelos", 1, 200, 50)
    if st.button("Generar Vuelos"):
        generar_vuelos_aleatorios(cant_vuelos)
        st.success(f"Se generaron {cant_vuelos} vuelos")
    
    st.write("---")
    
    st.write("**Paso 3: Genera los pasajeros**")
    cant_pasajeros = st.number_input("Cantidad de pasajeros", 1, 500, 100)
    if st.button("Generar Pasajeros"):
        generar_pasajeros_aleatorios(cant_pasajeros)
        st.success(f"Se generaron {cant_pasajeros} pasajeros")
    
    st.write("---")
    
    st.write("**Paso 4: Genera las reservaciones**")
    cant_reservaciones = st.number_input("Cantidad de reservaciones", 1, 200, 50)
    if st.button("Generar Reservaciones"):
        generar_reservaciones_aleatorias(cant_reservaciones)
        st.success(f"Se generaron {cant_reservaciones} reservaciones")
    
    st.write("---")
    
    st.write("**Paso 5: Genera los boletos**")
    cant_boletos = st.number_input("Cantidad de boletos", 1, 200, 50)
    if st.button("Generar Boletos"):
        generar_boletos_aleatorios(cant_boletos)
        st.success(f"Se generaron {cant_boletos} boletos")

# === REGISTROS MANUALES ===
elif menu == "✍️ Registros Manuales":
    submenu = st.selectbox("¿Qué quieres registrar?", [
        "Aerolínea", "Vuelo", "Pasajero", "Reservación", "Boleto"
    ])
    
    if submenu == "Aerolínea":
        st.subheader("Registrar Aerolínea")
        nombre = st.text_input("Nombre de la aerolínea")
        pais = st.text_input("País")
        
        if st.button("Guardar Aerolínea"):
            aero = Aerolinea(nombre=nombre, pais=pais)
            session.add(aero)
            session.commit()
            st.success("Aerolínea registrada")
    
    elif submenu == "Vuelo":
        st.subheader("Registrar Vuelo")
        aerolineas = session.query(Aerolinea).all()
        
        if not aerolineas:
            st.warning("Primero registra una aerolínea")
        else:
            aero_dict = {a.nombre: a.id for a in aerolineas}
            aero_sel = st.selectbox("Aerolínea", list(aero_dict.keys()))
            
            num_vuelo = st.text_input("Número de vuelo")
            tipo = st.selectbox("Tipo", ["Nacional", "Internacional"])
            origen = st.text_input("Origen")
            destino = st.text_input("Destino")
            fecha = st.date_input("Fecha")
            hora_sal = st.time_input("Hora Salida")
            hora_lleg = st.time_input("Hora Llegada")
            pasajeros = st.number_input("Pasajeros", 0, 500, 100)
            
            if st.button("Guardar Vuelo"):
                vuelo = Vuelo(
                    numero_vuelo=num_vuelo,
                    aerolinea_id=aero_dict[aero_sel],
                    tipo=tipo,
                    origen=origen,
                    destino=destino,
                    fecha=fecha,
                    hora_salida=hora_sal,
                    hora_llegada=hora_lleg,
                    pasajeros=pasajeros
                )
                session.add(vuelo)
                session.commit()
                st.success("Vuelo registrado")

# === CONSULTAS Y FILTROS ===
elif menu == "📊 Consultas y Filtros":
    st.subheader("Consultas y Filtros")
    
    tipo_consulta = st.selectbox("Tipo de consulta", [
        "Ver todos los vuelos",
        "Filtrar pasajeros",
        "Buscar reservaciones",
        "Ver boletos vendidos"
    ])
    
    if tipo_consulta == "Ver todos los vuelos":
        vuelos_df = pd.read_sql("SELECT v.*, a.nombre as aerolinea FROM vuelos v JOIN aerolineas a ON v.aerolinea_id = a.id", engine)
        st.dataframe(vuelos_df)
        
        st.write("**Vuelos por tipo:**")
        st.bar_chart(vuelos_df["tipo"].value_counts())
    
    elif tipo_consulta == "Filtrar pasajeros":
        st.write("**Filtros:**")
        
        edad_min = st.slider("Edad mínima", 0, 100, 18)
        edad_max = st.slider("Edad máxima", 0, 100, 80)
        
        query = f"SELECT * FROM pasajeros WHERE edad >= {edad_min} AND edad <= {edad_max}"
        pasajeros_df = pd.read_sql(query, engine)
        
        st.write(f"Se encontraron {len(pasajeros_df)} pasajeros")
        st.dataframe(pasajeros_df)

# === MAPA DE VUELOS ===
elif menu == "🗺️ Mapa de Vuelos":
    st.subheader("Mapa de Rutas de Vuelo")
    
    vuelos = pd.read_sql("SELECT v.*, a.nombre as aerolinea FROM vuelos v JOIN aerolineas a ON v.aerolinea_id = a.id", engine)
    
    if vuelos.empty:
        st.warning("No hay vuelos registrados")
    else:
        ciudades = {
            "Ciudad de México": (19.4326, -99.1332),
            "Guadalajara": (20.6597, -103.3496),
            "Monterrey": (25.6866, -100.3161),
            "Tijuana": (32.5149, -117.0382),
            "Cancún": (21.1619, -86.8515),
            "Mérida": (20.9674, -89.5926),
            "Miami": (25.7617, -80.1918),
            "New York": (40.7128, -74.0060),
            "Madrid": (40.4168, -3.7038),
            "Bogotá": (4.7110, -74.0721),
            "Lima": (-12.0464, -77.0428),
            "Buenos Aires": (-34.6037, -58.3816),
            "Santiago": (-33.4489, -70.6693)
        }
        
        vuelos["from_lat"] = vuelos["origen"].apply(lambda x: ciudades.get(x, (None, None))[0])
        vuelos["from_lon"] = vuelos["origen"].apply(lambda x: ciudades.get(x, (None, None))[1])
        vuelos["to_lat"] = vuelos["destino"].apply(lambda x: ciudades.get(x, (None, None))[0])
        vuelos["to_lon"] = vuelos["destino"].apply(lambda x: ciudades.get(x, (None, None))[1])
        vuelos = vuelos.dropna(subset=["from_lat", "from_lon", "to_lat", "to_lon"])
        
        vuelos["color"] = vuelos["tipo"].apply(lambda t: [0, 255, 0] if t == "Nacional" else [0, 150, 255])
        
        layer = pdk.Layer(
            "GreatCircleLayer",
            data=vuelos,
            get_source_position=["from_lon", "from_lat"],
            get_target_position=["to_lon", "to_lat"],
            get_source_color="color",
            get_target_color="color",
            get_stroke_width=3,
            pickable=True
        )
        
        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=pdk.ViewState(latitude=20, longitude=-40, zoom=2),
            tooltip={
                "html": "<b>{aerolinea}</b><br>Vuelo: {numero_vuelo}<br>{origen} → {destino}<br>Salida: {hora_salida}<br>Llegada: {hora_llegada}<br>🧍 Pasajeros: {pasajeros}",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }
        ))

# === ANÁLISIS DE TRÁFICO ===
elif menu == "📈 Análisis de Tráfico":
    st.subheader("Análisis de Tráfico Aéreo (Lógica Difusa)")
    
    tipo_analisis = st.radio("Periodo", ["Por día", "Por mes"])
    
    if tipo_analisis == "Por día":
        fecha_sel = st.date_input("Selecciona la fecha")
        vuelos_dia = session.query(Vuelo).filter(Vuelo.fecha == fecha_sel).all()
        num_vuelos = len(vuelos_dia)
        pasajeros_total = sum([v.pasajeros for v in vuelos_dia])
        
        nivel = calcular_nivel_trafico_difuso(num_vuelos)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Vuelos", num_vuelos)
        col2.metric("Pasajeros", pasajeros_total)
        col3.metric("Nivel de Tráfico", nivel)
        
        if nivel == "Bajo":
            st.success("Tráfico bajo - Operaciones normales")
        elif nivel == "Medio":
            st.warning("Tráfico medio - Atención moderada")
        else:
            st.error("Tráfico alto - Máxima atención requerida")
    
    else:
        vuelos_df = pd.read_sql("SELECT fecha, COUNT(*) as total FROM vuelos GROUP BY fecha", engine)
        vuelos_df["fecha"] = pd.to_datetime(vuelos_df["fecha"])
        vuelos_df["mes"] = vuelos_df["fecha"].dt.to_period("M")
        
        resumen = vuelos_df.groupby("mes")["total"].sum().reset_index()
        st.bar_chart(resumen.set_index("mes"))

# === GENERAR TICKET PDF ===
elif menu == "🎫 Generar Ticket PDF":
    st.subheader("Generar Ticket de Pasajero")
    
    boletos = session.query(Boleto).all()
    
    if not boletos:
        st.warning("No hay boletos registrados")
    else:
        boleto_dict = {}
        for b in boletos:
            pasajero = b.pasajero
            vuelo = b.vuelo
            info = f"{b.codigo_boleto} - {pasajero.nombre} - Vuelo {vuelo.numero_vuelo}"
            boleto_dict[info] = b.id
        
        boleto_sel = st.selectbox("Selecciona el boleto", list(boleto_dict.keys()))
        
        if st.button("Generar PDF"):
            pdf_buffer = generar_ticket_pdf(boleto_dict[boleto_sel])
            
            if pdf_buffer:
                st.success("PDF generado correctamente")
                st.download_button(
                    label="Descargar Ticket PDF",
                    data=pdf_buffer,
                    file_name="ticket_vuelo.pdf",
                    mime="application/pdf"
                )

st.write("---")
st.caption("Sistema de Gestión Aerolínea v1.0")