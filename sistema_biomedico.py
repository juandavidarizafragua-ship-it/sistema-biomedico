import streamlit as st
import requests
from datetime import datetime, date, timedelta
import hashlib
import pandas as pd
import io
import json

# -------- CONFIG --------
SUPABASE_URL = "https://hivvykyslqodrrfmteer.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhpdnZ5a3lzbHFvZHJyZm10ZWVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg3MTA0NzQsImV4cCI6MjA5NDI4NjQ3NH0.1dBUFD9myAK9057E0g6RVFKellm6RT_6E15RHz63ryc"
HEADERS = {
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}

# PERSONALIZAR POR CLIENTE
NOMBRE_EMPRESA = "Biomédica Demo"
COLOR = "#2E86AB"
SLUG = "biodemo"

USUARIOS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "rol": "admin"
    }
}

# -------- TABLAS (con prefijo del cliente) --------
T_CLIENTES = f"{SLUG}_clientes"
T_ALERTAS = f"{SLUG}_alertas"
T_EQUIPOS = f"{SLUG}_equipos"
T_HOJAS = f"{SLUG}_hojas_vida"
T_CRONOGRAMA = f"{SLUG}_cronograma"

# -------- SUPABASE HELPERS --------
def sb_get(tabla, params=""):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{tabla}?{params}", headers=HEADERS)
    return r.json() if r.status_code == 200 else []

def sb_post(tabla, datos):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers={**HEADERS, "Prefer": "return=representation"}, json=datos)
    return r.status_code == 201

def sb_patch(tabla, id_val, datos):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{tabla}?id=eq.{id_val}", headers={**HEADERS, "Prefer": "return=minimal"}, json=datos)
    return r.status_code == 204

def sb_delete(tabla, id_val):
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/{tabla}?id=eq.{id_val}", headers=HEADERS)
    return r.status_code in [200, 204]

def subir_documento(archivo, carpeta=None):
    if carpeta is None:
        carpeta = SLUG
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/documentos/{carpeta}/{archivo.name}"
        h = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": archivo.type}
        r = requests.post(url, headers=h, data=archivo.getvalue())
        if r.status_code in [200, 201]:
            return f"{SUPABASE_URL}/storage/v1/object/public/documentos/{carpeta}/{archivo.name}"
        return None
    except:
        return None

def listar_documentos(carpeta=None):
    if carpeta is None:
        carpeta = SLUG
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/list/documentos"
        r = requests.post(url, headers={**HEADERS}, json={"prefix": carpeta + "/", "limit": 100})
        return r.json() if r.status_code == 200 else []
    except:
        return []

# -------- PAGE CONFIG --------
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon="🔬", layout="wide")

st.markdown(f"""
<style>
.stApp {{ background-color: #0a0a0a; }}
.stButton > button {{
    background: linear-gradient(135deg, #0a1a2a, #112233) !important;
    color: {COLOR} !important; border: 1px solid {COLOR}66 !important;
    border-radius: 4px !important; font-size: 12px !important;
}}
.stTextInput > div > div > input, .stNumberInput > div > div > input,
.stDateInput > div > div > input, .stSelectbox > div > div > div,
.stTextArea > div > div > textarea {{
    background-color: #111 !important; color: #e0e0e0 !important;
    border: 1px solid {COLOR}44 !important;
}}
.metric-card {{
    background: linear-gradient(135deg, #111, #1a1a1a);
    border: 1px solid {COLOR}33; border-radius: 8px;
    padding: 20px 24px; text-align: center;
}}
.metric-num {{ font-family: serif; font-size: 42px; font-weight: 700; color: {COLOR}; line-height: 1; }}
.metric-label {{ font-size: 11px; color: #888; letter-spacing: 2px; margin-top: 6px; }}
.divider {{ border:none; height:1px; background:linear-gradient(90deg,transparent,{COLOR}44,transparent); margin:20px 0; }}
.equipo-card {{
    background: #111; border: 1px solid {COLOR}22; border-radius: 6px;
    padding: 14px 18px; margin: 6px 0;
}}
</style>
""", unsafe_allow_html=True)

