import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from haversine import haversine, Unit

# ============================================
# DATOS: SIENA (ASUÁN) Y ALEJANDRÍA
# ============================================

# Coordenadas en grados
siena = {"nombre": "Siena (Asuán)", "lat": 24.0889, "lon": 32.8998, "color": "red"}
alejandria = {"nombre": "Alejandría", "lat": 31.2001, "lon": 29.9187, "color": "red"}

# Radio terrestre en km
R = 6371

# ============================================
# FUNCIÓN: CONVERTIR GRADOS A RADIANES
# ============================================
def deg2rad(deg):
    return deg * np.pi / 180

# ============================================
# FUNCIÓN: CONVERTIR COORDENADAS ESFÉRICAS A CARTESIANAS
# ============================================
def esfera_a_cartesiano(lat_deg, lon_deg, radio=R):
    lat_rad = deg2rad(lat_deg)
    lon_rad = deg2rad(lon_deg)
    x = radio * np.cos(lat_rad) * np.cos(lon_rad)
    y = radio * np.cos(lat_rad) * np.sin(lon_rad)
    z = radio * np.sin(lat_rad)
    return x, y, z

# ============================================
# CÁLCULO CON HAVERSINE (usando librería)
# ============================================
distancia_km = haversine(
    (siena["lat"], siena["lon"]),
    (alejandria["lat"], alejandria["lon"]),
    unit=Unit.KILOMETERS
)

# Calcular ángulo central (θ) en radianes
theta_rad = distancia_km / R
theta_deg = theta_rad * 180 / np.pi

# ============================================
# GENERAR PUNTOS INTERMEDIOS PARA EL ARCO (CÍRCULO MÁXIMO)
# ============================================
def generar_arco_esferico(lat1, lon1, lat2, lon2, radio=R, num_puntos=100):
    """Genera puntos intermedios sobre el círculo máximo entre dos puntos"""
    
    # Convertir a radianes
    lat1_r = deg2rad(lat1)
    lon1_r = deg2rad(lon1)
    lat2_r = deg2rad(lat2)
    lon2_r = deg2rad(lon2)
    
    # Vectores unitarios desde el centro
    v1 = np.array([np.cos(lat1_r) * np.cos(lon1_r),
                   np.cos(lat1_r) * np.sin(lon1_r),
                   np.sin(lat1_r)])
    
    v2 = np.array([np.cos(lat2_r) * np.cos(lon2_r),
                   np.cos(lat2_r) * np.sin(lon2_r),
                   np.sin(lat2_r)])
    
    # Ángulo entre los dos vectores
    angulo_total = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))
    
    # Generar puntos intermedios (interpolación esférica)
    puntos = []
    for i in range(num_puntos + 1):
        t = i / num_puntos
        angulo = angulo_total * t
        
        # Fórmula de interpolación esférica (slerp)
        factor = np.sin(angulo) / np.sin(angulo_total) if angulo_total > 0 else 0
        v_interpolado = (np.sin(angulo_total - angulo) / np.sin(angulo_total)) * v1 + factor * v2
        
        # Escalar al radio terrestre
        punto = v_interpolado * radio
        puntos.append(punto)
    
    return np.array(puntos)

# Generar arco
arco_puntos = generar_arco_esferico(siena["lat"], siena["lon"], alejandria["lat"], alejandria["lon"], radio=R)

# ============================================
# CREAR FIGURA 3D CON PLOTLY
# ============================================

# Crear la esfera terrestre (puntos de malla)
phi = np.linspace(0, 2 * np.pi, 100)
theta = np.linspace(0, np.pi, 100)
phi_grid, theta_grid = np.meshgrid(phi, theta)

x_esfera = R * np.sin(theta_grid) * np.cos(phi_grid)
y_esfera = R * np.sin(theta_grid) * np.sin(phi_grid)
z_esfera = R * np.cos(theta_grid)

# Puntos de Siena y Alejandría en coordenadas cartesianas
x1, y1, z1 = esfera_a_cartesiano(siena["lat"], siena["lon"])
x2, y2, z2 = esfera_a_cartesiano(alejandria["lat"], alejandria["lon"])

# Vectores desde el centro (para dibujar radios)
centro = [0, 0, 0]

# ============================================
# CONSTRUIR EL GRÁFICO
# ============================================

