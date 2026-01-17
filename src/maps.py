import folium

# Coordenada inicial (latitud, longitud)
lat, lon = 4.7110, -74.0721  # Bogotá

# Radio del círculo [m]
radio = 500

# Crear mapa centrado
m = folium.Map(location=[lat, lon], zoom_start=15)

# Agregar círculo
folium.Circle(
    location=[lat, lon],
    radius=radio,           # en metros
    color='blue',
    fill=True,
    fill_opacity=0.3,
    popup=f"Radio: {radio} m"
).add_to(m)

# Mostrar
#m.save("mapa.html")
