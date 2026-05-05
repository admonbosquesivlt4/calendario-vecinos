import streamlit as st
import requests
import pandas as pd
from datetime import date
import calendar

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(page_title="Avisos Bosques IV - Lote 4", page_icon="🏘️", layout="centered")

SUPABASE_URL = "https://fhaqdadmudrdphlhabph.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin1234")

DEBUG = False  # 🔥 Cambia a True si quieres ver logs

# ── ESTILOS ────────────────────────────────────────
st.markdown("""
<style>
.card {background:#fff;padding:10px;border-radius:12px;margin-bottom:8px;box-shadow:0 2px 6px rgba(0,0,0,0.08);}
.event {padding:5px;border-radius:6px;margin-top:4px;font-size:12px;}
.header {text-align:center;font-weight:600;font-size:18px;}
</style>
""", unsafe_allow_html=True)

# ── SUPABASE ───────────────────────────────────────
def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def supa_get(tabla):
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{tabla}?select=*",
            headers=headers(),
            timeout=10
        )

        if r.status_code != 200:
            if DEBUG:
                st.error(f"Error Supabase {tabla}: {r.status_code}")
                st.write(r.text)
            return []

        return r.json()

    except Exception as e:
        if DEBUG:
            st.error(f"Error conexión: {e}")
        return []

def supa_post(tabla, data):
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{tabla}",
            headers=headers(),
            json=data
        )
        return r.status_code in (200, 201)
    except:
        return False

# ── DATA ───────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_eventos():
    data = supa_get("eventos")

    if not data:
        return pd.DataFrame(columns=["fecha","titulo","color"])

    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["fecha","titulo","color"])

    df.columns = df.columns.str.strip().str.lower()

    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["fecha_str"] = df["fecha"].dt.strftime("%Y-%m-%d")

    return df

@st.cache_data(ttl=120)
def cargar_vecinos():
    data = supa_get("vecinos")

    if not data or not isinstance(data, list):
        return pd.DataFrame(columns=["lote","depto","pin","nombre"])

    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["lote","depto","pin","nombre"])

    df.columns = df.columns.str.strip().str.lower()

    return df

# ── LOGIN ──────────────────────────────────────────
def login_vecino():
    st.markdown("## 🏘️ Avisos Bosques IV - Lote 4")

    lote = st.text_input("Lote")
    depto = st.text_input("Depto")
    pin = st.text_input("PIN", type="password")

    if st.button("Ingresar", use_container_width=True):
        vecinos = cargar_vecinos()

        if DEBUG:
            st.write("Vecinos:", vecinos.shape)
            st.write("Columnas:", vecinos.columns.tolist())

        if vecinos.empty:
            st.error("No hay vecinos registrados o falla conexión")
            return

        for col in ["lote", "depto", "pin"]:
            if col not in vecinos.columns:
                st.error(f"Falta columna '{col}' en BD")
                if DEBUG:
                    st.write(vecinos.columns.tolist())
                return

        vecinos["lote"] = vecinos["lote"].astype(str).str.strip().str.upper()
        vecinos["depto"] = vecinos["depto"].astype(str).str.strip().str.upper()
        vecinos["pin"] = vecinos["pin"].astype(str).str.strip()

        user = vecinos[
            (vecinos["lote"] == lote.strip().upper()) &
            (vecinos["depto"] == depto.strip().upper()) &
            (vecinos["pin"] == pin.strip())
        ]

        if not user.empty:
            st.session_state.login = True
            st.session_state.user = user.iloc[0].to_dict()
            st.success("Bienvenido 👋")
            st.rerun()
        else:
            st.error("Datos incorrectos")

# ── CALENDARIO ─────────────────────────────────────
def render_calendar(eventos):

    if "year" not in st.session_state:
        st.session_state.year = date.today().year
        st.session_state.month = date.today().month

    # Navegación
    c1, c2, c3 = st.columns([1,2,1])

    with c1:
        if st.button("◀"):
            if st.session_state.month == 1:
                st.session_state.month = 12
                st.session_state.year -= 1
            else:
                st.session_state.month -= 1
            st.rerun()

    with c2:
        st.markdown(f"<div class='header'>{calendar.month_name[st.session_state.month]} {st.session_state.year}</div>", unsafe_allow_html=True)

    with c3:
        if st.button("▶"):
            if st.session_state.month == 12:
                st.session_state.month = 1
                st.session_state.year += 1
            else:
                st.session_state.month += 1
            st.rerun()

    if st.button("Hoy"):
        st.session_state.year = date.today().year
        st.session_state.month = date.today().month
        st.rerun()

    # Días
    dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    cols = st.columns(7)
    for i, d in enumerate(dias):
        with cols[i]:
            st.markdown(f"<div style='text-align:center;font-weight:600'>{d}</div>", unsafe_allow_html=True)

    # Eventos
    ev_dict = {}
    if not eventos.empty:
        for _, ev in eventos.iterrows():
            ev_dict.setdefault(ev["fecha_str"], []).append(ev)

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
                        st.markdown(
                            f"<div class='event' style='background:{ev.get('color','#ddd')}22'>{ev['titulo']}</div>",
                            unsafe_allow_html=True
                        )

                st.markdown("</div>", unsafe_allow_html=True)

# ── VECINO ─────────────────────────────────────────
def pantalla_vecino():
    user = st.session_state.user

    st.markdown(f"<div class='card'>👤 {user.get('nombre','')} | Lote {user.get('lote','')}</div>", unsafe_allow_html=True)

    eventos = cargar_eventos()

    st.markdown("### 📅 Próximos eventos")

    if not eventos.empty:
        futuros = eventos[eventos["fecha"] >= pd.to_datetime(date.today())]
        for _, ev in futuros.iterrows():
            st.markdown(
                f"<div class='card'><b>{ev['titulo']}</b><br>{ev['fecha_str']}</div>",
                unsafe_allow_html=True
            )

    render_calendar(eventos)

# ── ADMIN ──────────────────────────────────────────
def pantalla_admin():
    st.title("🔐 Administración")

    eventos = cargar_eventos()
    render_calendar(eventos)

    st.divider()

    titulo = st.text_input("Evento")
    fecha = st.date_input("Fecha")

    if st.button("Guardar"):
        if titulo:
            ok = supa_post("eventos", {
                "titulo": titulo,
                "fecha": str(fecha),
                "color": "#185FA5"
            })
            if ok:
                st.success("Guardado")
                st.rerun()
            else:
                st.error("Error al guardar")

# ── MAIN ───────────────────────────────────────────
def main():

    if "login" not in st.session_state:
        st.session_state.login = False

    menu = st.sidebar.selectbox("Modo", ["Vecino", "Admin"])

    if menu == "Admin":
        pwd = st.sidebar.text_input("Password", type="password")
        if pwd == ADMIN_PASSWORD:
            pantalla_admin()
    else:
        if not st.session_state.login:
            login_vecino()
        else:
            pantalla_vecino()

main()
