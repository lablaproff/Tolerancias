import streamlit as st
import numpy as np
import math
import pandas as pd

# ================================
# Funciones para el enfoque metrológico
# ================================

def calcular_tolerancia_sensor(rango_min, rango_max, sensor_type, tolerancia_sensor_input=None):
    """
    Para sensores de temperatura se calcula automáticamente; para otros se usa el valor ingresado.
    """
    if sensor_type == "temperatura":
        return 0.15 + 0.0020 * max(abs(rango_min), abs(rango_max))
    else:
        return tolerancia_sensor_input if tolerancia_sensor_input is not None else 0.5

def calcular_tolerancia_metrologica(errores, incertidumbre_patron, rango_calibrado,
                                    tolerancia_transmisor, tolerancia_plc, tolerancia_pantalla,
                                    sensor_type, tolerancia_sensor_input=None, unidad=""):
    """
    Calcula la tolerancia metrológica combinando:
      - La incertidumbre estadística (desviación estándar de los errores) y la incertidumbre del patrón.
      - Una incertidumbre expandida (k=2, ~95% de confianza) con un ajuste práctico (se suma 0.05).
      - La combinación en cuadratura de las tolerancias de todos los componentes.
    """
    desviacion_estandar = np.std(errores, ddof=1)
    incertidumbre_combinada = math.sqrt(desviacion_estandar**2 + incertidumbre_patron**2)
    incertidumbre_expandida = 2 * incertidumbre_combinada
    tolerancia_estricta = incertidumbre_expandida
    tolerancia_practica = round(incertidumbre_expandida + 0.05, 2)
    
    rango_min, rango_max = rango_calibrado
    span = abs(rango_max - rango_min)
    tolerancia_porcentaje = (incertidumbre_expandida / span) * 100

    # Obtener la tolerancia del sensor
    tolerancia_sensor = calcular_tolerancia_sensor(rango_min, rango_max, sensor_type, tolerancia_sensor_input)
    
    # Combinación en cuadratura de todas las tolerancias
    tolerancia_total = math.sqrt(
        tolerancia_sensor**2 +
        tolerancia_transmisor**2 +
        tolerancia_plc**2 +
        tolerancia_pantalla**2
    )
    
    return {
        "Tolerancia basada en incertidumbre expandida (" + unidad + ")": round(tolerancia_estricta, 4),
        "Tolerancia con ajuste práctico (" + unidad + ")": tolerancia_practica,
        "Tolerancia en porcentaje del rango calibrado (%)": round(tolerancia_porcentaje, 2),
        "Tolerancia total considerando todos los componentes (" + unidad + ")": round(tolerancia_total, 2)
    }

