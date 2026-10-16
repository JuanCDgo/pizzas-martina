# Archivo Maestro - Pizzas Martina (Streamlit + Supabase)

## 📌 Resumen del Proyecto
App para la toma de pedidos, gestión de clientes (agenda) y cálculo de costos (por kilo o unidad) para el emprendimiento de pizzas. 
- **Stack:** Python, Streamlit, Supabase.
- **Objetivo clave:** Que Juan y Belén puedan cargar pedidos desde sus celus y se sincronice todo en tiempo real mediante la base de datos en la nube.

## 🗂️ Estructura de Archivos
- `maestro.md` -> Esta bitácora.
- `app.py` -> Archivo principal de Streamlit (interfaz y lógica).
- `requirements.txt` -> Librerías de Python (`streamlit`, `supabase`, `pandas`).
- `.streamlit/config.toml` -> Configuración visual (colores naranjas y fondo oscuro).
- `.streamlit/secrets.toml` -> Credenciales de conexión a Supabase.

## 🛠️ Decisiones Técnicas Tomadas
1. **Base de datos:** Se usa Supabase para evitar conflictos de concurrencia (`pizzas_clientes`, `pizzas_insumos`, `pizzas_pedidos`).
2. **Variedades de Pizza Dinámicas:** Arranca con **Muzzarella**, **Especial Huevo** y **Especial Tomate**, y permite agregar nuevas clases de pizza desde la pestaña `💰 Precios y Costos` sin necesidad de tocar SQL en Supabase.
3. **Costos:** Se manejan por Kilo (uso en gramos) o por Unidad de bulto cerrado para facilitar la carga a Belén.
4. **Reporte de Producción por WhatsApp:** En la pestaña `📊 Caja / Día` hay un botón directo para enviar por WhatsApp el resumen del día con la cantidad total de pizzas y el desglose por cada estilo (con opción de filtrar solo pendientes e incluir o no la lista de clientes).
5. **Estilo:** Dark mode nativo de Streamlit tuneado con colores de la marca (naranja `#FF6B00`).
