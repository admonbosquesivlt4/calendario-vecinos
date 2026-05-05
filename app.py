import streamlit as st
import requests
import pandas as pd
from datetime import date
import calendar

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(page_title="Avisos", page_icon="🏘️", layout="centered")

SUPABASE_URL = "https://fhaqdadmudrdphlhabph.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin1234")

# ── CSS (LOOK APP) ─────────────────────────────────
st.markdown("""
<style>
.card {
    background: #ffffff;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}
.event {
    padding:6px;
    border-radius:6px;
    margin-top:5px;
    font-size:13px;
}
.header {
    font-size:20px;
    font-weight:600;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ── SUPABASE ───────────────────────────────────────
def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY},
        "Content-Type": "application/json",
    }

def supa_get(tabla):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{tabla}?select=*", headers=headers())
    return r.json() if r.status_code == 200 else []

def supa_post(tabla, data):
    return requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=headers(), json=data).status_code in (200,201)

# ── DATA ───────────────────────────────────────────
@st.cache_data
def cargar_eventos():
    data = supa_get("eventos")
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["fecha","titulo","color"])

@st.cache_data
def cargar_vecinos():
    data = supa_get("vecinos")
    return pd.DataFrame(data) if data else pd.DataFrame()

# ── LOGIN ──────────────────────────────────────────
def login_vecino():
    st.markdown("<div class='header'>🏘️ Avisos Bosques IV Lote 4</div>", unsafe_allow_html=True)

    lote = st.text_input("Lote")
    depto = st.text_input("Depto")
    pin = st.text_input("PIN", type="password")

    if st.button("Ingresar", use_container_width=True):
        vecinos = cargar_vecinos()

        vecinos["lote"] = vecinos["lote"].astype(str).str.strip().str.upper()
        vecinos["depto"] = vecinos["depto"].astype(str).str.strip().str.upper()
        vecinos["pin"] = vecinos["pin"].astype(str).str.strip()

        user = vecinos[
            (vecinos["lote"] == lote.strip().upper()) &
            (vecinos["depto"] == depto.strip().upper()) &
            (vecinos["pin"] == pin.strip())
        ]

        if not user.empty:
            st.session_state["login"] = True
            st.session_state["user"] = user.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Datos incorrectos")

# ── CALENDARIO PRO ─────────────────────────────────
def render_calendar(eventos):

    # Estado mes
    if "year" not in st.session_state:
        st.session_state.year = date.today().year
        st.session_state.month = date.today().month

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        if st.button("◀"):
            if st.session_state.month == 1:
                st.session_state.month = 12
                st.session_state.year -= 1
            else:
                st.session_state.month -= 1

    with col2:
        st.markdown(f"<div class='header'>{calendar.month_name[st.session_state.month]} {st.session_state.year}</div>", unsafe_allow_html=True)

    with col3:
        if st.button("▶"):
            if st.session_state.month == 12:
                st.session_state.month = 1
                st.session_state.year += 1
            else:
                st.session_state.month += 1

    if st.button("Hoy"):
        st.session_state.year = date.today().year
        st.session_state.month = date.today().month

    ev_dict = {}
    for _, ev in eventos.iterrows():
        ev_dict.setdefault(ev["fecha"], []).append(ev)

    semanas = calendar.monthcalendar(st.session_state.year, st.session_state.month)

    for semana in semanas:
        cols = st.columns(7)

        for i, dia in enumerate(semana):
            if dia == 0:
                continue

            fecha_str = f"{st.session_state.year}-{st.session_state.month:02d}-{dia:02d}"

            with cols[i]:
                st.markdown(f"<div class='card'><b>{dia}</b>", unsafe_allow_html=True)

                if fecha_str in ev_dict:
                    for ev in ev_dict[fecha_str]:
                        st.markdown(f"<div class='event' style='background:{ev.get('color','#ddd')}22'>{ev['titulo']}</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

# ── VISTA VECINO ───────────────────────────────────
def pantalla_vecino():
    user = st.session_state["user"]

    st.markdown(f"<div class='card'>👤 {user.get('nombre')} | Lote {user.get('lote')}</div>", unsafe_allow_html=True)

    eventos = cargar_eventos()

    st.markdown("<div class='header'>📅 Próximos eventos</div>", unsafe_allow_html=True)

    if not eventos.empty:
        eventos = eventos.sort_values("fecha")
        for _, ev in eventos.iterrows():
            st.markdown(f"<div class='card'><b>{ev['titulo']}</b><br>{ev['fecha']}</div>", unsafe_allow_html=True)

    render_calendar(eventos)

# ── ADMIN ──────────────────────────────────────────
def pantalla_admin():
    st.title("Admin")

    eventos = cargar_eventos()

    render_calendar(eventos)

    st.divider()

    titulo = st.text_input("Evento")
    fecha = st.date_input("Fecha")

    if st.button("Guardar"):
        supa_post("eventos", {
            "titulo": titulo,
            "fecha": str(fecha),
            "color": "#185FA5"
        })
        st.success("Guardado")
        st.rerun()

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
        if not st.session_state["login"]:
            login_vecino()
        else:
            pantalla_vecino()

main()