# ================================
# Clase para el cálculo normativo (Caso B)
# ================================
class SensorCalibrationAnalyzer:
    def __init__(self, tipo_sensor, unidades):
        self.tipo_sensor = tipo_sensor
        self.unidades = unidades
        self.parametros_normativos = {
            'temperatura': {
                'clase_precision': {'alta': 0.1, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.15,
                'factor_compensacion': 0.0020
            },
            'presion': {
                'clase_precision': {'alta': 0.1, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.20,
                'factor_compensacion': 0.0025
            },
            'caudal': {
                'clase_precision': {'alta': 0.2, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.25,
                'factor_compensacion': 0.0030
            },
            'velocidad': {
                'clase_precision': {'alta': 0.1, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.18,
                'factor_compensacion': 0.0015
            }
        }
    
    def calcular_tolerancia_transmision(self, rango_calibrado, datos_calibracion, clase_precision='estandar', mostrar_detalles=False):
        if datos_calibracion.empty:
            raise ValueError("No se proporcionaron datos de calibración")
        
        puntos_calibracion = datos_calibracion['valor_medido']
        errores = datos_calibracion['error']
        error_medio = np.mean(errores)
        error_maximo = np.max(np.abs(errores))
        desviacion_estandar = np.std(errores)
        
        params = self.parametros_normativos.get(self.tipo_sensor, self.parametros_normativos['temperatura'])
        rango_min, rango_max = rango_calibrado
        rango_medicion = rango_max - rango_min
        
        precision_base = params['clase_precision'].get(clase_precision, 0.5)
        factor_base = params['factor_base_tolerancia']
        factor_compensacion = params['factor_compensacion'] * max(abs(rango_min), abs(rango_max))
        tolerancia_transmision = factor_base + factor_compensacion
        
        error_maximo_permitido_porcentual = precision_base
        error_maximo_permitido_unidades = (error_maximo_permitido_porcentual / 100) * rango_medicion
        porcentaje_tolerancia = (tolerancia_transmision / rango_medicion) * 100
        incertidumbre_combinada = math.sqrt(desviacion_estandar**2)
        incertidumbre_expandida = 2 * incertidumbre_combinada
        
        resultados = {
            'Tipo de sensor': self.tipo_sensor,
            'Unidades': self.unidades,
            'Rango calibrado': f"{rango_min} - {rango_max} {self.unidades}",
            'Clase de precisión': clase_precision,
            'Error medio': round(error_medio, 4),
            'Error máximo medido': round(error_maximo, 4),
            'Error máximo permitido (%)': round(error_maximo_permitido_porcentual, 2),
            'Error máximo permitido (unidades)': round(error_maximo_permitido_unidades, 4),
            'Desviación estándar': round(desviacion_estandar, 4),
            'Tolerancia de transmisión': round(tolerancia_transmision, 4),
            'Porcentaje de tolerancia': round(porcentaje_tolerancia, 2),
            'Incertidumbre combinada': round(incertidumbre_combinada, 4),
            'Incertidumbre expandida': round(incertidumbre_expandida, 4)
        }
        
        if mostrar_detalles:
            detalles = {
                'Puntos de calibración': list(puntos_calibracion),
                'Errores': list(errores),
                'Error medio': round(error_medio, 4),
                'Error máximo': round(error_maximo, 4),
                'Desviación estándar': round(desviacion_estandar, 4),
                'Precisión base': precision_base,
                'Factor base': factor_base,
                'Factor compensación': factor_compensacion,
                'Rango de medición': rango_medicion,
                'Error máximo permitido (unidades)': round(error_maximo_permitido_unidades, 4),
                'Porcentaje de tolerancia': round(porcentaje_tolerancia, 2)
            }
            resultados['Detalles'] = detalles
        
        return resultados

# ================================
# Función para calibración por comparación (Caso C)
# ================================
def calibracion_por_comparacion(df):
    """
    En calibración por comparación se ingresa 10 pares:
      - 'valor_equipo': medida del equipo.
      - 'valor_referencia': medida con instrumento calibrado.
    Se calcula el error (diferencia) y se extraen estadísticas.
    """
    df["error"] = df["valor_equipo"] - df["valor_referencia"]
    error_medio = np.mean(df["error"])
    error_maximo = np.max(np.abs(df["error"]))
    desviacion_estandar = np.std(df["error"], ddof=1)
    tolerancia_transmision = 2 * desviacion_estandar
    return {
        "Error medio": round(error_medio, 4),
        "Error máximo": round(error_maximo, 4),
        "Desviación estándar": round(desviacion_estandar, 4),
        "Tolerancia de transmisión (k=2)": round(tolerancia_transmision, 4)
    }

# ================================
# Interfaz Principal
# ================================
st.title("Calibración y Tolerancia de Transmisión de Sensores")

# Seleccionar el caso
caso = st.radio("Seleccione el caso a utilizar:", 
                options=["A: Fabricante + Calibración", 
                         "B: Solo Calibración del Proveedor", 
                         "C: Calibración por Comparación"])

# Selección de tipo de sensor
sensor_options = {
    "Temperatura": "temperatura",
    "Presión": "presion",
    "Caudal": "caudal",
    "Velocidad": "velocidad"
}
sensor_elegido = st.selectbox("Seleccione el tipo de sensor", list(sensor_options.keys()))
sensor_type = sensor_options[sensor_elegido]

# Permitir al usuario ingresar la unidad de medida, con un valor por defecto según el sensor
default_units = {"temperatura": "°C", "presion": "bar", "caudal": "m³/h", "velocidad": "rpm"}
unidad = st.text_input("Ingrese la unidad de medida para el sensor", value=default_units[sensor_type])

# Rango de calibración (aplica para casos A y B, y para conocer el span en C)
st.subheader("Rango de Calibración")
rango_min = st.number_input(f"Ingrese límite inferior del rango ({unidad})", value=0.0)
rango_max = st.number_input(f"Ingrese límite superior del rango ({unidad})", value=100.0)

# ------------------------------
# Caso A: Información completa (Fabricante + Calibración)
# ------------------------------
if caso.startswith("A"):
    st.subheader("Caso A: Información del fabricante y datos de calibración")
    st.write("Ingrese los datos de calibración en el formato: **valor_medido,error** (una línea por dato)")
    calibracion_text = st.text_area("Datos de calibración", height=150, placeholder="Ejemplo:\n25.0,0.2\n30.0,-0.1")
    
    st.subheader("Parámetros Metrológicos Adicionales")
    incertidumbre_patron = st.number_input(f"Incertidumbre del patrón ({unidad})", value=0.1, step=0.01)
    tolerancia_transmisor = st.number_input(f"Tolerancia del transmisor ({unidad})", value=0.2, step=0.01)
    tolerancia_plc = st.number_input(f"Tolerancia de la tarjeta PLC ({unidad})", value=0.1, step=0.01)
    tolerancia_pantalla = st.number_input(f"Tolerancia de la pantalla ({unidad})", value=0.05, step=0.01)
    if sensor_type != "temperatura":
        tolerancia_sensor_input = st.number_input(f"Ingrese la tolerancia del sensor (constante, {unidad})", value=0.5, step=0.01)
    else:
        tolerancia_sensor_input = None
        
    if st.button("Calcular (Caso A)"):
        if not calibracion_text.strip():
            st.error("Por favor, ingrese los datos de calibración.")
        else:
            datos = []
            for linea in calibracion_text.splitlines():
                linea = linea.strip()
                if linea:
                    partes = linea.split(',')
                    if len(partes) != 2:
                        st.error("Cada línea debe contener dos valores separados por coma.")
                        break
                    valor_medido, error = map(float, partes)
                    datos.append({'valor_medido': valor_medido, 'error': error})
            if not datos:
                st.error("No se procesaron datos válidos.")
            else:
                df_calibracion = pd.DataFrame(datos)
                resultados = calcular_tolerancia_metrologica(
                    errores=df_calibracion['error'].to_numpy(),
                    incertidumbre_patron=incertidumbre_patron,
                    rango_calibrado=(rango_min, rango_max),
                    tolerancia_transmisor=tolerancia_transmisor,
                    tolerancia_plc=tolerancia_plc,
                    tolerancia_pantalla=tolerancia_pantalla,
                    sensor_type=sensor_type,
                    tolerancia_sensor_input=tolerancia_sensor_input,
                    unidad=unidad
                )
                st.subheader("Resultados Metrológicos (Caso A)")
                for clave, valor in resultados.items():
                    st.write(f"**{clave}**: {valor}")

# ------------------------------
# Caso B: Solo calibración del proveedor (sin parámetros adicionales)
# ------------------------------
elif caso.startswith("B"):
    st.subheader("Caso B: Información de calibración del proveedor")
    st.write("Ingrese los datos de calibración en el formato: **valor_medido,error** (una línea por dato)")
    calibracion_text = st.text_area("Datos de calibración", height=150, placeholder="Ejemplo:\n25.0,0.2\n30.0,-0.1")
    st.subheader("Clase de Precisión")
    precision_map = {"Alta precisión": "alta", "Precisión estándar": "estandar", "Baja precisión": "baja"}
    clase_precision_elegida = st.selectbox("Seleccione la clase de precisión", list(precision_map.keys()))
    clase_precision = precision_map[clase_precision_elegida]
    
    if st.button("Calcular (Caso B)"):
        if not calibracion_text.strip():
            st.error("Por favor, ingrese los datos de calibración.")
        else:
            datos = []
            for linea in calibracion_text.splitlines():
                linea = linea.strip()
                if linea:
                    partes = linea.split(',')
                    if len(partes) != 2:
                        st.error("Cada línea debe contener dos valores separados por coma.")
                        break
                    valor_medido, error = map(float, partes)
                    datos.append({'valor_medido': valor_medido, 'error': error})
            if not datos:
                st.error("No se procesaron datos válidos.")
            else:
                df_calibracion = pd.DataFrame(datos)
                analizador = SensorCalibrationAnalyzer(sensor_type, unidad)
                resultados = analizador.calcular_tolerancia_transmision(
                    (rango_min, rango_max), df_calibracion, clase_precision, mostrar_detalles=False
                )
                st.subheader("Resultados Normativos (Caso B)")
                for clave, valor in resultados.items():
                    if clave != "Detalles":
                        st.write(f"**{clave}**: {valor}")

# ------------------------------
# Caso C: Calibración por comparación
# ------------------------------
elif caso.startswith("C"):
    st.subheader("Caso C: Calibración por Comparación")
    st.write("Ingrese 10 pares de datos que cubran todo el rango de operación del equipo.")
    st.write("Cada línea debe tener el formato: **valor_equipo,valor_referencia**")
    comparacion_text = st.text_area("Datos de calibración por comparación", height=150, 
                                    placeholder="Ejemplo:\n25.0,24.8\n30.0,29.7\n...")
    if st.button("Calcular (Caso C)"):
        if not comparacion_text.strip():
            st.error("Por favor, ingrese los datos de comparación.")
        else:
            datos = []
            for linea in comparacion_text.splitlines():
                linea = linea.strip()
                if linea:
                    partes = linea.split(',')
                    if len(partes) != 2:
                        st.error("Cada línea debe contener dos valores separados por coma.")
                        break
                    valor_equipo, valor_referencia = map(float, partes)
                    datos.append({'valor_equipo': valor_equipo, 'valor_referencia': valor_referencia})
            if len(datos) < 10:
                st.error("Debe ingresar al menos 10 pares de datos.")
            else:
                df_comparacion = pd.DataFrame(datos)
                resultados = calibracion_por_comparacion(df_comparacion)
                st.subheader("Resultados de Calibración por Comparación (Caso C)")
                for clave, valor in resultados.items():
                    st.write(f"**{clave}**: {valor}")
