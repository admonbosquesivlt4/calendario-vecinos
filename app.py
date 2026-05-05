import streamlit as st
import requests
import pandas as pd
from datetime import date
import calendar

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Avisos Vecinales Bosques IV Lote 4",
    page_icon="🏘️",
    layout="centered"
)

SUPABASE_URL = "https://fhaqdadmudrdphlhabph.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin1234")

# ── HEADERS ────────────────────────────────────────
def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

# ── SUPABASE ───────────────────────────────────────
def supa_get(tabla):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{tabla}?select=*", headers=headers())
        return r.json() if r.status_code == 200 else []
    except:
        return []

def supa_post(tabla, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=headers(), json=data)
        return r.status_code in (200, 201)
    except:
        return False

# ── DATA ───────────────────────────────────────────
@st.cache_data(ttl=30)
def cargar_eventos():
    data = supa_get("eventos")
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["fecha","titulo","color"])

@st.cache_data(ttl=60)
def cargar_vecinos():
    data = supa_get("vecinos")
    return pd.DataFrame(data) if data else pd.DataFrame()

# ── LOGIN VECINO (ROBUSTO) ─────────────────────────
def login_vecino():
    st.title("🏘️ Avisos Vecinales Bosques IV Lote 4")

    lote = st.text_input("Lote")
    depto = st.text_input("Depto")
    pin = st.text_input("PIN", type="password")

    if st.button("Ingresar", use_container_width=True):
        vecinos = cargar_vecinos()

        if vecinos.empty:
            st.error("No hay vecinos registrados")
            return

        # 🔥 NORMALIZACIÓN
        vecinos["lote"] = vecinos["lote"].astype(str).str.strip().str.upper()
        vecinos["depto"] = vecinos["depto"].astype(str).str.strip().str.upper()
        vecinos["pin"] = vecinos["pin"].astype(str).str.strip()

        lote_input = lote.strip().upper()
        depto_input = depto.strip().upper()
        pin_input = pin.strip()

        user = vecinos[
            (vecinos["lote"] == lote_input) &
            (vecinos["depto"] == depto_input) &
            (vecinos["pin"] == pin_input)
        ]

        if not user.empty:
            st.session_state["login"] = True
            st.session_state["user"] = user.iloc[0].to_dict()
            st.success("Bienvenido 👋")
            st.rerun()
        else:
            st.error("Datos incorrectos")

# ── CALENDARIO RESPONSIVO ──────────────────────────
def render_calendar(eventos):

    today = date.today()
    year = today.year
    month = today.month

    st.subheader(f"📅 {calendar.month_name[month]} {year}")

    ev_dict = {}
    for _, ev in eventos.iterrows():
        ev_dict.setdefault(ev["fecha"], []).append(ev)

    # Detectar móvil
    is_mobile = st.sidebar.checkbox("Modo móvil", value=False)

    cols = 2 if is_mobile else 7
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

# ── VISTA VECINO ───────────────────────────────────
def pantalla_vecino():
    user = st.session_state["user"]

    st.markdown(f"""
    <div style='padding:10px;background:#f5f5f5;border-radius:10px'>
    👤 <b>{user.get('nombre','')}</b><br>
    Lote: {user.get('lote','')} | Depto: {user.get('depto','')}
    </div>
    """, unsafe_allow_html=True)

    eventos = cargar_eventos()

    # 🔥 LISTA PRIMERO (MEJOR UX)
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
    else:
        st.info("No hay eventos")

    st.divider()

    render_calendar(eventos)

# ── ADMIN ──────────────────────────────────────────
def pantalla_admin():
    st.title("🔐 Administración")

    eventos = cargar_eventos()
    render_calendar(eventos)

    st.divider()

    st.subheader("➕ Nuevo evento")

    titulo = st.text_input("Título")
    fecha = st.date_input("Fecha")

    if st.button("Guardar evento", use_container_width=True):
        if not titulo:
            st.error("Falta título")
        else:
            ok = supa_post("eventos", {
                "titulo": titulo,
                "fecha": str(fecha),
                "color": "#185FA5"
            })

            if ok:
                st.success("Evento guardado")
                st.rerun()
            else:
                st.error("Error al guardar")

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