fig = go.Figure()

# 1. Esfera terrestre (semitransparente)
fig.add_trace(go.Surface(
    x=x_esfera, y=y_esfera, z=z_esfera,
    colorscale='Blues',
    opacity=0.35,
    showscale=False,
    name='Tierra'
))

# 2. Puntos de Siena y Alejandría
fig.add_trace(go.Scatter3d(
    x=[x1, x2],
    y=[y1, y2],
    z=[z1, z2],
    mode='markers+text',
    marker=dict(size=8, color='red', symbol='circle'),
    text=[siena["nombre"], alejandria["nombre"]],
    textposition='top center',
    name='Ciudades'
))

# 3. Radios (líneas desde el centro a cada punto)
fig.add_trace(go.Scatter3d(
    x=[centro[0], x1, None, centro[0], x2],
    y=[centro[1], y1, None, centro[1], y2],
    z=[centro[2], z1, None, centro[2], z2],
    mode='lines',
    line=dict(color='green', width=2, dash='solid'),
    name='Radios (R)'
))

# 4. Arco sobre la superficie (círculo máximo)
fig.add_trace(go.Scatter3d(
    x=arco_puntos[:, 0],
    y=arco_puntos[:, 1],
    z=arco_puntos[:, 2],
    mode='lines',
    line=dict(color='red', width=5),
    name='Arco (círculo máximo)'
))

# 5. Línea recta (cuerda) que atraviesa la Tierra (opcional, para comparar)
fig.add_trace(go.Scatter3d(
    x=[x1, x2],
    y=[y1, y2],
    z=[z1, z2],
    mode='lines',
    line=dict(color='orange', width=2, dash='dash'),
    name='Cuerda (línea recta)'
))

# ============================================
# CONFIGURAR APARIENCIA DEL GRÁFICO
# ============================================

fig.update_layout(
    title=dict(
        text=f"🌍 El experimento de Eratóstenes en 3D<br>"
             f"Ángulo central: {theta_deg:.2f}° | "
             f"Distancia sobre la superficie: {distancia_km:.0f} km | "
             f"Radio terrestre: {R} km",
        font=dict(size=14),
        x=0.5
    ),
    scene=dict(
        xaxis_title='X (km)',
        yaxis_title='Y (km)',
        zaxis_title='Z (km)',
        aspectmode='data',
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=0.8)
        )
    ),
    width=1000,
    height=800,
    legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)')
)

# ============================================
# MOSTRAR RESULTADOS EN CONSOLA
# ============================================
print("\n" + "="*60)
print("📐 CÁLCULO DE ERATÓSTENES - RESULTADOS")
print("="*60)
print(f"\n📍 CIUDADES:")
print(f"   • {siena['nombre']}: {siena['lat']}° N, {siena['lon']}° E")
print(f"   • {alejandria['nombre']}: {alejandria['lat']}° N, {alejandria['lon']}° E")
print(f"\n📏 RESULTADOS CON COORDENADAS MODERNAS:")
print(f"   • Ángulo central (θ): {theta_deg:.4f} grados = {theta_rad:.6f} radianes")
print(f"   • Distancia sobre la superficie: {distancia_km:.1f} km")
print(f"   • Fórmula aplicada: d = R × θ = {R} km × {theta_rad:.6f} = {distancia_km:.1f} km")
print(f"\n🏛️  DATOS HISTÓRICOS (Eratóstenes, 240 a.C.):")
print(f"   • Ángulo medido con la sombra: 7.2 grados")
print(f"   • Distancia caminada entre ciudades: 800 km")
print(f"   • Circunferencia calculada: 40.000 km")
print(f"\n📊 COMPARACIÓN:")
print(f"   • Diferencia en ángulo: {abs(7.2 - theta_deg):.2f} grados")
print(f"   • Diferencia en distancia: {abs(800 - distancia_km):.1f} km")
print(f"   • La diferencia se debe a que Siena y Alejandría no están exactamente")
print(f"     en el mismo meridiano (diferencia de longitud: {abs(siena['lon'] - alejandria['lon']):.2f}°)")
print("\n" + "="*60)
print("🎨 GRÁFICO 3D INTERACTIVO - Podés rotar, acercar y explorar")
print("="*60)

# ============================================
# MOSTRAR EL GRÁFICO
# ============================================
fig.show()
