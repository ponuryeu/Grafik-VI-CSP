import streamlit as st
import datetime
import pandas as pd
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# --- CONFIG STRONY ---
st.set_page_config(
    page_title="Grafik Służb VI Kompanii CSP Legionowo",
    page_icon="🚔",
    layout="wide"
)

DATA_FILE = "data.json"

# --- STYL POLICYJNY (TACTICAL COMMAND CENTER) ---
police_theme_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    :root {
        --police-dark: #0a0f1d;
        --police-card: #121929;
        --police-card-hover: #1a2338;
        --police-blue: #1d4ed8;
        --police-blue-light: #3b82f6;
        --police-cyan: #38bdf8;
        --police-border: #1e293b;
        --police-border-glow: #2563eb;
        --text-main: #f8fafc;
        --text-muted: #64748b;
        --badge-gold: #f59e0b;
        --badge-red: #ef4444;
        --badge-green: #10b981;
    }

    .stApp {
        background-color: var(--police-dark);
        color: var(--text-main);
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: var(--police-card);
        border-right: 1px solid var(--police-border);
    }

    .police-header {
        background: linear-gradient(135deg, rgba(29, 78, 216, 0.2) 0%, rgba(18, 25, 41, 0.9) 100%);
        border: 1px solid var(--police-border-glow);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 10px 30px -10px rgba(29, 78, 216, 0.3);
        margin-bottom: 25px;
        position: relative;
    }
    .police-header::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, transparent, var(--police-blue-light), transparent);
    }
    .police-tag {
        display: inline-block;
        background: rgba(37, 99, 235, 0.2);
        color: var(--police-cyan);
        border: 1px solid rgba(56, 189, 248, 0.4);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .police-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }
    .police-subtitle {
        color: var(--text-muted);
        font-size: 0.9rem;
        margin-top: 6px;
    }
    .police-author {
        margin-top: 12px;
        font-size: 0.85rem;
        color: var(--police-cyan);
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .stat-card {
        background: var(--police-card);
        border: 1px solid var(--police-border);
        border-radius: 16px;
        padding: 18px;
        text-align: center;
    }
    .stat-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .stat-num {
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--police-cyan);
        margin-top: 4px;
    }

    .duty-card {
        background: var(--police-card);
        border: 1px solid var(--police-border);
        border-left: 4px solid var(--police-blue-light);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .badge {
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-pisarka { background: rgba(147, 51, 234, 0.2); color: #c084fc; border: 1px solid #a855f7; }
    .badge-dowodca { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
    .badge-wyróżnienie { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981; }
    .badge-standard { background: rgba(100, 116, 139, 0.2); color: #cbd5e1; border: 1px solid #475569; }
    .badge-l1 { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid #f59e0b; }
    .badge-l2 { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--police-card);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid var(--police-border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 10px;
        color: var(--text-muted);
        font-weight: 600;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--police-blue) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4);
    }

    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, var(--police-blue) 0%, #1e40af 100%);
        color: #ffffff;
        border: 1px solid var(--police-blue-light);
        border-radius: 10px;
        padding: 8px 20px;
        font-weight: 700;
    }

    [data-testid="stDataFrame"] {
        background: var(--police-card);
        border-radius: 14px;
        border: 1px solid var(--police-border);
    }
</style>
"""
st.markdown(police_theme_css, unsafe_allow_html=True)

# --- MODEL DANYCH ---
@dataclass
class Person:
    id: str
    platoon: int
    points: int = 0
    role: str = "student"
    active: bool = True
    day_shifts: int = 0
    night_shifts: int = 0
    weekend_shifts: int = 0
    assigned_duties: set = field(default_factory=set)
    point_history: list = field(default_factory=list)

    @property
    def total_shifts(self) -> int:
        return self.day_shifts + self.night_shifts

    @property
    def status_html(self) -> str:
        if self.role == "pisarka":
            return '<span class="badge badge-pisarka">✍️ PISARKA</span>'
        if self.role == "dowodca":
            return '<span class="badge badge-dowodca">⭐ DOWÓDCA</span>'
        if self.points >= 5:
            return '<span class="badge badge-wyróżnienie">🟢 WYRÓŻNIENIE</span>'
        if -5 <= self.points <= -1:
            return '<span class="badge badge-l1">🟡 CZARNA LISTA L1</span>'
        if self.points <= -6:
            return '<span class="badge badge-l2">🔴 CZARNA LISTA L2</span>'
        return '<span class="badge badge-standard">⚪ STANDARD</span>'


# --- PERSISTENCE (ZAPIS I ODCZYT Z DYSKU) ---
def export_backup_json() -> str:
    data = {
        "pins": st.session_state.pins,
        "objects": st.session_state.objects,
        "people": {},
        "schedule": {}
    }
    for p_id, p in st.session_state.people.items():
        data["people"][p_id] = {
            "id": p.id,
            "platoon": p.platoon,
            "points": p.points,
            "role": p.role,
            "active": p.active,
            "day_shifts": p.day_shifts,
            "night_shifts": p.night_shifts,
            "weekend_shifts": p.weekend_shifts,
            "assigned_duties": [[d.isoformat(), s] for d, s in p.assigned_duties],
            "point_history": p.point_history
        }
    for d_obj, shifts in st.session_state.schedule.items():
        data["schedule"][d_obj.isoformat()] = shifts
    return json.dumps(data, indent=2, ensure_ascii=False)


def import_backup_json(json_str: str):
    data = json.loads(json_str)
    if "pins" in data:
        st.session_state.pins = data["pins"]
    if "objects" in data:
        st.session_state.objects = data["objects"]

    new_people = {}
    for p_id, p_data in data.get("people", {}).items():
        duties = set()
        for d_str, s in p_data.get("assigned_duties", []):
            duties.add((datetime.date.fromisoformat(d_str), s))

        person = Person(
            id=p_data["id"],
            platoon=p_data["platoon"],
            points=p_data.get("points", 0),
            role=p_data.get("role", "student"),
            active=p_data.get("active", True),
            day_shifts=p_data.get("day_shifts", 0),
            night_shifts=p_data.get("night_shifts", 0),
            weekend_shifts=p_data.get("weekend_shifts", 0),
            assigned_duties=duties,
            point_history=p_data.get("point_history", [])
        )
        new_people[p_id] = person
    st.session_state.people = new_people

    new_schedule = {}
    for d_str, shifts in data.get("schedule", {}).items():
        new_schedule[datetime.date.fromisoformat(d_str)] = shifts
    st.session_state.schedule = new_schedule


def save_to_disk():
    try:
        content = export_backup_json()
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        st.error(f"Błąd zapisu danych: {e}")


def load_from_disk():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                import_backup_json(f.read())
            return True
        except Exception:
            return False
    return False


# --- INICJALIZACJA STANU ---
if "initialized" not in st.session_state:
    st.session_state.pins = {
        "admin": "9999",
        "pisarka": "5555",
        "pluton_1": "1111",
        "pluton_2": "2222",
        "pluton_3": "3333",
        "pluton_4": "4444"
    }

    people = {}
    for platoon in range(1, 5):
        for nr in range(1, 25):
            p_id = f"{platoon}{nr:02d}"
            people[p_id] = Person(id=p_id, platoon=platoon)
            
    st.session_state.people = people
    st.session_state.objects = ["Jamnik", "Pudel", "Owczarek"]
    st.session_state.schedule = {}
    st.session_state.auth_role = "sluchacz"

    # Wczytaj z pliku data.json jeśli istnieje
    load_from_disk()
    st.session_state.initialized = True


ROLE_LABELS = {
    "admin": "ADMINISTRATOR",
    "pisarka": "PISARKA / GRAFIK",
    "pluton_1": "DOWÓDZTWO PLUTONU 1",
    "pluton_2": "DOWÓDZTWO PLUTONU 2",
    "pluton_3": "DOWÓDZTWO PLUTONU 3",
    "pluton_4": "DOWÓDZTWO PLUTONU 4",
    "sluchacz": "SŁUCHACZ"
}


# --- LOGIKA GENEROWANIA GRAFIKU ---
def generate_schedule(start_date, end_date):
    people = st.session_state.people
    objects = st.session_state.objects
    
    for p in people.values():
        p.day_shifts = 0
        p.night_shifts = 0
        p.weekend_shifts = 0
        p.assigned_duties = set()

    schedule = {}
    current_date = start_date
    next_target_platoon = 1

    while current_date <= end_date:
        is_weekend = current_date.weekday() in (5, 6)
        schedule[current_date] = {"I": {}, "II": {}}
        assigned_today = set()

        for shift_code in ["I", "II"]:
            for obj in objects:
                chosen_person = None
                platoon_order = [((next_target_platoon - 1 + i) % 4) + 1 for i in range(4)]
                
                for target_platoon in platoon_order:
                    eligible = []
                    for p in people.values():
                        if not p.active or p.role == "pisarka" or p.id in assigned_today:
                            continue
                        if p.platoon != target_platoon:
                            continue
                        if (current_date - datetime.timedelta(days=1), "II") in p.assigned_duties and shift_code == "I":
                            continue
                        eligible.append(p)

                    if eligible:
                        eligible.sort(key=lambda x: (
                            x.total_shifts,
                            x.day_shifts if shift_code == "I" else x.night_shifts,
                            x.weekend_shifts if is_weekend else 0
                        ))
                        chosen_person = eligible[0]
                        next_target_platoon = (chosen_person.platoon % 4) + 1
                        break

                if chosen_person:
                    schedule[current_date][shift_code][obj] = chosen_person.id
                    assigned_today.add(chosen_person.id)
                    chosen_person.assigned_duties.add((current_date, shift_code))

                    if shift_code == "I": chosen_person.day_shifts += 1
                    else: chosen_person.night_shifts += 1
                    if is_weekend: chosen_person.weekend_shifts += 1

        current_date += datetime.timedelta(days=1)

    st.session_state.schedule = schedule
    save_to_disk()


# --- SIDEBAR AUTORYZACJI ---
st.sidebar.markdown("<h3 style='color: var(--police-cyan); font-size: 0.85rem; letter-spacing: 1px;'>🛡️ PANEL DOSTĘPU</h3>", unsafe_allow_html=True)

if st.session_state.auth_role == "sluchacz":
    input_pin = st.sidebar.text_input("Wpisz Kod PIN:", type="password")
    if st.sidebar.button("Zaloguj"):
        matched_role = None
        for role_key, pin_val in st.session_state.pins.items():
            if input_pin == pin_val:
                matched_role = role_key
                break
        
        if matched_role:
            st.session_state.auth_role = matched_role
            st.sidebar.success(f"Zalogowano jako {ROLE_LABELS[matched_role]}")
            st.rerun()
        else:
            st.sidebar.error("Błędny kod PIN!")
    st.sidebar.caption("👤 Status: Słuchacz (Tylko odczyt)")
else:
    role_title = ROLE_LABELS.get(st.session_state.auth_role, "UŻYTKOWNIK")
    st.sidebar.success(f"🔑 Zalogowano:\n**{role_title}**")
    if st.sidebar.button("Wyloguj się"):
        st.session_state.auth_role = "sluchacz"
        st.rerun()

st.sidebar.divider()
st.sidebar.caption("✍️ Autor: post. Łukasz Gawin\nSłuchacz CSP Legionowo 2026")


# --- HEADER GŁÓWNY ---
st.markdown("""
<div class="police-header">
    <div class="police-tag">CENTRUM SZKOLENIA POLICJI</div>
    <div class="police-title">Grafik Służb VI Kompanii CSP Legionowo</div>
    <div class="police-subtitle">Zbalansowany System Obsady Posterunków | Rotacja Plutonowa (1 → 2 → 3 → 4)</div>
    <div class="police-author">autor: post. Łukasz Gawin - Słuchacz CSP Legionowo 2026</div>
</div>
""", unsafe_allow_html=True)


# --- METRYKI ---
c1, c2, c3 = st.columns(3)
active_count = sum(1 for p in st.session_state.people.values() if p.active and p.role != "pisarka")
black_list_count = sum(1 for p in st.session_state.people.values() if p.points < 0)

with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Słuchacze w Służbie</div>
        <div class="stat-num">{active_count}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Czarna Lista (Ukarani)</div>
        <div class="stat-num" style="color: var(--badge-gold);">{black_list_count}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Posterunki</div>
        <div class="stat-num">{len(st.session_state.objects)}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# --- KONTROLA TABÓW ---
auth = st.session_state.auth_role
tabs_titles = ["📅 Grafik Służb", "📊 Ewidencja Kompanii", "👤 Kartoteka Słuchacza"]

if auth in ("pluton_1", "pluton_2", "pluton_3", "pluton_4", "admin"):
    tabs_titles.extend(["🚨 Zastępstwa & L4", "⚖️ Czarna Lista / Kary"])

if auth in ("pisarka", "admin"):
    tabs_titles.extend(["🗓️ Generator Grafiku", "💾 Backup & Kopia"])

if auth == "admin":
    tabs_titles.append("⚙️ Panel Admina")

tabs = st.tabs(tabs_titles)
tab_idx = 0


# --- TAB: GRAFIK SŁUŻB ---
with tabs[tab_idx]:
    if not st.session_state.schedule:
        st.info("💡 Grafik nie został jeszcze wygenerowany. Pisarka lub Admin może uruchomić generator.")
    else:
        available_dates = sorted(list(st.session_state.schedule.keys()))
        selected_date = st.selectbox("Wybierz dzień służby:", available_dates, format_func=lambda d: f"{d.strftime('%Y-%m-%d')} ({['Poniedziałek','Wtorek','Środa','Czwartek','Piątek','Sobota','Niedziela'][d.weekday()]})")

        if selected_date:
            day_schedule = st.session_state.schedule[selected_date]
            col_shift1, col_shift2 = st.columns(2)
            
            with col_shift1:
                st.markdown("<h4 style='color: var(--police-cyan); margin-bottom: 15px;'>☀️ I ZMIANA (09:00 - 21:00)</h4>", unsafe_allow_html=True)
                for obj, p_id in day_schedule["I"].items():
                    person = st.session_state.people.get(p_id)
                    p_html = person.status_html if person else ""
                    st.markdown(f"""
                    <div class="duty-card">
                        <div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">POSTERUNEK</div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: #fff;">{obj}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 800; color: var(--police-cyan);">Słuchacz nr {p_id}</div>
                            <div style="margin-top: 4px;">{p_html}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_shift2:
                st.markdown("<h4 style='color: var(--badge-gold); margin-bottom: 15px;'>🌙 II ZMIANA (21:00 - 09:00)</h4>", unsafe_allow_html=True)
                for obj, p_id in day_schedule["II"].items():
                    person = st.session_state.people.get(p_id)
                    p_html = person.status_html if person else ""
                    st.markdown(f"""
                    <div class="duty-card" style="border-left-color: var(--badge-gold);">
                        <div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">POSTERUNEK</div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: #fff;">{obj}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 800; color: var(--badge-gold);">Słuchacz nr {p_id}</div>
                            <div style="margin-top: 4px;">{p_html}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

tab_idx += 1

# --- TAB: EWIDENCJA KOMPANII ---
with tabs[tab_idx]:
    st.subheader("Statystyki Służb i Sumaryczne Punkty")
    all_data = []
    for p in sorted(st.session_state.people.values(), key=lambda x: x.id):
        all_data.append({
            "Nr Słuchacza": p.id,
            "Pluton": f"Pluton {p.platoon}",
            "Rola": p.role.upper(),
            "Służby Dzień (I)": p.day_shifts,
            "Służby Noc (II)": p.night_shifts,
            "Weekendowe": p.weekend_shifts,
            "ŁĄCZNIE SŁUŻB": p.total_shifts,
            "Punkty": p.points
        })

    st.dataframe(pd.DataFrame(all_data), use_container_width=True, hide_index=True)

tab_idx += 1

# --- TAB: KARTOTEKA SŁUCHACZA ---
with tabs[tab_idx]:
    st.subheader("👤 Kartoteka Słuchacza (Imienny Wykaz Służb i Kar)")
    
    student_ids = sorted([p_id for p_id, p in st.session_state.people.items()])
    options = ["-- Wybierz Słuchacza z listy --"] + student_ids
    sel_student_id = st.selectbox("Wybierz Słuchacza do podglądu:", options, index=0)

    if sel_student_id != "-- Wybierz Słuchacza z listy --":
        person = st.session_state.people[sel_student_id]
        
        pk_col1, pk_col2, pk_col3, pk_col4 = st.columns(4)
        pk_col1.metric("Numer Słuchacza", person.id)
        pk_col2.metric("Pluton", f"Pluton {person.platoon}")
        pk_col3.metric("Wyznaczone Służby", f"{person.total_shifts} dyżurów")
        pk_col4.metric("Bilans Punktowy", f"{person.points} pkt")

        st.markdown(f"**Status / Rola:** {person.status_html}", unsafe_allow_html=True)
        st.divider()

        col_k1, col_k2 = st.columns(2)

        with col_k1:
            st.markdown("#### 📅 Wyznaczone Służby w Grafiku")
            student_duties = []
            
            if st.session_state.schedule:
                for d_obj, shifts in sorted(st.session_state.schedule.items()):
                    for shift_code in ["I", "II"]:
                        for obj_name, assigned_p_id in shifts[shift_code].items():
                            if assigned_p_id == person.id:
                                day_name = ["Poniedziałek","Wtorek","Środa","Czwartek","Piątek","Sobota","Niedziela"][d_obj.weekday()]
                                shift_title = "☀️ I Zmiana (09:00 - 21:00)" if shift_code == "I" else "🌙 II Zmiana (21:00 - 09:00)"
                                student_duties.append({
                                    "Data": d_obj.strftime("%Y-%m-%d"),
                                    "Dzień": day_name,
                                    "Zmiana": shift_title,
                                    "Posterunek": obj_name
                                })

            if student_duties:
                st.dataframe(pd.DataFrame(student_duties), use_container_width=True, hide_index=True)
            else:
                st.info("Brak przypisanych służb w aktualnym grafiku.")

        with col_k2:
            st.markdown("#### 📜 Historia Punktów i Kary")
            if person.point_history:
                history_df = pd.DataFrame(person.point_history)
                history_df.columns = ["Data Wpisu", "Zmiana Pkt", "Powód / Uzasadnienie"]
                st.dataframe(history_df, use_container_width=True, hide_index=True)
            else:
                st.success("Brak odnotowanych kar ani wpisów punktowych.")
    else:
        st.info("👈 Wybierz słuchacza z listy powyżej, aby wyświetlić dane kartoteki, służby oraz bilans karny.")

tab_idx += 1


# --- ZASTĘPSTWA & CZARNA LISTA ---
if auth in ("pluton_1", "pluton_2", "pluton_3", "pluton_4", "admin"):
    
    platoon_limit = int(auth.split("_")[1]) if auth.startswith("pluton_") else None

    # TAB: ZASTĘPSTWA & L4
    with tabs[tab_idx]:
        st.subheader("Wyznaczanie Zastępstw i Obsługa L4 / Ochotników")
        if not st.session_state.schedule:
            st.warning("Brak wygenerowanego grafiku do edycji zastępstw.")
        else:
            if platoon_limit:
                st.caption(f"🔒 Dostęp ograniczony: Możesz wybierać zastępców wyłącznie z **Plutonu {platoon_limit}**.")
            else:
                st.caption("🔑 Dostęp Administratora: Możesz wybierać zastępców ze **wszystkich plutonów**.")

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                sel_date = st.selectbox("Data:", sorted(list(st.session_state.schedule.keys())), key="abs_d")
                sel_shift = st.radio("Zmiana:", ["I", "II"], key="abs_s", horizontal=True)
                sel_obj = st.selectbox("Posterunek:", st.session_state.objects, key="abs_o")
                curr_id = st.session_state.schedule[sel_date][sel_shift].get(sel_obj)
                curr_person = st.session_state.people.get(curr_id)
                
                if curr_person:
                    st.info(f"Obecny słuchacz na posterunku: **Słuchacz {curr_id}** (Pluton {curr_person.platoon})")
                else:
                    st.info(f"Obecny słuchacz na posterunku: **Słuchacz {curr_id}**")

            with col_a2:
                filter_candidate_type = st.radio(
                    "Filtruj wolnych słuchaczy:",
                    ["Wszyscy wolni (Czarna Lista + Ochotnicy)", "Tylko z Czarnej Listy (Pkt < 0)"],
                    horizontal=True
                )

                candidates = []
                for p in st.session_state.people.values():
                    if not p.active or p.role == "pisarka": continue
                    if platoon_limit is not None and p.platoon != platoon_limit: continue
                    if filter_candidate_type == "Tylko z Czarnej Listy (Pkt < 0)" and p.points >= 0: continue
                    if any(d == sel_date for d, s in p.assigned_duties): continue
                    if (sel_date - datetime.timedelta(days=1), "II") in p.assigned_duties and sel_shift == "I": continue
                    candidates.append(p)

                candidates.sort(key=lambda x: x.points)
                
                if candidates:
                    rep_opts = {}
                    for p in candidates:
                        status_tag = "🔴 Czarna Lista" if p.points < 0 else "🟢 Ochotnik / Standard"
                        rep_opts[p.id] = f"Słuchacz {p.id} (Pluton {p.platoon} | Pkt: {p.points} | {status_tag})"

                    chosen_rep = st.selectbox("Wybierz zastępcę:", list(rep_opts.keys()), format_func=lambda x: rep_opts[x])
                    is_punishment = st.checkbox("Nalicz punkty za służbę zastępczą (+2 pkt)", value=True)

                    if st.button("Wyznacz Zastępcę", type="primary"):
                        st.session_state.people[curr_id].assigned_duties.discard((sel_date, sel_shift))
                        st.session_state.schedule[sel_date][sel_shift][sel_obj] = chosen_rep
                        st.session_state.people[chosen_rep].assigned_duties.add((sel_date, sel_shift))
                        
                        if is_punishment:
                            today_str = datetime.date.today().strftime("%Y-%m-%d")
                            st.session_state.people[chosen_rep].points += 2
                            st.session_state.people[chosen_rep].point_history.append({
                                "date": today_str,
                                "delta": 2,
                                "reason": f"Zastępstwo / służba na posterunku {sel_obj} ({sel_date})"
                            })
                        
                        save_to_disk()
                        st.success(f"Zastąpiono słuchacza {curr_id} przez {chosen_rep}!")
                        st.rerun()
                else:
                    st.warning("Brak wolnych słuchaczy spełniających wybrane kryteria.")

    tab_idx += 1

    # TAB: CZARNA LISTA / KARY
    with tabs[tab_idx]:
        st.subheader("System Dyscyplinarny i Punkty Kary")
        
        if platoon_limit:
            st.caption(f"🔒 Edycja punktów ograniczona do: **Pluton {platoon_limit}**.")
        else:
            st.caption("🔑 Uprawnienia Admina: Zarządzanie punktacją **wszystkich plutonów**.")

        available_students = [
            p_id for p_id, p in st.session_state.people.items() 
            if p.role != "pisarka" and (platoon_limit is None or p.platoon == platoon_limit)
        ]

        if not available_students:
            st.warning("Brak słuchaczy w Twoim plutonie.")
        else:
            c_p1, c_p2 = st.columns([1, 2])
            with c_p1:
                st.markdown("#### Dodaj / Odejmij Punkty")
                st_id = st.selectbox("Wybierz Słuchacza:", sorted(available_students))
                pts_val = st.number_input("Punkty (+ / -):", value=-2, step=1)
                reason_val = st.text_input("Powód / Uzasadnienie:", "Niewykonywanie poleceń / spóźnienie")
                
                if st.button("Zapisz Punkty"):
                    p_target = st.session_state.people[st_id]
                    p_target.points += pts_val
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    p_target.point_history.append({
                        "date": today_str,
                        "delta": pts_val,
                        "reason": reason_val
                    })
                    save_to_disk()
                    st.success(f"Zaktualizowano punktację dla słuchacza {st_id}!")
                    st.rerun()

            with c_p2:
                st.markdown("#### Aktualna Czarna Lista")
                bl_list = [
                    p for p in st.session_state.people.values() 
                    if p.points < 0 and (platoon_limit is None or p.platoon == platoon_limit)
                ]
                if bl_list:
                    df_bl = pd.DataFrame([{"Nr Słuchacza": p.id, "Pluton": p.platoon, "Punkty Kary": p.points} for p in sorted(bl_list, key=lambda x: x.points)])
                    st.dataframe(df_bl, use_container_width=True, hide_index=True)
                else:
                    st.info("Brak ukaranych słuchaczy w tym zakresie.")

    tab_idx += 1


# --- GENERATOR & BACKUP ---
if auth in ("pisarka", "admin"):

    # TAB: GENERATOR
    with tabs[tab_idx]:
        st.subheader("🗓️ Generator Grafiku Służb")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g_start = st.date_input("Od dnia:", datetime.date(2026, 8, 20))
            g_end = st.date_input("Do dnia:", datetime.date(2026, 9, 20))
            if st.button("Wygeneruj Grafik (Rotacja Plutonów)", type="primary"):
                generate_schedule(g_start, g_end)
                st.success("Nowy grafik został wygenerowany pomyślnie i zapisany!")
                st.rerun()

        with col_g2:
            st.caption("Uruchomienie generatora przeliczy obciążenia słuchaczy i przypisze rotacyjnie plutony 1 → 2 → 3 → 4 do dostępnych posterunków. Osoby o roli **Pisarka** zostaną automatycznie wykluczone.")

    tab_idx += 1

    # TAB: BACKUP
    with tabs[tab_idx]:
        st.subheader("💾 Kopia Zapasowa (Backup JSON)")
        b_col1, b_col2 = st.columns(2)

        with b_col1:
            st.markdown("#### 📤 Pobierz Kopię Zapasową")
            st.caption("Pobiera plik `.json` zawierający pełną konfigurację, grafik, punkty i posterunki.")
            json_data = export_backup_json()
            st.download_button(
                label="Pobierz plik Backup (.json)",
                data=json_data,
                file_name=f"backup_grafik_csp_{datetime.date.today()}.json",
                mime="application/json"
            )

        with b_col2:
            st.markdown("#### 📥 Przywróć Kopię Zapasową")
            uploaded_file = st.file_uploader("Wgraj plik `.json` z kopią:", type=["json"])
            if uploaded_file is not None:
                if st.button("Przywróć dane z pliku", type="primary"):
                    try:
                        content = uploaded_file.read().decode("utf-8")
                        import_backup_json(content)
                        save_to_disk()
                        st.success("Pomyślnie wczytano i zapisano dane z backupu!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd podczas wczytywania pliku: {e}")

    tab_idx += 1


# --- TAB: PANEL ADMINA ---
if auth == "admin":
    with tabs[tab_idx]:
        st.subheader("⚙️ Pełny Panel Administracyjny")
        
        adm_c1, adm_c2 = st.columns(2)

        with adm_c1:
            # 1. POSTERUNKI
            st.markdown("#### 🏢 Obiekty & Posterunki")
            
            new_obj_name = st.text_input("Nazwa nowego posterunku:")
            if st.button("Dodaj Posterunek"):
                if new_obj_name and new_obj_name not in st.session_state.objects:
                    st.session_state.objects.append(new_obj_name)
                    save_to_disk()
                    st.success(f"Dodano posterunek: {new_obj_name}")
                    st.rerun()

            st.write("")
            if st.session_state.objects:
                obj_to_edit = st.selectbox("Wybierz posterunek do zmiany/usunięcia:", st.session_state.objects)
                renamed_obj = st.text_input("Nowa nazwa dla posterunku:", value=obj_to_edit)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Zmień nazwę"):
                        idx = st.session_state.objects.index(obj_to_edit)
                        st.session_state.objects[idx] = renamed_obj
                        save_to_disk()
                        st.success("Zmieniono nazwę posterunku!")
                        st.rerun()
                with col_btn2:
                    if st.button("❌ Usuń posterunek"):
                        st.session_state.objects.remove(obj_to_edit)
                        save_to_disk()
                        st.success("Usunięto posterunek!")
                        st.rerun()

            st.divider()

            # 2. ROLE
            st.markdown("#### 👤 Mianowanie Ról w Kompanii")
            target_p_id = st.selectbox("Wybierz osobę z kompanii:", sorted(list(st.session_state.people.keys())))
            target_person = st.session_state.people[target_p_id]
            
            role_options = {"student": "Słuchacz", "pisarka": "Pisarka", "dowodca": "Dowódca"}
            rev_role_options = {"Słuchacz": "student", "Pisarka": "pisarka", "Dowódca": "dowodca"}
            
            current_role_key = target_person.role if target_person.role in role_options else "student"
            current_role_label = role_options[current_role_key]
            
            new_role_choice = st.radio(
                "Przypisz Rolę:",
                ["Słuchacz", "Pisarka", "Dowódca"],
                index=["Słuchacz", "Pisarka", "Dowódca"].index(current_role_label)
            )

            if st.button("Zapisz Rolę Osoby"):
                target_person.role = rev_role_options[new_role_choice]
                save_to_disk()
                st.success(f"Zmieniono rolę dla słuchacza {target_p_id} na: **{new_role_choice}**")
                st.rerun()

        with adm_c2:
            # 3. KODY PIN
            st.markdown("#### 🔑 Kody PIN (Konta Dostępowe)")
            st.caption("Zmiana kodów PIN dla ról administracyjnych i dowódczych:")
            
            updated_pins = {}
            for r_key, r_label in ROLE_LABELS.items():
                if r_key == "sluchacz": continue
                updated_pins[r_key] = st.text_input(f"PIN ({r_label}):", value=st.session_state.pins.get(r_key, ""), type="password", key=f"pin_{r_key}")

            if st.button("Zapisz Kody PIN"):
                st.session_state.pins.update(updated_pins)
                save_to_disk()
                st.success("Zaktualizowano kody PIN dla wszystkich kont!")
                st.rerun()

            st.divider()
            st.markdown("#### ⚠️ Reset Systemu")
            if st.button("Wyczyszczenie Grafiku do Zera"):
                st.session_state.schedule = {}
                save_to_disk()
                st.warning("Grafik został zresetowany.")
                st.rerun()
