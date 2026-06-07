import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Simulador TFG - H2REGRID", layout="wide")

st.title("Microrred Híbrida: Control por Banda de Histéresis")
st.markdown("**Trabajo Fin de Grado** | Autor: José Antonio Carreño Ramírez")
st.markdown("Simulación interactiva del lazo de control de corriente para el inversor de acoplamiento a red.")

# --- INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
# Inicializamos las variables de los componentes por separado
if "L_slider" not in st.session_state: st.session_state.L_slider = 1.0
if "L_num" not in st.session_state: st.session_state.L_num = 1.0

if "banda_slider" not in st.session_state: st.session_state.banda_slider = 4.0
if "banda_num" not in st.session_state: st.session_state.banda_num = 4.0

if "P_slider" not in st.session_state: st.session_state.P_slider = 50.0
if "P_num" not in st.session_state: st.session_state.P_num = 50.0

# --- FUNCIONES DE SINCRONIZACIÓN (CALLBACKS) ---
# Si muevo la barra, actualizo la caja. Si escribo en la caja, actualizo la barra.
def sync_L_from_slider(): st.session_state.L_num = st.session_state.L_slider
def sync_L_from_num(): st.session_state.L_slider = st.session_state.L_num

def sync_banda_from_slider(): st.session_state.banda_num = st.session_state.banda_slider
def sync_banda_from_num(): st.session_state.banda_slider = st.session_state.banda_num

def sync_P_from_slider(): st.session_state.P_num = st.session_state.P_slider
def sync_P_from_num(): st.session_state.P_slider = st.session_state.P_num

# --- BARRA LATERAL: CONTROLES INTERACTIVOS ENLAZADOS ---
st.sidebar.header("Parámetros del Sistema")

# 1. Inductancia (L)
st.sidebar.markdown("**Inductancia del Filtro (mH)**")
col1a, col1b = st.sidebar.columns([3, 1])
with col1a:
    st.slider("L_slider", 0.1, 50.0, key="L_slider", on_change=sync_L_from_slider, label_visibility="collapsed")
with col1b:
    st.number_input("L_num", 0.1, 50.0, key="L_num", on_change=sync_L_from_num, format="%.2f", label_visibility="collapsed")

# 2. Banda de Histéresis
st.sidebar.markdown("**Banda de Histéresis (A)**")
col2a, col2b = st.sidebar.columns([3, 1])
with col2a:
    st.slider("banda_slider", 0.1, 20.0, key="banda_slider", on_change=sync_banda_from_slider, label_visibility="collapsed")
with col2b:
    st.number_input("banda_num", 0.1, 20.0, key="banda_num", on_change=sync_banda_from_num, format="%.2f", label_visibility="collapsed")

# 3. Potencia Activa
st.sidebar.markdown("**Potencia Activa Inyectada (kW)**")
col3a, col3b = st.sidebar.columns([3, 1])
with col3a:
    st.slider("P_slider", 1.0, 100.0, key="P_slider", on_change=sync_P_from_slider, label_visibility="collapsed")
with col3b:
    st.number_input("P_num", 1.0, 100.0, key="P_num", on_change=sync_P_from_num, format="%.1f", label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.info("El simulador resuelve la ecuación diferencial del filtro inductivo con un paso de 10 µs, emulando un DSP físico.")

# Asignamos los valores finales para el motor matemático
L_mH = st.session_state.L_num
banda_A = st.session_state.banda_num
P_ref_kW = st.session_state.P_num

# --- MOTOR DE SIMULACIÓN MATEMÁTICA ---
f = 50.0
w = 2 * np.pi * f
V_rms = 230.0
V_red_peak = V_rms * np.sqrt(2)
V_dc = 400.0
dt = 1e-5  
t = np.arange(0, 0.04, dt) 

L = L_mH * 1e-3  
I_rms = (P_ref_kW * 1000) / V_rms
I_ref_peak = I_rms * np.sqrt(2)

v_red = V_red_peak * np.sin(w * t)
i_ref = I_ref_peak * np.sin(w * t)

i_meas = np.zeros_like(t)
v_inv = np.zeros_like(t)
estado_inv = V_dc

for k in range(1, len(t)):
    error = i_meas[k-1] - i_ref[k-1]
    if error > banda_A:
        estado_inv = -V_dc
    elif error < -banda_A:
        estado_inv = V_dc
        
    v_inv[k] = estado_inv
    di = ((v_inv[k] - v_red[k]) / L) * dt
    i_meas[k] = i_meas[k-1] + di

# --- VISUALIZACIÓN GRÁFICA (MATPLOTLIB) ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
plt.subplots_adjust(hspace=0.3)

ax1.plot(t * 1000, v_red, color='#2ca02c', linewidth=2, label='Tensión de Red (Bus Infinito)')
ax1.plot(t * 1000, v_inv, color='#1f77b4', alpha=0.7, label='Tensión de Salida del Inversor')
ax1.set_title('Tensiones del Sistema', fontsize=14)
ax1.set_ylabel('Voltaje (V)', fontsize=12)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

ax2.plot(t * 1000, i_ref, color='black', linestyle='--', linewidth=2, label='Corriente de Referencia (P_ref)')
ax2.plot(t * 1000, i_meas, color='#d62728', linewidth=1.5, label='Corriente Real Inyectada')
ax2.plot(t * 1000, i_ref + banda_A, color='gray', linestyle=':', alpha=0.5)
ax2.plot(t * 1000, i_ref - banda_A, color='gray', linestyle=':', alpha=0.5)

ax2.set_title('Dinámica de Corriente y Banda de Histéresis', fontsize=14)
ax2.set_xlabel('Tiempo (ms)', fontsize=12)
ax2.set_ylabel('Corriente (A)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

st.pyplot(fig)
