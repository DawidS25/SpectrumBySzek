import streamlit as st
import random
import pandas as pd
import io
import base64
import requests
from datetime import datetime

# --------- Wczytanie pytań i przygotowanie słowników ---------
@st.cache_data
def load_questions():
    df = pd.read_csv('questions.csv', sep=';')
    def filter_by_category(cat):
        return df[df['categories'] == cat].to_dict(orient='records')

    categories = {
        "Śmieszne": filter_by_category('Śmieszne'),
        "Światopoglądowe": filter_by_category('Światopoglądowe'),
        "Związkowe": filter_by_category('Związkowe'),
        "Pikantne": filter_by_category('Pikantne'),
        "Luźne": filter_by_category('Luźne'),
        "Przeszłość": filter_by_category('Przeszłość'),
        "Wolisz": filter_by_category('Wolisz'),
        "Dylematy": filter_by_category('Dylematy'),
    }

    emojis = {
        "Śmieszne": "😂",
        "Światopoglądowe": "🌍",
        "Związkowe": "❤️",
        "Pikantne": "🌶️",
        "Luźne": "😎",
        "Przeszłość": "📜",
        "Wolisz": "🤔",
        "Dylematy": "⚖️"
    }

    return categories, emojis

# --------- Inicjalizacja session_state ---------
def initialize_session_state(defaults):
    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, set):
                st.session_state[key] = value.copy()
            elif isinstance(value, list):
                st.session_state[key] = value[:]
            else:
                st.session_state[key] = value

# --------- Losowanie pytania ---------
def draw_question(chosen_categories, used_ids, CATEGORIES):
    all_qs = []
    for cat in chosen_categories:
        all_qs.extend(CATEGORIES[cat])
    available = [q for q in all_qs if q["id"] not in used_ids]
    if not available:
        return None
    question = random.choice(available)
    used_ids.add(question["id"])
    return question

# --------- Ekran setup (wprowadzanie graczy) ---------
def setup_screen(defaults):
    st.title("🎲 Spectrum")
    st.markdown("<div style='margin-top: -20px; font-size: 10px; color: gray;'>made by Szek</div>", unsafe_allow_html=True)
    st.header("🎭 Wprowadź imiona graczy")

    player_names = []
    for i in range(2):
        name = st.text_input(f"🙋‍♂️ Gracz {i + 1}", value=st.session_state.players[i])
        player_names.append(name.strip())

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🔙 Powrót do wyboru trybu"):
            # wyczyść sesję trybu dwuosobowego
            for key in defaults.keys():
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.step = "mode_select"
            st.rerun()
    with col2:
        if all(player_names) and st.button("✅ Dalej"):
            st.session_state.players = player_names
            st.session_state.all_players = player_names.copy()
            st.session_state.scores = {name: 0 for name in player_names}
            st.session_state.results_data = []
            st.session_state.step = "categories"
            st.rerun()

# --------- Ekran wyboru kategorii ---------
def categories_screen(CATEGORIES, CATEGORY_EMOJIS):
    st.header("📚 Wybierz kategorie pytań")

    if "category_selection" not in st.session_state:
        st.session_state.category_selection = set()

    cols = st.columns(4)
    for i, cat in enumerate(CATEGORIES.keys()):
        col = cols[i % 4]
        display_name = f"{CATEGORY_EMOJIS.get(cat, '')} {cat}"
        if cat in st.session_state.category_selection:
            if col.button(f"✅ {display_name}", key=f"cat_{cat}"):
                st.session_state.category_selection.remove(cat)
                st.rerun()
        else:
            if col.button(display_name, key=f"cat_{cat}"):
                st.session_state.category_selection.add(cat)
                st.rerun()

    selected_display = [f"{CATEGORY_EMOJIS.get(cat, '')} {cat}" for cat in st.session_state.category_selection]
    st.markdown(f"**Wybrane kategorie:** {', '.join(selected_display) or 'Brak'}")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🔙 Powrót"):
            if "category_selection" in st.session_state:
                del st.session_state["category_selection"]
            st.session_state.step = "setup"
            st.rerun()
    with col2:
        if st.session_state.category_selection and st.button("🎯 Rozpocznij grę"):
            st.session_state.chosen_categories = list(st.session_state.category_selection)
            st.session_state.step = "game"
            st.rerun()

