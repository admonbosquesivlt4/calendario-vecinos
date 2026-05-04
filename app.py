import streamlit as st
import requests
import pandas as pd
from datetime import date
import calendar

# ── CONFIG ─────────────────────────────
st.set_page_config(page_title="Avisos Vecinales", page_icon="🏘️", layout="wide")

SUPABASE_URL = "https://fhaqdadmudrdphlhabph.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "Temporal123!")

MESES_ES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

COLORES_EVENTO = {
    "Reunión": "#2E7D32",
    "Pago": "#C62828",
    "Aviso": "#185FA5",
    "Evento": "#6A1B9A"
}

# ── SUPABASE ───────────────────────────
def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def supa_get(tabla, params=""):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{tabla}?{params}", headers=headers())
    return r.json() if r.status_code == 200 else []

def supa_post(tabla, data):
    return requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=headers(), json=data).status_code in (200,201)

def supa_delete(tabla, filtro):
    return requests.delete(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=headers()).status_code in (200,204)

# ── DATA ───────────────────────────────
@st.cache_data
def cargar_eventos():
    data = supa_get("eventos", "select=*&order=fecha.asc")
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["id","fecha","titulo","color"])

def filtrar_eventos(df, fecha):
    if df.empty:
        return pd.DataFrame()
    return df[df["fecha"] == fecha]

# ── LOGIN ──────────────────────────────
def login_vecino(lote, depto, pin):
    data = supa_get("vecinos",
        f"lote=ilike.{lote}&depto=ilike.{depto}&pin=eq.{pin}&select=*")
    return data[0] if data else None

# ── SESSION ────────────────────────────
def init_session():
    defaults = {
        "modo": None,
        "vecino": None,
        "year": date.today().year,
        "month": date.today().month,
        "fecha": None,
        "intentos": 0
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── CALENDARIO ─────────────────────────
def render_calendar(eventos, admin=False):
    year = st.session_state.year
    month = st.session_state.month

    st.subheader(f"📅 {MESES_ES[month]} {year}")

    c1, c2, c3 = st.columns([1,2,1])

    with c1:
        if st.button("⬅"):
            st.session_state.month = 12 if month == 1 else month - 1
            if month == 1: st.session_state.year -= 1
            st.rerun()

    with c3:
        if st.button("➡"):
            st.session_state.month = 1 if month == 12 else month + 1
            if month == 12: st.session_state.year += 1
            st.rerun()

    dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    cols = st.columns(7)
    for i, d in enumerate(dias):
        cols[i].markdown(f"**{d}**")

    cal = calendar.monthcalendar(year, month)

    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            if dia == 0:
                cols[i].write("")
            else:
                fecha = date(year, month, dia)
                f_str = str(fecha)
                eventos_dia = filtrar_eventos(eventos, f_str)

                with cols[i]:
                    if st.button(str(dia), key=f"dia_{f_str}"):
                        st.session_state.fecha = fecha

                    if not eventos_dia.empty:
                        for _, ev in eventos_dia.iterrows():
                            st.markdown(f"🟢 {ev['titulo']}")

    # ── PANEL DETALLE ─────────────────
    if st.session_state.fecha:
        st.divider()
        f = str(st.session_state.fecha)
        st.subheader(f"📌 {f}")

        eventos_dia = filtrar_eventos(eventos, f)

        if not eventos_dia.empty:
            for _, ev in eventos_dia.iterrows():
                c1, c2 = st.columns([5,1])
                c1.success(ev["titulo"])
                if admin:
                    if c2.button("🗑", key=f"del_{ev['id']}"):
                        supa_delete("eventos", f"id=eq.{ev['id']}")
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.info("Sin eventos")

        if admin:
            st.markdown("### ➕ Nuevo evento")
            titulo = st.text_input("Título")
            tipo = st.selectbox("Tipo", list(COLORES_EVENTO.keys()))

            if st.button("Guardar"):
                if not titulo:
                    st.warning("Falta título")
                else:
                    supa_post("eventos", {
                        "titulo": titulo,
                        "fecha": f,
                        "color": COLORES_EVENTO[tipo]
                    })
                    st.success("Guardado")
                    st.cache_data.clear()
                    st.rerun()

# ── RESUMEN ────────────────────────────
def resumen_eventos(eventos):
    st.markdown("### 📢 Próximos eventos")

    if eventos.empty:
        st.info("Sin eventos")
        return

    hoy = str(date.today())
    futuros = eventos[eventos["fecha"] >= hoy]

    if futuros.empty:
        st.info("No hay próximos eventos")
    else:
        for _, ev in futuros.head(5).iterrows():
            st.markdown(f"📅 {ev['fecha']} — {ev['titulo']}")

# ── PANTALLAS ──────────────────────────
def inicio():
    st.title("🏘️ Avisos Vecinales")

    c1, c2 = st.columns(2)
    if c1.button("👤 Vecino"):
        st.session_state.modo = "login_vecino"
        st.rerun()
    if c2.button("🔐 Admin"):
        st.session_state.modo = "login_admin"
        st.rerun()

def login_vecino_ui():
    st.title("Acceso Vecino")

    lote = st.text_input("Lote")
    depto = st.text_input("Depto")
    pin = st.text_input("PIN", type="password")

    if st.button("Entrar"):
        if st.session_state.intentos >= 5:
            st.error("Bloqueado")
            return

        v = login_vecino(lote, depto, pin)
        if v:
            st.session_state.vecino = v
            st.session_state.modo = "vecino"
            st.session_state.intentos = 0
            st.rerun()
        else:
            st.session_state.intentos += 1
            st.error("Datos incorrectos")

def vista_vecino():
    v = st.session_state.vecino
    st.markdown(f"👤 **{v['nombre']} {v['apellido']}**")

    eventos = cargar_eventos()
    render_calendar(eventos)
    resumen_eventos(eventos)

    if st.button("Salir"):
        st.session_state.clear()
        st.rerun()

def login_admin():
    st.title("Admin")
    pwd = st.text_input("Password", type="password")

    if st.button("Entrar"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.modo = "admin"
            st.rerun()
        else:
            st.error("Incorrecto")

def admin():
    st.title("Panel Admin")

    eventos = cargar_eventos()
    render_calendar(eventos, admin=True)
    resumen_eventos(eventos)

    if st.button("Salir"):
        st.session_state.clear()
        st.rerun()

# ── MAIN ───────────────────────────────
def main():
    init_session()

    modo = st.session_state.modo

    if modo is None:
        inicio()
    elif modo == "login_vecino":
        login_vecino_ui()
    elif modo == "vecino":
        vista_vecino()
    elif modo == "login_admin":
        login_admin()
    elif modo == "admin":
        admin()

if __name__ == "__main__":
    main()