# -------- LOGIN --------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown(f"""
    <div style='text-align:center; padding:60px 0 30px 0;'>
        <div style='font-family:serif; font-size:11px; color:{COLOR}; letter-spacing:4px;'>{NOMBRE_EMPRESA.upper()}</div>
        <div style='font-family:serif; font-size:28px; font-weight:700; color:#fff; margin:8px 0;'>Gestión de Equipos Biomédicos</div>
        <div style='font-size:11px; color:#555; letter-spacing:2px;'>Powered by A.R.I.Z.A.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        usr = st.text_input("Usuario", key="login_usr")
        pwd = st.text_input("Contraseña", type="password", key="login_pwd")
        if st.button("Ingresar", use_container_width=True):
            pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
            if usr in USUARIOS and USUARIOS[usr]["password"] == pwd_hash:
                st.session_state.autenticado = True
                st.session_state.usuario = usr
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# -------- HEADER --------
st.markdown(f"""
<div style='text-align:center; padding:20px 0 10px 0; border-bottom:1px solid {COLOR}33; margin-bottom:20px;'>
    <div style='font-family:serif; font-size:11px; color:{COLOR}; letter-spacing:4px;'>{NOMBRE_EMPRESA.upper()}</div>
    <div style='font-family:serif; font-size:24px; font-weight:700; color:#fff;'>Gestión de Equipos Biomédicos</div>
</div>
""", unsafe_allow_html=True)

# -------- MENÚ --------
if "menu" not in st.session_state:
    st.session_state.menu = "Inventario"

modulos = ["Inventario", "Cronograma", "Hojas de Vida", "Clientes", "Alertas", "Documentos"]
cols = st.columns(len(modulos))
for i, mod in enumerate(modulos):
    with cols[i]:
        if st.button(f"◈ {mod.upper()}", use_container_width=True, key=f"menu_{mod}"):
            st.session_state.menu = mod
            st.rerun()

menu = st.session_state.menu
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Obtener clientes para filtros
clientes_list = sb_get(T_CLIENTES, "order=nombre.asc")
nombres_clientes = ["Todos"] + [c.get("nombre", "") for c in clientes_list]
mapa_clientes = {c.get("id"): c.get("nombre", "") for c in clientes_list}


