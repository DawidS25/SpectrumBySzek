import streamlit as st
import random
import pandas as pd
import os
import io
import base64
import requests
from datetime import datetime

# ------------------------------
# PYTANIA
# ------------------------------
df = pd.read_csv('questions.csv', sep=';')

def filter_by_category(cat):
    return df[df['categories'] == cat].to_dict(orient='records')

funny_questions = filter_by_category('Śmieszne')
worldview_questions = filter_by_category('Światopoglądowe')
relationship_questions = filter_by_category('Związkowe')
spicy_questions = filter_by_category('Pikantne')
casual_questions = filter_by_category('Luźne')
past_questions = filter_by_category('Przeszłość')
would_you_rather_questions = filter_by_category('Wolisz')
dylema_questions = filter_by_category('Dylematy')

CATEGORIES = {
    "Śmieszne": funny_questions,
    "Światopoglądowe": worldview_questions,
    "Związkowe": relationship_questions,
    "Pikantne": spicy_questions,
    "Luźne": casual_questions,
    "Przeszłość": past_questions,
    "Wolisz": would_you_rather_questions,
    "Dylematy": dylema_questions
}

CATEGORY_EMOJIS = {
    "Śmieszne": "😂",
    "Światopoglądowe": "🌍",
    "Związkowe": "❤️",
    "Pikantne": "🌶️",
    "Luźne": "😎",
    "Przeszłość": "📜",
    "Wolisz": "🤔",
    "Dylematy": "⚖️"
}

# ------------------------------
# SESJA
# ------------------------------
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

for key, value in defaults.items():
    if key not in st.session_state:
        if isinstance(value, set):
            st.session_state[key] = value.copy()
        elif isinstance(value, list):
            st.session_state[key] = value[:]
        else:
            st.session_state[key] = value

# ------------------------------
# FUNKCJA LOSUJĄCA PYTANIA
# ------------------------------
def draw_question():
    all_qs = []
    for cat in st.session_state.chosen_categories:
        all_qs.extend(CATEGORIES[cat])
    available = [q for q in all_qs if q["id"] not in st.session_state.used_ids]
    if not available:
        return None
    question = random.choice(available)
    st.session_state.used_ids.add(question["id"])
    return question

# ------------------------------
# UPLOAD DO GITHUB 
# ------------------------------

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

# ------------------------------
# INTERFEJS
# ------------------------------
if st.session_state.step in ["setup", "categories", "end"]:
    st.title("🎲 Spectrum")

if st.session_state.step == "setup":
    st.header("🎭 Wprowadź imiona graczy")

    player_names = []
    for i in range(2):
        name = st.text_input(f"🙋‍♂️ Gracz {i + 1}", value=st.session_state.players[i])
        player_names.append(name.strip())

    if all(player_names):
        if st.button("✅ Dalej"):
            st.session_state.players = player_names
            st.session_state.all_players = player_names.copy()
            st.session_state.scores = {name: 0 for name in player_names}
            st.session_state.results_data = []
            st.session_state.step = "categories"
            st.rerun()

elif st.session_state.step == "categories":
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

    if st.session_state.category_selection:
        if st.button("🎯 Rozpocznij grę"):
            st.session_state.chosen_categories = list(st.session_state.category_selection)
            st.session_state.step = "game"
            st.rerun()