# --------- Ekran gry ---------
def game_screen(CATEGORIES):
    # Ustawienie domyślnych danych
    if "scores" not in st.session_state:
        st.session_state.scores = {}
    if "all_players" not in st.session_state:
        st.session_state.all_players = st.session_state.players.copy()
    for player in st.session_state.all_players:
        if player not in st.session_state.scores:
            st.session_state.scores[player] = 0

    turn = st.session_state.questions_asked % 2
    responder = st.session_state.all_players[turn]
    guesser = st.session_state.all_players[1 - turn]

    if st.session_state.ask_continue:
        st.header("❓ Czy chcesz kontynuować grę?")
        rounds_played = st.session_state.questions_asked // 2
        total_questions = st.session_state.questions_asked
        st.write(f"🥊 Rozegrane rundy: {rounds_played} → {total_questions} pytań 🧠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Tak, kontynuuj"):
                st.session_state.ask_continue = False
                st.session_state.current_question = draw_question(st.session_state.chosen_categories, st.session_state.used_ids, CATEGORIES)
                st.rerun()
        with col2:
            if st.button("❌ Zakończ i pokaż wyniki"):
                st.session_state.step = "end"
                st.rerun()
    else:
        if not st.session_state.current_question:
            st.session_state.current_question = draw_question(st.session_state.chosen_categories, st.session_state.used_ids, CATEGORIES)
            if not st.session_state.current_question:
                st.success("🎉 Pytania się skończyły! Gratulacje.")
                st.session_state.step = "end"
                st.rerun()

        q = st.session_state.current_question
        current_round = (st.session_state.questions_asked // 2) + 1
        current_question_number = st.session_state.questions_asked + 1

        st.markdown(f"### 🥊 Runda {current_round}")
        st.markdown("<div style='margin-top: -20px; font-size: 10px; color: gray;'>Spectrum - made by Szek</div>", unsafe_allow_html=True)
        st.subheader(f"🧠 Pytanie {current_question_number} – kategoria: *{q['categories']}*")
        st.write(q["text"])
        st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)

        if st.button("🔄 Zmień pytanie"):
            new_q = draw_question(st.session_state.chosen_categories, st.session_state.used_ids, CATEGORIES)
            if new_q:
                st.session_state.current_question = new_q
            st.rerun()

        st.markdown(f"Odpowiada: **{responder}** &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Zgaduje: **{guesser}**", unsafe_allow_html=True)

        st.markdown(f"**Ile punktów zdobywa {guesser}?**")
        if "guesser_points" not in st.session_state:
            st.session_state.guesser_points = None

        cols = st.columns(4)
        for i, val in enumerate([0, 2, 3, 4]):
            label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
            if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
                st.session_state.guesser_points = val
                st.rerun()

        if st.session_state.guesser_points is not None:
            if st.button("💾 Zapisz i dalej"):
                guesser_points = st.session_state.guesser_points
                st.session_state.guesser_points = None

                if guesser_points == 0:
                    responder_points = 0
                elif guesser_points in [2,3]:
                    responder_points = 1
                elif guesser_points == 4:
                    responder_points = 2
                else:
                    responder_points = 0

                st.session_state.scores[guesser] += guesser_points
                st.session_state.scores[responder] += responder_points

                points_this_round = {
                    responder: responder_points,
                    guesser: guesser_points,
                }

                if "results_data" not in st.session_state:
                    st.session_state.results_data = []

                data_to_save = {
                    "r_pytania": current_question_number,
                    "kategoria": q['categories'],
                    "pytanie": q['text'],
                    "odpowiada": responder,
                    "zgaduje": guesser,
                    responder: points_this_round[responder],
                    guesser: points_this_round[guesser],
                }
                st.session_state.results_data.append(data_to_save)

                st.session_state.questions_asked += 1

                if st.session_state.questions_asked % 2 == 0:
                    st.session_state.ask_continue = True
                    st.session_state.current_question = None
                else:
                    st.session_state.current_question = draw_question(st.session_state.chosen_categories, st.session_state.used_ids, CATEGORIES)

                st.rerun()