# ================================================================
# MÓDULO: INVENTARIO DE EQUIPOS
# ================================================================
if menu == "Inventario":
    equipos = sb_get(T_EQUIPOS, "order=created_at.desc")

    st.markdown(f"<div style='font-family:serif; font-size:20px; color:{COLOR};'>Inventario de Equipos</div>", unsafe_allow_html=True)

    # Métricas
    activos = len([e for e in equipos if e.get("estado") == "Activo"])
    fuera = len([e for e in equipos if e.get("estado") == "Fuera de servicio"])
    baja = len([e for e in equipos if e.get("estado") == "Dado de baja"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(equipos)}</div><div class='metric-label'>TOTAL EQUIPOS</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#44ff88;'>{activos}</div><div class='metric-label'>ACTIVOS</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#ffaa44;'>{fuera}</div><div class='metric-label'>FUERA SERVICIO</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#ff4444;'>{baja}</div><div class='metric-label'>DADOS DE BAJA</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Registrar equipo
    with st.expander("➕ Registrar equipo"):
        ec1, ec2 = st.columns(2)
        with ec1:
            eq_nombre = st.text_input("Nombre del equipo", key="eq_nombre", placeholder="Autoclave, Monitor de signos...")
            eq_marca = st.text_input("Marca", key="eq_marca")
            eq_modelo = st.text_input("Modelo", key="eq_modelo")
            eq_serie = st.text_input("Número de serie", key="eq_serie")
            eq_ubicacion = st.text_input("Ubicación / Área", key="eq_ubic", placeholder="Consultorio 1, Lab, Sala de espera...")
        with ec2:
            eq_cliente = st.selectbox("Cliente / Consultorio", [c.get("nombre") for c in clientes_list] if clientes_list else ["Sin clientes registrados"], key="eq_cliente")
            eq_clasificacion = st.selectbox("Clasificación de riesgo", ["I", "IIA", "IIB", "III"], key="eq_clasif")
            eq_registro = st.text_input("Registro INVIMA", key="eq_invima")
            eq_fecha_adq = st.date_input("Fecha de adquisición", key="eq_fecha")
            eq_estado = st.selectbox("Estado", ["Activo", "Fuera de servicio", "Dado de baja"], key="eq_estado")
            eq_frec_mant = st.selectbox("Frecuencia de mantenimiento", ["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"], key="eq_frec")

        eq_notas = st.text_area("Observaciones", key="eq_notas")

        if st.button("✓ Registrar equipo", key="btn_eq"):
            if eq_nombre and eq_marca:
                cliente_id = None
                for c in clientes_list:
                    if c.get("nombre") == eq_cliente:
                        cliente_id = c.get("id")
                        break

                sb_post(T_EQUIPOS, {
                    "nombre": eq_nombre, "marca": eq_marca, "modelo": eq_modelo,
                    "serie": eq_serie, "ubicacion": eq_ubicacion,
                    "cliente_id": cliente_id, "cliente_nombre": eq_cliente,
                    "clasificacion_riesgo": eq_clasificacion,
                    "registro_invima": eq_registro,
                    "fecha_adquisicion": str(eq_fecha_adq),
                    "estado": eq_estado,
                    "frecuencia_mantenimiento": eq_frec_mant,
                    "notas": eq_notas
                })
                st.success("✓ Equipo registrado")
                st.rerun()
            else:
                st.warning("Nombre y marca son obligatorios")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Filtros
    fc1, fc2 = st.columns(2)
    with fc1:
        filtro_cliente = st.selectbox("Filtrar por cliente:", nombres_clientes, key="inv_filtro_cli")
    with fc2:
        filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "Activo", "Fuera de servicio", "Dado de baja"], key="inv_filtro_est")

    for equipo in equipos:
        if filtro_cliente != "Todos" and equipo.get("cliente_nombre") != filtro_cliente:
            continue
        if filtro_estado != "Todos" and equipo.get("estado") != filtro_estado:
            continue

        estado = equipo.get("estado", "Activo")
        color_est = {"Activo": "#44ff88", "Fuera de servicio": "#ffaa44", "Dado de baja": "#ff4444"}.get(estado, "#888")

        with st.expander(f"🔬 {equipo.get('nombre')} — {equipo.get('marca')} {equipo.get('modelo')} — {equipo.get('cliente_nombre', '')}"):
            ic1, ic2 = st.columns(2)
            with ic1:
                st.markdown(f"**Nombre:** {equipo.get('nombre')}")
                st.markdown(f"**Marca:** {equipo.get('marca')}")
                st.markdown(f"**Modelo:** {equipo.get('modelo')}")
                st.markdown(f"**Serie:** {equipo.get('serie', '—')}")
                st.markdown(f"**Ubicación:** {equipo.get('ubicacion', '—')}")
            with ic2:
                st.markdown(f"**Cliente:** {equipo.get('cliente_nombre', '—')}")
                st.markdown(f"**Riesgo:** {equipo.get('clasificacion_riesgo', '—')}")
                st.markdown(f"**INVIMA:** {equipo.get('registro_invima', '—')}")
                st.markdown(f"**Adquisición:** {equipo.get('fecha_adquisicion', '—')}")
                st.markdown(f"**Frecuencia mant.:** {equipo.get('frecuencia_mantenimiento', '—')}")
                st.markdown(f"<span style='color:{color_est}'>**Estado: {estado}**</span>", unsafe_allow_html=True)

            st.markdown(f"**Notas:** {equipo.get('notas', '—')}")

            ba, bb, bc = st.columns(3)
            with ba:
                if estado != "Activo":
                    if st.button("Activar", key=f"eq_act_{equipo.get('id')}"):
                        sb_patch(T_EQUIPOS, equipo.get("id"), {"estado": "Activo"})
                        st.rerun()
            with bb:
                if estado == "Activo":
                    if st.button("Fuera de servicio", key=f"eq_fs_{equipo.get('id')}"):
                        sb_patch(T_EQUIPOS, equipo.get("id"), {"estado": "Fuera de servicio"})
                        st.rerun()
            with bc:
                if estado != "Dado de baja":
                    if st.button("Dar de baja", key=f"eq_baja_{equipo.get('id')}"):
                        sb_patch(T_EQUIPOS, equipo.get("id"), {"estado": "Dado de baja"})
                        st.rerun()

    if equipos and st.button("📊 Exportar inventario a Excel", key="exp_inv"):
        df = pd.DataFrame(equipos)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("Descargar", buffer.getvalue(), f"inventario_{date.today()}.xlsx")