elif st.session_state.step == "game":
    # Zapewnij domyślne wartości
    if "scores" not in st.session_state:
        st.session_state.scores = {}
    if "all_players" not in st.session_state:
        st.session_state.all_players = st.session_state.players.copy()
    for player in st.session_state.all_players:
        if player not in st.session_state.scores:
            st.session_state.scores[player] = 0

    # Na zmianę responder i guesser: tura 0 => p1 odpowiada, p2 zgaduje; tura 1 => p2 odpowiada, p1 zgaduje itd.
    turn = st.session_state.questions_asked % 2
    if turn == 0:
        responder = st.session_state.all_players[0]
        guesser = st.session_state.all_players[1]
    else:
        responder = st.session_state.all_players[1]
        guesser = st.session_state.all_players[0]

    if st.session_state.ask_continue:
        st.header("❓ Czy chcesz kontynuować grę?")
        rounds_played = st.session_state.questions_asked // 2
        total_questions = st.session_state.questions_asked
        st.write(f"🥊 Rozegrane rundy: {rounds_played} -> {total_questions} pytań 🧠")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Tak, kontynuuj"):
                st.session_state.ask_continue = False
                st.session_state.current_question = draw_question()
                st.rerun()
        with col2:
            if st.button("❌ Zakończ i pokaż wyniki"):
                st.session_state.step = "end"
                st.rerun()
    else:
        if not st.session_state.current_question:
            st.session_state.current_question = draw_question()
            if not st.session_state.current_question:
                st.success("🎉 Pytania się skończyły! Gratulacje.")
                st.session_state.step = "end"
                st.rerun()

        q = st.session_state.current_question
        current_round = (st.session_state.questions_asked // 2) + 1
        current_question_number = st.session_state.questions_asked + 1

        st.markdown(f"### 🥊 Runda {current_round}")
        st.subheader(f"🧠 Pytanie {current_question_number} – kategoria: *{q['categories']}*")
        st.write(q["text"])
        st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)

        if st.button("🔄 Zmień pytanie"):
            new_q = draw_question()
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

        # Usunięte dodatkowe punkty i osoba trzecia - już nie ma extra_point ani direction_guesser

        if st.session_state.guesser_points is not None:
            if st.button("💾 Zapisz i dalej"):
                guesser_points = st.session_state.guesser_points

                # Reset wyborów
                st.session_state.guesser_points = None

                # Liczenie punktów dla respondera według zasad:
                if guesser_points == 0:
                    responder_points = 0
                elif guesser_points in [2, 3]:
                    responder_points = 1
                elif guesser_points == 4:
                    responder_points = 2
                else:
                    responder_points = 0  # Bezpieczna wartość na wypadek błędu

                # Aktualizacja wyników
                st.session_state.scores[guesser] += guesser_points
                st.session_state.scores[responder] += responder_points

                points_this_round = {
                    responder: responder_points,
                    guesser: guesser_points,
                }

                # Dopisywanie wyników do pamięci
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

                # Po 2 pytaniach pokazujemy pytanie czy kontynuować
                if st.session_state.questions_asked % 2 == 0:
                    st.session_state.ask_continue = True
                    st.session_state.current_question = None
                else:
                    st.session_state.current_question = draw_question()

                st.rerun()

elif st.session_state.step == "end":
    total_questions = st.session_state.questions_asked
    total_rounds = total_questions // 2  # 2 pytania na rundę w trybie 2 graczy
    st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1], reverse=True)
    medale = ["🏆", "🥈", "🥉"]
    for i, (name, score) in enumerate(sorted_scores):
        medal = medale[i] if i < 3 else ""
        st.write(f"{medal} **{name}:** {score} punktów")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔁 Jeszcze nie kończymy!"):
            st.session_state.ask_continue = False
            st.session_state.current_question = draw_question()
            st.session_state.step = "game"
            st.rerun()

    with col2:
        if st.button("🎮 Zagraj ponownie"):
            # Resetowanie stanu do domyślnych wartości
            for key, value in defaults.items():
                if isinstance(value, set):
                    st.session_state[key] = value.copy()
                elif isinstance(value, list):
                    st.session_state[key] = value[:]
                else:
                    st.session_state[key] = value
            if "all_players" in st.session_state:
                del st.session_state["all_players"]
            if "category_selection" in st.session_state:
                del st.session_state["category_selection"]
            if "results_uploaded" in st.session_state:
                del st.session_state["results_uploaded"]
            st.rerun()

    # --- Generowanie pliku Excel z wyników w pamięci ---
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

        # --- Upload na GitHub tylko raz ---
        if not st.session_state.results_uploaded:
            temp_filename = "wyniki_temp.xlsx"
            with open(temp_filename, "wb") as f:
                f.write(data)

            repo = "DawidS25/SpectrumDual"  # zmień na swoje repo
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

# git pull origin main --rebase
# git add .
# git commit -m ""
# git push