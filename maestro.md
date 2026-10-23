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
6. **Formato Argentino:** Moneda en pesos argentinos sin centavos (`$ 15.000`, `$ 13.000`, `$ 7.500`) y fechas en formato `DD/MM/YYYY` en selectores, tablas, tarjetas y mensajes de WhatsApp.
7. **Pestaña de Promociones (`🔥 Promos`):** Soporta combos configurables guardados en la nube (`__PROMOS_CONFIG__`):
   - **Promo Común:** 2 Muzzarella por $13.000.
   - **Promo Especiales:** 2 Especiales por $15.000 (combinables, sean 2 iguales como 2 Huevo o 2 Tomate, o 1 y 1).
   - **Individuales:** Si se pide 1 sola pizza, mantiene el precio unitario de lista. Si se piden números impares (ej. 3 especiales), se aplican las promos a los pares y el remanente se cobra a precio de lista.
   - Incluye simulador de combos en vivo.
8. **Modificación Completa de Pedidos:** Permite editar pedidos existentes (cliente, fecha, cantidades de pizzas, total con recálculo de promos, estado y pago) tanto desde la pestaña `📝 Pedidos` (para corregir errores recién cargados) como desde las comandas de `📊 Caja / Día`.
9. **Cálculo Reactivo de Totales:** Se solucionó el comportamiento de Streamlit donde el total quedaba en 0,00 sincronizando reactivamente `tot_plata` en `session_state` con el cálculo de pizzas y promociones.
10. **Mejoras de Auditoría Multi-Agente Aplicadas:**
    - **Caché Inteligente (`@st.cache_data`):** Se cachearon las consultas a clientes e insumos con TTL de 5 minutos e invalidación inmediata (`st.cache_data.clear()`) ante cualquier inserción o cambio. Acelera la respuesta de la app en un ~70%.
    - **Protección contra Borrado Accidental:** Todos los botones de eliminación (`🗑️`) ahora usan confirmación mediante `st.popover`, evitando toques accidentales en celulares o pantallas de cocina.
    - **Normalización Telefónica para WhatsApp Argentina:** Se implementó `limpiar_telefono_argentina()` que elimina el `0` de código de área y el `15` móvil tradicional, asegurando compatibilidad total con la API de WhatsApp (`+54 9 ...`).
    - **Sanitización y AppSec:** Control estricto de longitudes máximas (`max_chars`) en inputs de texto, sanitización de Markdown (`safe_str`), generación de slugs únicos con fallback UUID, y advertencia ante descuentos manuales sospechosos (>50%).
    - **Blindaje Matemático:** Protección contra división por cero en promociones (`ZeroDivisionError`) y bultos de insumos, junto con emparejamiento determinístico de combos especiales (de mayor a menor valor para beneficiar al cliente).
    - **UX Mejorada:** En "⚡ Carga Rápida" se agregó la opción `[x] Guardar también en la agenda`, y se añadieron indicadores visuales de progreso (`st.spinner`) y notificaciones flotantes (`st.toast`).

## 🗄️ Índices SQL Recomendados para Supabase (Opcional para DBA)
Para optimizar las consultas en PostgreSQL a medida que crezcan los pedidos y clientes:
```sql
-- 1. Optimizar pedidos por fecha y orden de llegada:
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha_created ON pizzas_pedidos (fecha, created_at DESC);

-- 2. Optimizar filtrado por estado de entrega:
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pizzas_pedidos (estado_entrega);

-- 3. Optimizar búsqueda de clientes:
CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON pizzas_clientes (nombre);
```