# --------- Ekran wyników ---------
def end_screen(defaults):
    total_questions = st.session_state.questions_asked
    total_rounds = total_questions // 2
    st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    medals = ["🏆", "🥈", "🥉"]
    for i, (name, score) in enumerate(sorted_scores):
        medal = medals[i] if i < 3 else ""
        st.write(f"{medal} **{name}:** {score} punktów")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔁 Jeszcze nie kończymy!"):
            st.session_state.ask_continue = False
            st.session_state.current_question = draw_question(st.session_state.chosen_categories, st.session_state.used_ids, st.session_state.CATEGORIES)
            st.session_state.step = "game"
            st.rerun()
    with col2:
        if st.button("🎮 Zagraj ponownie"):
            for key, value in defaults.items():
                if isinstance(value, set):
                    st.session_state[key] = value.copy()
                elif isinstance(value, list):
                    st.session_state[key] = value[:]
                else:
                    st.session_state[key] = value
            # Czyść ewentualne dodatkowe klucze
            for key in ["all_players", "category_selection", "results_uploaded"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # --- Pobieranie wyników jako Excel ---
    if "results_data" in st.session_state and st.session_state.results_data:

        if "results_uploaded" not in st.session_state:
            st.session_state.results_uploaded = False

        df_results = pd.DataFrame(st.session_state.results_data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_results.to_excel(writer, index=False, sheet_name='Wyniki')
        data = output.getvalue()

        st.download_button(
            label="💾 Pobierz wyniki gry (XLSX)",
            data=data,
            file_name="wyniki_gry.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- Upload na GitHub ---
        if not st.session_state.results_uploaded:
            temp_filename = "wyniki_temp.xlsx"
            with open(temp_filename, "wb") as f:
                f.write(data)

            repo = "DawidS25/SpectrumBySzek"  # zmień na swoje repo
            try:
                token = st.secrets["GITHUB_TOKEN"]
            except Exception:
                token = None

            if token:
                next_num = get_next_game_number(repo, token)
                today_str = datetime.today().strftime("%Y-%m-%d")
                file_name = f"gra{next_num:03d}_{today_str}.xlsx"
                path_in_repo = f"wyniki/{file_name}"
                commit_message = f"🎉 Wyniki gry {file_name}"

                response = upload_to_github(temp_filename, repo, path_in_repo, token, commit_message)
                if response.status_code == 201:
                    st.success(f"✅ Wyniki zapisane online.")
                    st.session_state.results_uploaded = True
                else:
                    st.error(f"❌ Błąd zapisu: {response.status_code} – {response.json()}")
            else:
                st.warning("⚠️ Nie udało się zapisać wyników online.")

# --------- Funkcje uploadu (można potem przenieść) ---------
def upload_to_github(file_path, repo, path_in_repo, token, commit_message):
    with open(file_path, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": "main"
    }

    response = requests.put(url, headers=headers, json=data)
    return response

def get_next_game_number(repo, token, folder="wyniki"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 1

    files = response.json()
    today_str = datetime.today().strftime("%Y-%m-%d")
    max_num = 0
    for file in files:
        name = file["name"]
        if name.startswith("gra") and name.endswith(".xlsx") and today_str in name:
            try:
                num_part = name[3:6]
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except:
                pass
    return max_num + 1

# --------- Główna funkcja uruchamiająca tryb ---------
def run():
    CATEGORIES, CATEGORY_EMOJIS = load_questions()

    defaults = {
        "players": ["", ""],
        "chosen_categories": [],
        "used_ids": set(),
        "current_question": None,
        "scores": {},
        "step": "setup",
        "questions_asked": 0,
        "ask_continue": False,
        "guesser_points": None,
        "results_data": []
    }

    initialize_session_state(defaults)

    # Aby łatwo przekazywać do innych funkcji
    st.session_state.CATEGORIES = CATEGORIES
    st.session_state.CATEGORY_EMOJIS = CATEGORY_EMOJIS

    if st.session_state.step == "setup":
        setup_screen(defaults)
    elif st.session_state.step == "categories":
        categories_screen(CATEGORIES, CATEGORY_EMOJIS)
    elif st.session_state.step == "game":
        game_screen(CATEGORIES)
    elif st.session_state.step == "end":
        end_screen(defaults)