# ================================================================
# MÓDULO: CRONOGRAMA DE MANTENIMIENTO
# ================================================================
elif menu == "Cronograma":
    cronograma = sb_get(T_CRONOGRAMA, "order=fecha_programada.asc")
    equipos = sb_get(T_EQUIPOS, "order=nombre.asc")

    st.markdown(f"<div style='font-family:serif; font-size:20px; color:{COLOR};'>Cronograma de Mantenimiento</div>", unsafe_allow_html=True)

    hoy = date.today()
    vencidos = [c for c in cronograma if c.get("fecha_programada") and c.get("fecha_programada") < str(hoy) and c.get("estado") != "Completado"]
    proximos = [c for c in cronograma if c.get("fecha_programada") and str(hoy) <= c.get("fecha_programada") <= str(hoy + timedelta(days=7)) and c.get("estado") != "Completado"]
    pendientes = [c for c in cronograma if c.get("estado") == "Pendiente"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#ff4444;'>{len(vencidos)}</div><div class='metric-label'>VENCIDOS</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#ffaa44;'>{len(proximos)}</div><div class='metric-label'>PRÓX. 7 DÍAS</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(pendientes)}</div><div class='metric-label'>PENDIENTES</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(cronograma)}</div><div class='metric-label'>TOTAL</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Programar mantenimiento
    with st.expander("➕ Programar mantenimiento"):
        if equipos:
            opciones_equipos = {f"{e.get('nombre')} — {e.get('marca')} {e.get('modelo')} ({e.get('cliente_nombre', '')})": e.get("id") for e in equipos}
            cr_equipo_sel = st.selectbox("Equipo", list(opciones_equipos.keys()), key="cr_equipo")
            cr_equipo_id = opciones_equipos[cr_equipo_sel]
        else:
            st.warning("Registra equipos primero en Inventario")
            cr_equipo_id = None

        cc1, cc2 = st.columns(2)
        with cc1:
            cr_tipo = st.selectbox("Tipo de mantenimiento", ["Preventivo", "Correctivo", "Calibración", "Inspección"], key="cr_tipo")
            cr_fecha = st.date_input("Fecha programada", key="cr_fecha")
        with cc2:
            cr_tecnico = st.text_input("Técnico responsable", key="cr_tecnico")
            cr_prioridad = st.selectbox("Prioridad", ["Normal", "Alta", "Urgente"], key="cr_prioridad")

        cr_descripcion = st.text_area("Descripción del trabajo", key="cr_desc")

        if st.button("✓ Programar", key="btn_cr"):
            if cr_equipo_id:
                # Obtener nombre del equipo
                nombre_eq = cr_equipo_sel.split(" — ")[0]
                sb_post(T_CRONOGRAMA, {
                    "equipo_id": cr_equipo_id,
                    "equipo_nombre": nombre_eq,
                    "tipo": cr_tipo,
                    "fecha_programada": str(cr_fecha),
                    "tecnico": cr_tecnico,
                    "prioridad": cr_prioridad,
                    "descripcion": cr_descripcion,
                    "estado": "Pendiente"
                })
                st.success("✓ Mantenimiento programado")
                st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Filtros
    filtro_cr_estado = st.selectbox("Filtrar:", ["Pendientes", "Todos", "Completados", "Vencidos"], key="cr_filtro")

    for item in cronograma:
        estado = item.get("estado", "Pendiente")
        fecha = item.get("fecha_programada", "")
        es_vencido = fecha and fecha < str(hoy) and estado != "Completado"

        if filtro_cr_estado == "Pendientes" and estado != "Pendiente":
            continue
        if filtro_cr_estado == "Completados" and estado != "Completado":
            continue
        if filtro_cr_estado == "Vencidos" and not es_vencido:
            continue

        icono = "🔴" if es_vencido else ("🟡" if fecha and fecha <= str(hoy + timedelta(days=7)) else "🟢")
        color_cr = "#ff4444" if es_vencido else ("#ffaa44" if estado == "Pendiente" else "#44ff88")

        with st.expander(f"{icono} {item.get('equipo_nombre', '—')} — {item.get('tipo')} — {fecha}"):
            st.markdown(f"**Equipo:** {item.get('equipo_nombre', '—')}")
            st.markdown(f"**Tipo:** {item.get('tipo')}")
            st.markdown(f"**Técnico:** {item.get('tecnico', '—')}")
            st.markdown(f"**Prioridad:** {item.get('prioridad', 'Normal')}")
            st.markdown(f"<span style='color:{color_cr}'>**Fecha: {fecha}**</span>", unsafe_allow_html=True)
            st.markdown(f"**Descripción:** {item.get('descripcion', '—')}")
            st.markdown(f"**Estado:** {estado}")

            if estado != "Completado":
                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:12px; color:{COLOR};'>Completar mantenimiento:</div>", unsafe_allow_html=True)

                comp_obs = st.text_area("Observaciones del trabajo realizado", key=f"cr_obs_{item.get('id')}")
                comp_repuestos = st.text_input("Repuestos utilizados", key=f"cr_rep_{item.get('id')}")
                comp_fecha_real = st.date_input("Fecha real de ejecución", value=date.today(), key=f"cr_freal_{item.get('id')}")

                if st.button("✓ Marcar como completado", key=f"cr_comp_{item.get('id')}"):
                    # Actualizar cronograma
                    sb_patch(T_CRONOGRAMA, item.get("id"), {
                        "estado": "Completado",
                        "observaciones": comp_obs,
                        "repuestos": comp_repuestos,
                        "fecha_ejecucion": str(comp_fecha_real)
                    })
                    # Crear entrada en hoja de vida
                    sb_post(T_HOJAS, {
                        "equipo_id": item.get("equipo_id"),
                        "equipo_nombre": item.get("equipo_nombre"),
                        "tipo_mantenimiento": item.get("tipo"),
                        "fecha": str(comp_fecha_real),
                        "tecnico": item.get("tecnico"),
                        "trabajo_realizado": item.get("descripcion", "") + " | " + comp_obs,
                        "repuestos": comp_repuestos,
                        "observaciones": comp_obs
                    })
                    st.success("✓ Completado y registrado en hoja de vida")
                    st.rerun()


# ================================================================
# MÓDULO: HOJAS DE VIDA DE EQUIPOS
# ================================================================
elif menu == "Hojas de Vida":
    equipos = sb_get(T_EQUIPOS, "order=nombre.asc")
    hojas = sb_get(T_HOJAS, "order=fecha.desc")

    st.markdown(f"<div style='font-family:serif; font-size:20px; color:{COLOR};'>Hojas de Vida de Equipos</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(equipos)}</div><div class='metric-label'>EQUIPOS</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(hojas)}</div><div class='metric-label'>REGISTROS TOTALES</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Seleccionar equipo
    if equipos:
        opciones_eq = {f"{e.get('nombre')} — {e.get('marca')} {e.get('modelo')} (Serie: {e.get('serie', 'N/A')})": e.get("id") for e in equipos}
        equipo_sel = st.selectbox("Seleccionar equipo:", list(opciones_eq.keys()), key="hv_equipo")
        equipo_id = opciones_eq[equipo_sel]

        # Info del equipo
        equipo_data = next((e for e in equipos if e.get("id") == equipo_id), {})
        st.markdown(f"""
        <div class='equipo-card'>
            <div style='display:flex; justify-content:space-between; flex-wrap:wrap;'>
                <div><strong style='color:{COLOR};'>{equipo_data.get('nombre')}</strong> — {equipo_data.get('marca')} {equipo_data.get('modelo')}</div>
                <div style='color:#888; font-size:12px;'>Serie: {equipo_data.get('serie', '—')} | INVIMA: {equipo_data.get('registro_invima', '—')}</div>
            </div>
            <div style='color:#666; font-size:12px; margin-top:4px;'>
                Cliente: {equipo_data.get('cliente_nombre', '—')} | Ubicación: {equipo_data.get('ubicacion', '—')} | Riesgo: {equipo_data.get('clasificacion_riesgo', '—')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # Registrar mantenimiento manual en hoja de vida
        with st.expander("➕ Registrar mantenimiento manual"):
            hm1, hm2 = st.columns(2)
            with hm1:
                hv_tipo = st.selectbox("Tipo", ["Preventivo", "Correctivo", "Calibración", "Inspección"], key="hv_tipo")
                hv_fecha = st.date_input("Fecha", key="hv_fecha")
                hv_tecnico = st.text_input("Técnico", key="hv_tecnico")
            with hm2:
                hv_trabajo = st.text_area("Trabajo realizado", key="hv_trabajo")
                hv_repuestos = st.text_input("Repuestos", key="hv_repuestos")
                hv_obs = st.text_area("Observaciones", key="hv_obs")

            if st.button("✓ Registrar en hoja de vida", key="btn_hv"):
                sb_post(T_HOJAS, {
                    "equipo_id": equipo_id,
                    "equipo_nombre": equipo_sel.split(" — ")[0],
                    "tipo_mantenimiento": hv_tipo,
                    "fecha": str(hv_fecha),
                    "tecnico": hv_tecnico,
                    "trabajo_realizado": hv_trabajo,
                    "repuestos": hv_repuestos,
                    "observaciones": hv_obs
                })
                st.success("✓ Registrado en hoja de vida")
                st.rerun()

        # Historial del equipo seleccionado
        st.markdown(f"<div style='font-family:serif; font-size:14px; color:{COLOR}; margin:12px 0;'>Historial de mantenimiento</div>", unsafe_allow_html=True)

        hojas_equipo = [h for h in hojas if h.get("equipo_id") == equipo_id]

        if hojas_equipo:
            for h in hojas_equipo:
                tipo_color = {"Preventivo": "#44ff88", "Correctivo": "#ff4444", "Calibración": "#4488ff", "Inspección": "#ffaa44"}.get(h.get("tipo_mantenimiento"), "#888")
                st.markdown(f"""
                <div style='background:#0d0d0d; border:1px solid {COLOR}15; border-left:3px solid {tipo_color}; border-radius:4px; padding:12px 16px; margin:6px 0;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#e0e0e0; font-size:13px;'><strong>{h.get('tipo_mantenimiento')}</strong> — {h.get('fecha', '—')}</span>
                        <span style='color:{tipo_color}; font-size:11px;'>{h.get('tecnico', '—')}</span>
                    </div>
                    <div style='color:#888; font-size:12px; margin-top:4px;'>{h.get('trabajo_realizado', '—')}</div>
                    <div style='color:#666; font-size:11px; margin-top:2px;'>Repuestos: {h.get('repuestos', '—')} | Obs: {h.get('observaciones', '—')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Exportar hoja de vida
            if st.button("📊 Exportar hoja de vida a Excel", key="exp_hv"):
                df = pd.DataFrame(hojas_equipo)
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                nombre_eq = equipo_sel.split(" — ")[0].replace(" ", "_")
                st.download_button("Descargar", buffer.getvalue(), f"hoja_vida_{nombre_eq}_{date.today()}.xlsx")
        else:
            st.markdown("<div style='text-align:center; color:#555; padding:30px;'>No hay registros de mantenimiento para este equipo</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#555; padding:40px;'>Registra equipos primero en Inventario</div>", unsafe_allow_html=True)


# ================================================================
# MÓDULO FIJO: CLIENTES / CONSULTORIOS
# ================================================================
elif menu == "Clientes":
    clientes = sb_get(T_CLIENTES, "order=created_at.desc")
    equipos_all = sb_get(T_EQUIPOS, "order=nombre.asc")

    st.markdown(f"<div style='font-family:serif; font-size:20px; color:{COLOR};'>Clientes / Consultorios</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(clientes)}</div><div class='metric-label'>TOTAL CLIENTES</div></div>", unsafe_allow_html=True)
    with col2:
        activos_cli = len([c for c in clientes if c.get("estado") == "Activo"])
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#44ff88;'>{activos_cli}</div><div class='metric-label'>ACTIVOS</div></div>", unsafe_allow_html=True)
    with col3:
        total_eq = len(equipos_all)
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{total_eq}</div><div class='metric-label'>EQUIPOS TOTALES</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    with st.expander("➕ Nuevo cliente"):
        nc1, nc2 = st.columns(2)
        with nc1:
            cl_nombre = st.text_input("Nombre del consultorio / clínica", key="cl_nom")
            cl_contacto = st.text_input("Persona de contacto", key="cl_contacto")
            cl_telefono = st.text_input("Teléfono", key="cl_tel")
        with nc2:
            cl_email = st.text_input("Email", key="cl_email")
            cl_direccion = st.text_input("Dirección", key="cl_dir")
            cl_nit = st.text_input("NIT", key="cl_nit")

        cl_notas = st.text_area("Notas", key="cl_notas")

        if st.button("✓ Registrar cliente", key="btn_cl"):
            if cl_nombre:
                sb_post(T_CLIENTES, {
                    "nombre": cl_nombre, "contacto": cl_contacto,
                    "telefono": cl_telefono, "email": cl_email,
                    "direccion": cl_direccion, "nit": cl_nit,
                    "notas": cl_notas, "estado": "Activo"
                })
                st.success("✓ Cliente registrado")
                st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    for cliente in clientes:
        # Contar equipos de este cliente
        equipos_cliente = len([e for e in equipos_all if e.get("cliente_nombre") == cliente.get("nombre")])

        with st.expander(f"{cliente.get('nombre')} — {equipos_cliente} equipos"):
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(f"**Contacto:** {cliente.get('contacto', '—')}")
                st.markdown(f"**Teléfono:** {cliente.get('telefono', '—')}")
                st.markdown(f"**Email:** {cliente.get('email', '—')}")
            with cc2:
                st.markdown(f"**Dirección:** {cliente.get('direccion', '—')}")
                st.markdown(f"**NIT:** {cliente.get('nit', '—')}")
                st.markdown(f"**Equipos registrados:** {equipos_cliente}")

            st.markdown(f"**Notas:** {cliente.get('notas', '—')}")

            num = (cliente.get("telefono") or "").replace(" ", "").replace("-", "")
            if num:
                st.markdown(f"<a href='https://wa.me/57{num}' target='_blank' style='color:{COLOR};'>📱 WhatsApp</a>", unsafe_allow_html=True)


# ================================================================
# MÓDULO FIJO: ALERTAS
# ================================================================
elif menu == "Alertas":
    alertas = sb_get(T_ALERTAS, "order=fecha_vencimiento.asc")

    st.markdown(f"<div style='font-family:serif; font-size:20px; color:{COLOR};'>Alertas y Vencimientos</div>", unsafe_allow_html=True)

    hoy = date.today()
    vencidas = [a for a in alertas if a.get("fecha_vencimiento") and a.get("fecha_vencimiento") < str(hoy) and a.get("estado") != "Completada"]
    proximas = [a for a in alertas if a.get("fecha_vencimiento") and str(hoy) <= a.get("fecha_vencimiento") <= str(hoy + timedelta(days=7)) and a.get("estado") != "Completada"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#ff4444;'>{len(vencidas)}</div><div class='metric-label'>VENCIDAS</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-num' style='color:#ffaa44;'>{len(proximas)}</div><div class='metric-label'>PRÓX. 7 DÍAS</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-num'>{len(alertas)}</div><div class='metric-label'>TOTAL</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    with st.expander("➕ Nueva alerta"):
        al_titulo = st.text_input("Título", key="al_tit", placeholder="Calibración autoclave, Vencimiento certificado...")
        al_desc = st.text_area("Descripción", key="al_desc")
        al_fecha = st.date_input("Fecha de vencimiento", key="al_fecha")
        al_prioridad = st.selectbox("Prioridad", ["Normal", "Alta", "Urgente"], key="al_pri")

        if st.button("✓ Crear alerta", key="btn_al"):
            if al_titulo:
                sb_post(T_ALERTAS, {
                    "titulo": al_titulo, "descripcion": al_desc,
                    "fecha_vencimiento": str(al_fecha), "prioridad": al_prioridad,
                    "estado": "Pendiente"
                })
                st.success("✓ Alerta creada")
                st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    for alerta in alertas:
        if alerta.get("estado") == "Completada":
            continue
        fecha = alerta.get("fecha_vencimiento", "")
        es_vencida = fecha and fecha < str(hoy)
        color_a = "#ff4444" if es_vencida else ("#ffaa44" if fecha and fecha <= str(hoy + timedelta(days=7)) else "#888")

        with st.expander(f"{'🔴' if es_vencida else '🟡'} {alerta.get('titulo')} — {fecha}"):
            st.markdown(f"**Descripción:** {alerta.get('descripcion', '—')}")
            st.markdown(f"**Prioridad:** {alerta.get('prioridad', 'Normal')}")
            st.markdown(f"<span style='color:{color_a}'>**Vence:** {fecha}</span>", unsafe_allow_html=True)

            if st.button("✓ Marcar completada", key=f"al_comp_{alerta.get('id')}"):
                sb_patch(T_ALERTAS, alerta.get("id"), {"estado": "Completada"})
                st.rerun()


# ================================================================
# MÓDULO FIJO: DOCUMENTOS
# ================================================================
elif menu == "Documentos":
    st.markdown(f"<div style='font-family:serif; font-size:20px; color:{COLOR};'>Documentos</div>", unsafe_allow_html=True)

    archivo = st.file_uploader("Subir documento", type=["pdf", "png", "jpg", "jpeg", "doc", "docx", "xlsx"])
    if archivo:
        if st.button("📤 Subir", key="btn_upload"):
            url = subir_documento(archivo)
            if url:
                st.success("✓ Documento subido")
                st.markdown(f"[Ver documento]({url})")
            else:
                st.error("Error al subir")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:serif; font-size:14px; color:{COLOR};'>Documentos almacenados</div>", unsafe_allow_html=True)

    docs = listar_documentos()
    if docs:
        for doc in docs:
            nombre_doc = doc.get("name", "")
            if nombre_doc:
                url_doc = f"{SUPABASE_URL}/storage/v1/object/public/documentos/{SLUG}/{nombre_doc}"
                st.markdown(f"""
                <div style='background:#111; border:1px solid {COLOR}22; padding:10px 16px; border-radius:4px; margin:4px 0; display:flex; justify-content:space-between; align-items:center;'>
                    <span style='color:#e0e0e0; font-size:13px;'>📄 {nombre_doc}</span>
                    <a href='{url_doc}' target='_blank' style='color:{COLOR}; font-size:11px;'>Descargar</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#555; padding:30px;'>No hay documentos subidos</div>", unsafe_allow_html=True)


# -------- FOOTER --------
st.markdown(f"""
<div style='text-align:center; padding:20px 0; margin-top:30px; border-top:1px solid {COLOR}22;
    font-family:serif; font-size:10px; color:{COLOR}66; letter-spacing:3px;'>
    {NOMBRE_EMPRESA.upper()} — POWERED BY A.R.I.Z.A.
</div>
""", unsafe_allow_html=True)
