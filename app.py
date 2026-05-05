import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
import calendar

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Avisos Vecinales",
    page_icon="🏘️",
    layout="centered"
)

SUPABASE_URL = "https://fhaqdadmudrdphlhabph.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin1234")

# ── HELPERS ────────────────────────────────────────
def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def supa_get(tabla):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{tabla}?select=*", headers=headers())
    return r.json() if r.status_code == 200 else []

def supa_post(tabla, data):
    return requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=headers(), json=data).status_code in (200,201)

# ── DATA ───────────────────────────────────────────
@st.cache_data(ttl=30)
def cargar_eventos():
    data = supa_get("eventos")
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["fecha","titulo","color"])

@st.cache_data(ttl=60)
def cargar_vecinos():
    data = supa_get("vecinos")
    return pd.DataFrame(data) if data else pd.DataFrame()

# ── LOGIN VECINO ───────────────────────────────────
def login_vecino():
    st.title("🏘️ Avisos Vecinales")

    lote = st.text_input("Lote")
    depto = st.text_input("Depto")
    pin = st.text_input("PIN", type="password")

    if st.button("Ingresar", use_container_width=True):
        vecinos = cargar_vecinos()

        if vecinos.empty:
            st.error("No hay vecinos registrados")
            return

        user = vecinos[
            (vecinos["lote"] == lote.upper()) &
            (vecinos["depto"] == depto.upper()) &
            (vecinos["pin"] == pin)
        ]

        if not user.empty:
            st.session_state["login"] = True
            st.session_state["user"] = user.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Datos incorrectos")

# ── CALENDARIO RESPONSIVO ──────────────────────────
def render_calendar(eventos):

    today = date.today()
    year = today.year
    month = today.month

    st.subheader(f"📅 {calendar.month_name[month]} {year}")

    # Agrupar eventos
    ev_dict = {}
    for _, ev in eventos.iterrows():
        ev_dict.setdefault(ev["fecha"], []).append(ev)

    # Detectar ancho (aproximado)
    cols = 7
    is_mobile = st.sidebar.checkbox("Modo móvil", value=False)

    if is_mobile:
        cols = 2

    semanas = calendar.monthcalendar(year, month)

    for semana in semanas:
        columnas = st.columns(cols)

        for i, dia in enumerate(semana):
            if dia == 0:
                continue

            col = columnas[i % cols]

            with col:
                fecha_str = f"{year}-{month:02d}-{dia:02d}"

                st.markdown(f"### {dia}")

                # eventos visibles
                if fecha_str in ev_dict:
                    for ev in ev_dict[fecha_str]:
                        st.markdown(f"""
                        <div style='background:{ev.get("color","#ddd")}22;
                                    padding:6px;
                                    border-radius:8px;
                                    margin-bottom:5px'>
                        {ev['titulo']}
                        </div>
                        """, unsafe_allow_html=True)

# ── ADMIN ──────────────────────────────────────────
def pantalla_admin():
    st.title("🔐 Admin")

    eventos = cargar_eventos()
    render_calendar(eventos)

    st.divider()
    st.subheader("➕ Nuevo evento")

    titulo = st.text_input("Título")
    fecha = st.date_input("Fecha")

    if st.button("Guardar", use_container_width=True):
        supa_post("eventos", {
            "titulo": titulo,
            "fecha": str(fecha),
            "color": "#185FA5"
        })
        st.success("Guardado")
        st.rerun()

# ── VISTA VECINO ───────────────────────────────────
def pantalla_vecino():
    user = st.session_state["user"]

    st.markdown(f"👤 {user['nombre']} - Lote {user['lote']}")

    eventos = cargar_eventos()

    # 🔥 PRIMERO LISTA (MEJOR EN MOBILE)
    st.subheader("📅 Próximos eventos")

    if not eventos.empty:
        eventos = eventos.sort_values("fecha")
        for _, ev in eventos.iterrows():
            st.markdown(f"""
            <div style='padding:10px;
                        border-left:4px solid #185FA5;
                        margin-bottom:10px;
                        background:#fafafa'>
            <b>{ev['titulo']}</b><br>
            {ev['fecha']}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # 🔥 CALENDARIO
    render_calendar(eventos)

# ── MAIN ───────────────────────────────────────────
def main():

    if "login" not in st.session_state:
        st.session_state["login"] = False

    menu = st.sidebar.selectbox("Modo", ["Vecino", "Admin"])

    if menu == "Admin":
        pwd = st.sidebar.text_input("Password", type="password")
        if pwd == ADMIN_PASSWORD:
            pantalla_admin()
        else:
            st.warning("Acceso restringido")

    else:
        if not st.session_state["login"]:
            login_vecino()
        else:
            pantalla_vecino()

if __name__ == "__main__":
    main()
