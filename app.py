import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Simulador TFG - H2REGRID", layout="wide")

st.title("Microrred Híbrida: Control por Banda de Histéresis")
st.markdown("**Trabajo Fin de Grado** | Autor: José Antonio Carreño Ramírez")
st.markdown("Simulación interactiva del lazo de control de corriente para el inversor de acoplamiento a red.")

# --- BARRA LATERAL: CONTROLES INTERACTIVOS ---
st.sidebar.header("Parámetros del Sistema")
st.sidebar.markdown("Escribe el valor exacto o usa las flechas:")

# Usamos number_input en lugar de slider para permitir escritura exacta
L_mH = st.sidebar.number_input("Inductancia del Filtro (mH)", 
                               min_value=0.1, 
                               max_value=50.0, 
                               value=1.0,  # Valor por defecto: 1 mH (1e-3 H)
                               step=0.1, 
                               format="%.2f")

banda_A = st.sidebar.number_input("Banda de Histéresis (A)", 
                                  min_value=0.1, 
                                  max_value=20.0, 
                                  value=4.0, 
                                  step=0.1, 
                                  format="%.2f")

P_ref_kW = st.sidebar.number_input("Potencia Activa Inyectada (kW)", 
                                   min_value=1.0, 
                                   max_value=100.0, 
                                   value=50.0, 
                                   step=1.0, 
                                   format="%.1f")

st.sidebar.markdown("---")
st.sidebar.info("El simulador resuelve paso a paso la ecuación diferencial de la inductancia, emulando el tiempo de muestreo (10 µs) de un DSP físico.")

# --- MOTOR DE SIMULACIÓN MATEMÁTICA ---
# Parámetros fijos
f = 50.0
w = 2 * np.pi * f
V_rms = 230.0
V_red_peak = V_rms * np.sqrt(2)
V_dc = 400.0
dt = 1e-5  # 10 microsegundos
t = np.arange(0, 0.04, dt)  # 40 milisegundos (2 ciclos de red)

# Cálculos intermedios
L = L_mH * 1e-3  # Convierte los mH ingresados a Henrios para la ecuación
I_rms = (P_ref_kW * 1000) / V_rms
I_ref_peak = I_rms * np.sqrt(2)

# Señales de referencia
v_red = V_red_peak * np.sin(w * t)
i_ref = I_ref_peak * np.sin(w * t)

# Vectores de almacenamiento
i_meas = np.zeros_like(t)
v_inv = np.zeros_like(t)

# Condición inicial
estado_inv = V_dc

# Bucle de integración (Euler)
for k in range(1, len(t)):
    # Controlador de histéresis
    error = i_meas[k-1] - i_ref[k-1]
    if error > banda_A:
        estado_inv = -V_dc
    elif error < -banda_A:
        estado_inv = V_dc
        
    v_inv[k] = estado_inv
    
    # Ecuación del filtro L
    di = ((v_inv[k] - v_red[k]) / L) * dt
    i_meas[k] = i_meas[k-1] + di

# --- VISUALIZACIÓN GRÁFICA (MATPLOTLIB) ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
plt.subplots_adjust(hspace=0.3)

# Gráfica 1: Tensiones
ax1.plot(t * 1000, v_red, color='#2ca02c', linewidth=2, label='Tensión de Red (Bus Infinito)')
ax1.plot(t * 1000, v_inv, color='#1f77b4', alpha=0.7, label='Tensión de Salida del Inversor')
ax1.set_title('Tensiones del Sistema', fontsize=14)
ax1.set_ylabel('Voltaje (V)', fontsize=12)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.6)

# Gráfica 2: Corrientes
ax2.plot(t * 1000, i_ref, color='black', linestyle='--', linewidth=2, label='Corriente de Referencia (P_ref)')
ax2.plot(t * 1000, i_meas, color='#d62728', linewidth=1.5, label='Corriente Real Inyectada')
# Líneas visuales de la banda de histéresis
ax2.plot(t * 1000, i_ref + banda_A, color='gray', linestyle=':', alpha=0.5)
ax2.plot(t * 1000, i_ref - banda_A, color='gray', linestyle=':', alpha=0.5)

ax2.set_title('Dinámica de Corriente y Banda de Histéresis', fontsize=14)
ax2.set_xlabel('Tiempo (ms)', fontsize=12)
ax2.set_ylabel('Corriente (A)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.6)

# Renderizar figura en Streamlit
st.pyplot(fig)
