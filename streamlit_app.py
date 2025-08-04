import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="centered")
st.title("Plansza Spectrum")

# Ustawienie stanu strony
if "screen" not in st.session_state:
    st.session_state.screen = "tarcza"
if "slider_val" not in st.session_state:
    st.session_state.slider_val = 0
if "promien_val" not in st.session_state:
    st.session_state.promien_val = 0
if "punktacja" not in st.session_state:
    st.session_state.punktacja = None

# Stałe
total_width = 25
half_width = total_width / 2
center_base = 90

colors = {
    "2": "#FFDAB5",
    "3": "#ADD8E6",
    "4": "#3399FF",
    "tlo": "#F5F5DC",
    "promien": "red"
}

def draw_sector(ax, center_angle, width, color):
    theta1 = center_angle - width / 2
    theta2 = center_angle + width / 2
    theta1_clip = max(theta1, 0)
    theta2_clip = min(theta2, 180)
    if theta1_clip >= theta2_clip:
        return
    theta = np.linspace(theta1_clip, theta2_clip, 100)
    x = np.cos(np.deg2rad(theta))
    y = np.sin(np.deg2rad(theta))
    x = np.append(x, 0)
    y = np.append(y, 0)
    ax.fill(x, y, color=color, alpha=1)

def draw_circle_with_promien(promien_angle_deg):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    # Tło półkola
    theta_bg = np.linspace(0, 180, 300)
    x_bg = np.cos(np.deg2rad(theta_bg))
    y_bg = np.sin(np.deg2rad(theta_bg))
    ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])
    # Czerwony promień
    rad = np.deg2rad(promien_angle_deg)
    x_end = np.cos(rad)
    y_end = np.sin(rad)
    ax.plot([0, x_end], [0, y_end], color=colors["promien"], linewidth=3)
    return fig

def draw_circle_with_punktacja_and_promien(punktacja_slider_val, promien_slider_val):
    shift = 90 + (punktacja_slider_val + 100) * (-175) / 200
    promien_angle = 90 - promien_slider_val / 100 * 90

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_aspect('equal')
    ax.axis('off')

    # Tło półkola
    theta_bg = np.linspace(0, 180, 300)
    x_bg = np.cos(np.deg2rad(theta_bg))
    y_bg = np.sin(np.deg2rad(theta_bg))
    ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])

    # Punktacja
    segment_sequence = [("2", colors["2"]), ("3", colors["3"]), ("4", colors["4"]), ("3", colors["3"]), ("2", colors["2"])]
    start_angle = center_base - half_width + shift
    for i, (label, color) in enumerate(segment_sequence):
        angle = start_angle + i * 5
        draw_sector(ax, angle, 5, color)

    # Promień
    rad = np.deg2rad(promien_angle)
    x_end = np.cos(rad)
    y_end = np.sin(rad)
    ax.plot([0, x_end], [0, y_end], color=colors["promien"], linewidth=1)

    return fig

if st.session_state.screen == "tarcza":
    st.markdown("### Ustaw punktację")
    st.session_state.slider_val = st.slider("Przesuń tarczę", -100, 100, st.session_state.slider_val, label_visibility="collapsed")
    shift = 90 + (st.session_state.slider_val + 100) * (-175) / 200

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_aspect('equal')
    ax.axis('off')
    theta_bg = np.linspace(0, 180, 300)
    x_bg = np.cos(np.deg2rad(theta_bg))
    y_bg = np.sin(np.deg2rad(theta_bg))
    ax.fill(np.append(x_bg, 0), np.append(y_bg, 0), color=colors["tlo"])

    segment_sequence = [("2", colors["2"]), ("3", colors["3"]), ("4", colors["4"]), ("3", colors["3"]), ("2", colors["2"])]
    start_angle = center_base - half_width + shift
    for i, (label, color) in enumerate(segment_sequence):
        angle = start_angle + i * 5
        draw_sector(ax, angle, 5, color)

    st.pyplot(fig)

    
    def przejdz_do_promienia():
        st.session_state.screen = "promien"
        st.session_state.promien_val = 0
        st.session_state.punktacja = st.session_state.slider_val

    st.button("Zatwierdź", on_click=przejdz_do_promienia)


elif st.session_state.screen == "promien":
    st.markdown("### Wskaż odpowiedź")
    st.session_state.promien_val = st.slider("Ustaw promień", -100, 100, st.session_state.promien_val, label_visibility="collapsed")
    shift_promien = 90 - st.session_state.promien_val / 100 * 90
    st.pyplot(draw_circle_with_promien(shift_promien))

    col1, col2 = st.columns(2)

    def przejdz_do_wyniku():
        st.session_state.screen = "wynik"
    
    def powrot_do_tarczy():
        st.session_state.screen = "tarcza"

    with col1:
        st.button("Powrót", on_click=powrot_do_tarczy)
    with col2:
        st.button("Zatwierdź", on_click=przejdz_do_wyniku)

elif st.session_state.screen == "wynik":
    st.markdown("### Wynik rundy")
    st.pyplot(draw_circle_with_punktacja_and_promien(st.session_state.punktacja, st.session_state.promien_val))

    def nowa_runda():
        st.session_state.screen = "tarcza"
        st.session_state.slider_val = 0
        st.session_state.promien_val = 0
        st.session_state.punktacja = None

    st.button("Kolejna runda", on_click=nowa_runda)


# git pull origin main --rebase
# git add .
# git commit -m ""
# git push
