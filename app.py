import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date
import json
import re
from urllib.parse import quote

# --- 1. CONFIGURACIÓN PRINCIPAL ---
st.set_page_config(
    page_title="Pizzas Martina",
    page_icon="🍕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos sutiles para mejorar visualización en celulares
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        padding: 12px 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Error conectando a Supabase. Revisá que `.streamlit/secrets.toml` esté bien configurado. Detalle: {e}")
    st.stop()


# --- 3. FUNCIONES AUXILIARES DE DATOS Y VARIEDADES DINÁMICAS ---
CONFIG_ROW_NAME = "__PRECIOS_VENTA__"
CATALOG_ROW_NAME = "__CATALOGO_PIZZAS__"

VARIEDADES_BASE = [
    {"slug": "muzza", "nombre": "Muzzarella", "emoji": "🧀", "precio": 8000.0, "base": True},
    {"slug": "huevo", "nombre": "Especial Huevo", "emoji": "🥚", "precio": 9500.0, "base": True},
    {"slug": "tomate", "nombre": "Especial Tomate", "emoji": "🍅", "precio": 9500.0, "base": True},
]

def slugify(texto: str) -> str:
    limpio = re.sub(r"[^a-z0-9]+", "_", texto.lower().strip()).strip("_")
    return limpio or "pizza_extra"

def parsear_modo_insumo(modo_raw: str):
    """Extrae el modo base ('kg' o 'unidad') y el diccionario de usos en variedades extra."""
    if not modo_raw:
        return "kg", {}
    if "|" in modo_raw:
        partes = modo_raw.split("|", 1)
        try:
            return partes[0], json.loads(partes[1])
        except Exception:
            return partes[0], {}
    return modo_raw, {}

def empaquetar_modo_insumo(modo_base: str, usos_extra: dict) -> str:
    usos_limpios = {k: float(v) for k, v in usos_extra.items() if float(v or 0) > 0}
    if not usos_limpios:
        return modo_base
    return f"{modo_base}|{json.dumps(usos_limpios)}"

def parsear_estado_y_extras_pedido(estado_raw: str):
    """Extrae el estado de entrega ('pendiente', 'en horno', 'entregado') y cantidades de variedades extra."""
    if not estado_raw:
        return "pendiente", {}
    if "|" in estado_raw:
        partes = estado_raw.split("|", 1)
        try:
            return partes[0], json.loads(partes[1])
        except Exception:
            return partes[0], {}
    return estado_raw, {}

def empaquetar_estado_y_extras_pedido(estado_limpio: str, cant_extras: dict) -> str:
    extras_limpios = {k: int(v) for k, v in cant_extras.items() if int(v or 0) > 0}
    if not extras_limpios:
        return estado_limpio
    return f"{estado_limpio}|{json.dumps(extras_limpios)}"

def obtener_clientes():
    res = supabase.table("pizzas_clientes").select("*").order("nombre").execute()
    return res.data or []

def obtener_insumos_y_catalogo():
    res = supabase.table("pizzas_insumos").select("*").order("created_at").execute()
    filas = res.data or []

    catalogo = [dict(v) for v in VARIEDADES_BASE]
    id_catalogo = None
    id_precios_legacy = None
    precios_legacy = None
    insumos = []

    for f in filas:
        nombre_f = f.get("nombre")
        modo_f = f.get("modo") or ""

        if nombre_f == CATALOG_ROW_NAME and modo_f.startswith("catalogo|"):
            id_catalogo = f.get("id")
            try:
                datos_cat = json.loads(modo_f.split("|", 1)[1])
                if isinstance(datos_cat, list) and len(datos_cat) > 0:
                    catalogo = datos_cat
            except Exception:
                pass
        elif nombre_f == CONFIG_ROW_NAME and modo_f == "config":
            id_precios_legacy = f.get("id")
            precios_legacy = {
                "muzza": float(f.get("uso_muzza") or 8000.0),
                "huevo": float(f.get("uso_huevo") or 9500.0),
                "tomate": float(f.get("uso_tomate") or 9500.0),
            }
        else:
            insumos.append(f)

    # Si no existía fila de catálogo pero sí precios legacy, sincronizar precios base
    if not id_catalogo and precios_legacy:
        for v in catalogo:
            if v["slug"] in precios_legacy:
                v["precio"] = precios_legacy[v["slug"]]

    return insumos, catalogo, id_catalogo

def guardar_catalogo_pizzas(id_catalogo, lista_catalogo):
    modo_serializado = f"catalogo|{json.dumps(lista_catalogo, ensure_ascii=False)}"
    p_muzza = next((float(v["precio"]) for v in lista_catalogo if v["slug"] == "muzza"), 8000.0)
    p_huevo = next((float(v["precio"]) for v in lista_catalogo if v["slug"] == "huevo"), 9500.0)
    p_tomate = next((float(v["precio"]) for v in lista_catalogo if v["slug"] == "tomate"), 9500.0)

    datos = {
        "nombre": CATALOG_ROW_NAME,
        "modo": modo_serializado,
        "precio_bulto": 0,
        "cantidad_bulto": 1,
        "uso_muzza": p_muzza,
        "uso_huevo": p_huevo,
        "uso_tomate": p_tomate,
    }
    if id_catalogo:
        supabase.table("pizzas_insumos").update(datos).eq("id", id_catalogo).execute()
    else:
        supabase.table("pizzas_insumos").insert(datos).execute()

def obtener_uso_insumo_en_variedad(insumo: dict, slug: str) -> float:
    if slug == "muzza":
        return float(insumo.get("uso_muzza") or 0)
    if slug == "huevo":
        return float(insumo.get("uso_huevo") or 0)
    if slug == "tomate":
        return float(insumo.get("uso_tomate") or 0)
    _, usos_extra = parsear_modo_insumo(insumo.get("modo", "kg"))
    return float(usos_extra.get(slug) or 0)

def obtener_cantidad_pedido_variedad(pedido: dict, slug: str) -> int:
    if slug == "muzza":
        return int(pedido.get("cant_muzza") or 0)
    if slug == "huevo":
        return int(pedido.get("cant_huevo") or 0)
    if slug == "tomate":
        return int(pedido.get("cant_tomate") or 0)
    _, extras = parsear_estado_y_extras_pedido(pedido.get("estado_entrega", "pendiente"))
    return int(extras.get(slug) or 0)

def calcular_costos_por_pizza(insumos, catalogo):
    costos_totales = {v["slug"]: 0.0 for v in catalogo}
    detalle_por_insumo = []

    for ins in insumos:
        modo_base, _ = parsear_modo_insumo(ins.get("modo", "kg"))
        precio_bulto = float(ins.get("precio_bulto") or 0)
        cant_bulto = float(ins.get("cantidad_bulto") or 1)
        if cant_bulto <= 0:
            cant_bulto = 1.0

        costo_por_unidad_compra = precio_bulto / cant_bulto
        factor = (1.0 / 1000.0) if modo_base == "kg" else 1.0

        costos_este_insumo = {}
        usos_este_insumo = {}
        for v in catalogo:
            slug = v["slug"]
            uso_v = obtener_uso_insumo_en_variedad(ins, slug)
            costo_v = costo_por_unidad_compra * factor * uso_v
            costos_totales[slug] += costo_v
            costos_este_insumo[slug] = round(costo_v, 2)
            usos_este_insumo[slug] = uso_v

        detalle_por_insumo.append({
            "id": ins["id"],
            "Insumo": ins["nombre"],
            "modo_base": modo_base,
            "Costo x Kg/Unid": round(costo_por_unidad_compra, 2),
            "costos_variedad": costos_este_insumo,
            "usos_variedad": usos_este_insumo,
        })

    return {
        "por_variedad": costos_totales,
        "detalle": detalle_por_insumo
    }

def link_whatsapp_cliente(telefono: str, nombre: str, detalle_txt: str, total: float):
    if not telefono:
        return None
    solo_nums = re.sub(r"\D", "", telefono)
    if not solo_nums:
        return None
    if not solo_nums.startswith("54"):
        solo_nums = "549" + solo_nums.lstrip("0")
    msg = f"Hola {nombre}! Te escribimos de *Pizzas Martina* por tu pedido ({detalle_txt} - Total: ${total:,.0f})."
    return f"https://wa.me/{solo_nums}?text={quote(msg)}"

def armar_mensaje_produccion_whatsapp(
    fecha_obj: date,
    catalogo: list,
    totales_estilo: dict,
    pendientes_estilo: dict,
    pedidos_lista: list,
    solo_pendientes: bool = False,
    incluir_clientes: bool = False,
    incluir_caja: bool = True,
    datos_caja: dict = None
) -> str:
    fecha_str = fecha_obj.strftime("%d/%m/%Y")
    fuente_cant = pendientes_estilo if solo_pendientes else totales_estilo
    total_gral = sum(fuente_cant.values())
    titulo_modo = "PENDIENTES DE HORNEAR / ENTREGAR" if solo_pendientes else "RESUMEN DEL DIA"

    lineas = [
        f"*PIZZAS MARTINA - {fecha_str}*",
        f"*{titulo_modo}*",
        "",
        f"*TOTAL PIZZAS: {total_gral}*",
    ]

    for v in catalogo:
        slug = v["slug"]
        cant_v = fuente_cant.get(slug, 0)
        if cant_v > 0 or v.get("base"):
            lineas.append(f"- {v['nombre']}: *{cant_v}*")

    if not solo_pendientes:
        tot_pend = sum(pendientes_estilo.values())
        tot_entregadas = max(0, sum(totales_estilo.values()) - tot_pend)
        lineas.append("")
        lineas.append(f"Entregadas: *{tot_entregadas}* | Pendientes: *{tot_pend}*")

    if incluir_clientes and pedidos_lista:
        lineas.append("")
        lineas.append("*DETALLE DE PEDIDOS:*")
        for p in pedidos_lista:
            est_limpio, _ = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))
            if solo_pendientes and est_limpio == "entregado":
                continue
            partes_p = []
            for v in catalogo:
                c_var = obtener_cantidad_pedido_variedad(p, v["slug"])
                if c_var > 0:
                    partes_p.append(f"{c_var} {v['nombre']}")
            txt_pizzas = ", ".join(partes_p)
            dir_txt = f" ({p['direccion']})" if p.get("direccion") else ""
            monto_txt = f" - ${float(p.get('total_plata') or 0):,.0f}"
            lineas.append(f"- *{p['nombre_cliente']}*{dir_txt}: {txt_pizzas}{monto_txt}")

    if incluir_caja and datos_caja:
        lineas.append("")
        lineas.append("*RESUMEN DE CAJA:*")
        lineas.append(f"- Venta Total: *${datos_caja['total']:,.0f}*")
        lineas.append(f"- Transferencia: ${datos_caja['transferencia']:,.0f}")
        lineas.append(f"- Efectivo: ${datos_caja['efectivo']:,.0f}")
        lineas.append(f"- Falta Cobrar: ${datos_caja['pendiente']:,.0f}")
        lineas.append(f"- Ganancia limpia est.: *${datos_caja['ganancia']:,.0f}*")

    return "\n".join(lineas)


# --- 4. CARGA INICIAL DE DATOS ---
clientes = obtener_clientes()
insumos, catalogo_pizzas, id_catalogo = obtener_insumos_y_catalogo()
costos_pizza = calcular_costos_por_pizza(insumos, catalogo_pizzas)

# --- 5. ENCABEZADO Y NAVEGACIÓN ---
col_titulo, col_refresh = st.columns([4, 1])
with col_titulo:
    st.title("🍕 Pizzas Martina")
with col_refresh:
    st.write("")
    if st.button("🔄", help="Actualizar datos en tiempo real", use_container_width=True):
        st.rerun()

tab_pedidos, tab_clientes, tab_costos, tab_caja = st.tabs([
    "📝 Pedidos",
    "👥 Clientes",
    "💰 Precios y Costos",
    "📊 Caja / Día"
])


# =========================================================
# PESTAÑA 1: PEDIDOS
# =========================================================
with tab_pedidos:
    st.subheader("Nuevo Pedido")

    mapa_clientes = {
        f"📒 {c['nombre']} ({c.get('direccion') or 'Sin dirección'})": c
        for c in clientes
    }
    opciones_clientes = list(mapa_clientes.keys()) + ["⚡ Carga Rápida (cliente de paso / sin agendar)"]

    col_top1, col_top2 = st.columns([2, 1])
    with col_top1:
        seleccion_cli = st.selectbox(
            "Cliente:",
            options=opciones_clientes
        )
    with col_top2:
        fecha_pedido = st.date_input("Fecha del pedido", value=date.today())

    cliente_elegido = mapa_clientes.get(seleccion_cli)

    if cliente_elegido:
        nombre_final = cliente_elegido["nombre"]
        telefono_final = cliente_elegido.get("telefono") or ""
        direccion_final = cliente_elegido.get("direccion") or ""
        st.caption(
            f"📍 **Dirección:** {direccion_final or 'Sin dirección'} · "
            f"📞 **Tel:** {telefono_final or 'Sin teléfono'}"
        )
    else:
        nombre_rapido = st.text_input(
            "Nombre o referencia rápida para este pedido *",
            placeholder="Ej: Lucas (retira), Vecino 3°B, Mostrador..."
        )
        nombre_final = nombre_rapido.strip()
        telefono_final = ""
        direccion_final = ""

    st.markdown("##### 🍕 Cantidades por Estilo de Pizza")
    cantidades_elegidas = {}
    cols_pizzas = st.columns(3)
    for idx, var in enumerate(catalogo_pizzas):
        with cols_pizzas[idx % 3]:
            cantidades_elegidas[var["slug"]] = st.number_input(
                f"{var['emoji']} {var['nombre']} (${float(var['precio']):,.0f})",
                min_value=0,
                step=1,
                value=0,
                key=f"ped_cant_{var['slug']}"
            )

    total_calculado = sum(
        cantidades_elegidas[v["slug"]] * float(v["precio"])
        for v in catalogo_pizzas
    )

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        total_plata = st.number_input(
            "💵 Total a cobrar ($)",
            min_value=0.0,
            value=float(total_calculado),
            step=500.0,
            help="Se calcula solo según las pizzas elegidas, pero podés ajustarlo si hay envío o descuento."
        )
    with col_p2:
        metodo_pago = st.selectbox(
            "Método de Pago",
            options=["transferencia", "efectivo", "pendiente"],
            format_func=lambda x: {
                "transferencia": "🏦 Transferencia",
                "efectivo": "💵 Efectivo",
                "pendiente": "⏳ Pendiente"
            }.get(x, x.capitalize())
        )
    with col_p3:
        estado_entrega = st.selectbox(
            "Estado de Entrega",
            options=["pendiente", "entregado", "cancelado"],
            format_func=lambda x: {
                "pendiente": "🕒 Pendiente",
                "entregado": "✅ Entregado",
                "cancelado": "❌ Cancelado / No había nadie"
            }.get(x, x.capitalize())
        )

    if st.button("🔥 Cargar Pedido", type="primary", use_container_width=True):
        total_pizzas_ped = sum(cantidades_elegidas.values())
        if not nombre_final:
            st.warning("⚠️ Elegí un cliente de la lista o escribí un nombre rápido.")
        elif total_pizzas_ped <= 0:
            st.warning("⚠️ Agregá al menos 1 pizza al pedido.")
        else:
            extras_pedido = {
                k: v for k, v in cantidades_elegidas.items()
                if k not in ("muzza", "huevo", "tomate") and v > 0
            }
            estado_empaquetado = empaquetar_estado_y_extras_pedido(estado_entrega, extras_pedido)

            supabase.table("pizzas_pedidos").insert({
                "fecha": str(fecha_pedido),
                "nombre_cliente": nombre_final,
                "telefono": telefono_final,
                "direccion": direccion_final,
                "cant_muzza": int(cantidades_elegidas.get("muzza", 0)),
                "cant_huevo": int(cantidades_elegidas.get("huevo", 0)),
                "cant_tomate": int(cantidades_elegidas.get("tomate", 0)),
                "total_plata": float(total_plata),
                "estado_entrega": estado_empaquetado,
                "metodo_pago": metodo_pago
            }).execute()

            st.success(f"✅ Pedido de **{nombre_final}** cargado correctamente (${total_plata:,.0f}).")
            st.rerun()


# =========================================================
# PESTAÑA 2: AGENDA DE CLIENTES HABITUALES (SIN PEDIDO)
# =========================================================
with tab_clientes:
    st.subheader("👥 Agenda de Clientes Habituales")
    st.caption(
        "Guardá acá a todos tus clientes con su teléfono y dirección cuando quieras (sin necesidad de cargar un pedido). "
        "Cuando te compren, solo los elegís de la lista en la pestaña **📝 Pedidos** y se completan todos sus datos solos."
    )

    with st.container(border=True):
        st.markdown("#### 📝 Guardar Nuevo Cliente")
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            ag_nom = st.text_input("Nombre y Apellido *", placeholder="Ej: Juan Pérez", key="nuevo_cli_nom")
        with ac2:
            ag_tel = st.text_input("Teléfono / WhatsApp", placeholder="Ej: 11 2345-6789", key="nuevo_cli_tel")
        with ac3:
            ag_dir = st.text_input("Dirección / Entrecalles", placeholder="Ej: Belgrano 1230", key="nuevo_cli_dir")

        if st.button("💾 Guardar Cliente en la Agenda", type="primary", use_container_width=True):
            if not ag_nom.strip():
                st.warning("⚠️ Escribí al menos el nombre del cliente.")
            else:
                supabase.table("pizzas_clientes").insert({
                    "nombre": ag_nom.strip(),
                    "telefono": ag_tel.strip(),
                    "direccion": ag_dir.strip()
                }).execute()
                st.success(f"✅ Cliente **{ag_nom.strip()}** guardado en la agenda.")
                st.rerun()

    st.divider()

    st.subheader(f"📒 Clientes Guardados ({len(clientes)})")
    if clientes:
        busqueda_cli = st.text_input("🔍 Buscar cliente por nombre, dirección o teléfono:", key="busq_cli")
        clientes_filtrados = [
            c for c in clientes
            if busqueda_cli.lower() in (c.get("nombre") or "").lower()
            or busqueda_cli.lower() in (c.get("direccion") or "").lower()
            or busqueda_cli.lower() in (c.get("telefono") or "").lower()
        ]
        if not clientes_filtrados:
            st.info("No se encontraron clientes con esa búsqueda.")
        for c in clientes_filtrados:
            with st.container(border=True):
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    ed_cli_nom = st.text_input("Nombre", value=c.get("nombre") or "", key=f"cnom_{c['id']}")
                with cc2:
                    ed_cli_tel = st.text_input("Teléfono", value=c.get("telefono") or "", key=f"ctel_{c['id']}")
                with cc3:
                    ed_cli_dir = st.text_input("Dirección", value=c.get("direccion") or "", key=f"cdir_{c['id']}")

                cb1, cb2, cb3 = st.columns([2, 2, 1])
                with cb1:
                    if st.button("💾 Guardar Cambios", key=f"save_cli_{c['id']}", use_container_width=True):
                        supabase.table("pizzas_clientes").update({
                            "nombre": ed_cli_nom.strip() or c["nombre"],
                            "telefono": ed_cli_tel.strip(),
                            "direccion": ed_cli_dir.strip()
                        }).eq("id", c["id"]).execute()
                        st.success("Cliente actualizado.")
                        st.rerun()
                with cb2:
                    tel_limpio = re.sub(r"\D", "", ed_cli_tel or "")
                    if tel_limpio:
                        if not tel_limpio.startswith("54"):
                            tel_limpio = "549" + tel_limpio.lstrip("0")
                        st.link_button(
                            "📲 Escribir WhatsApp",
                            f"https://wa.me/{tel_limpio}",
                            use_container_width=True
                        )
                with cb3:
                    if st.button("🗑️ Borrar", key=f"del_cli_{c['id']}", use_container_width=True):
                        supabase.table("pizzas_clientes").delete().eq("id", c["id"]).execute()
                        st.rerun()
    else:
        st.info("Todavía no hay clientes guardados. Cargalos arriba para tenerlos listos cuando arranquen las ventas.")



# =========================================================
# PESTAÑA 2: PRECIOS, VARIEDADES DE PIZZA Y COSTOS (BELÉN)
# =========================================================
with tab_costos:
    st.subheader("💰 Precios de Venta y Rentabilidad por Estilo")
    st.caption("Compará el costo de la receta vs. el precio de venta y agregá nuevas variedades de pizza cuando quieras.")

    cols_rent = st.columns(3)
    for idx, var in enumerate(catalogo_pizzas):
        with cols_rent[idx % 3]:
            slug = var["slug"]
            costo_v = costos_pizza["por_variedad"].get(slug, 0.0)
            precio_v = float(var["precio"])
            ganancia_v = precio_v - costo_v
            margen_pct = (ganancia_v / precio_v * 100) if precio_v > 0 else 0
            st.metric(
                label=f"{var['emoji']} {var['nombre']}",
                value=f"${precio_v:,.0f}",
                delta=f"Ganancia: ${ganancia_v:,.0f} ({margen_pct:.0f}%)"
            )
            st.caption(f"Costo receta: **${costo_v:,.0f}**")

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        with st.expander("✏️ Cambiar Precios de Venta", expanded=False):
            with st.form("form_precios_venta"):
                nuevos_precios = {}
                for var in catalogo_pizzas:
                    nuevos_precios[var["slug"]] = st.number_input(
                        f"{var['emoji']} {var['nombre']} ($)",
                        min_value=0.0,
                        value=float(var["precio"]),
                        step=500.0,
                        key=f"pv_edit_{var['slug']}"
                    )
                if st.form_submit_button("💾 Guardar Precios", use_container_width=True):
                    for var in catalogo_pizzas:
                        var["precio"] = float(nuevos_precios[var["slug"]])
                    guardar_catalogo_pizzas(id_catalogo, catalogo_pizzas)
                    st.success("✅ Precios actualizados.")
                    st.rerun()

    with col_exp2:
        with st.expander("🍕 Agregar / Quitar Variedad de Pizza", expanded=False):
            with st.form("form_nueva_variedad", clear_on_submit=True):
                nv_nombre = st.text_input("Nombre del nuevo estilo *", placeholder="Ej: Fugazzeta, Calabresa, Jamón y Morrón")
                nv_c1, nv_c2 = st.columns(2)
                with nv_c1:
                    nv_emoji = st.selectbox("Ícono", ["🍕", "🧅", "🌶️", "🥓", "🍄", "🫒", "🧄", "🧀"])
                with nv_c2:
                    nv_precio = st.number_input("Precio de Venta ($)", min_value=0.0, value=10000.0, step=500.0)

                if st.form_submit_button("➕ Crear Estilo de Pizza", use_container_width=True):
                    if not nv_nombre.strip():
                        st.warning("Escribí el nombre de la nueva variedad.")
                    else:
                        nuevo_slug = slugify(nv_nombre)
                        slugs_actuales = [v["slug"] for v in catalogo_pizzas]
                        if nuevo_slug in slugs_actuales:
                            st.warning("Ya existe una variedad con ese nombre.")
                        else:
                            catalogo_pizzas.append({
                                "slug": nuevo_slug,
                                "nombre": nv_nombre.strip(),
                                "emoji": nv_emoji,
                                "precio": float(nv_precio),
                                "base": False
                            })
                            guardar_catalogo_pizzas(id_catalogo, catalogo_pizzas)
                            st.success(f"✅ Variedad '{nv_nombre.strip()}' agregada a toda la app.")
                            st.rerun()

            variedades_extra = [v for v in catalogo_pizzas if not v.get("base")]
            if variedades_extra:
                st.markdown("**Variedades agregadas:**")
                for ve in variedades_extra:
                    ce1, ce2 = st.columns([3, 1])
                    with ce1:
                        st.write(f"{ve['emoji']} **{ve['nombre']}** (${float(ve['precio']):,.0f})")
                    with ce2:
                        if st.button("🗑️", key=f"del_var_{ve['slug']}", help="Quitar variedad"):
                            nuevo_cat = [v for v in catalogo_pizzas if v["slug"] != ve["slug"]]
                            guardar_catalogo_pizzas(id_catalogo, nuevo_cat)
                            st.rerun()

    st.divider()

    # --- CALCULADORA DE INSUMOS DE BELÉN ---
    st.subheader("⚖️ Calculadora de Costos e Insumos")
    st.caption(
        "Acá podés cargar **todos tus insumos**: tanto **comestibles** (harina, muzzarella, salsa, huevo, tomate) "
        "como **descartables y packaging** (cajas, bolsas, papel manteca, separadores)."
    )

    if not insumos:
        with st.container(border=True):
            st.info("💡 **¿Querés arrancar más rápido?** Podés cargar una lista base con los insumos más comunes (Harina, Muzzarella, Salsa, Levadura, Huevo, Tomate, Caja de Pizza y Bolsa Camiseta) y después solo editás los precios.")
            if st.button("⚡ Cargar lista base de insumos (Comestibles + Cajas + Bolsas)", use_container_width=True):
                plantilla_inicial = [
                    {"nombre": "Harina 000 (Bolsa 25kg)", "modo": "kg", "precio_bulto": 18000, "cantidad_bulto": 25, "uso_muzza": 300, "uso_huevo": 300, "uso_tomate": 300},
                    {"nombre": "Muzzarella", "modo": "kg", "precio_bulto": 8500, "cantidad_bulto": 1, "uso_muzza": 250, "uso_huevo": 250, "uso_tomate": 250},
                    {"nombre": "Salsa de Tomate", "modo": "kg", "precio_bulto": 2500, "cantidad_bulto": 1, "uso_muzza": 120, "uso_huevo": 120, "uso_tomate": 120},
                    {"nombre": "Huevo (Maple x 30 u.)", "modo": "unidad", "precio_bulto": 6000, "cantidad_bulto": 30, "uso_muzza": 0, "uso_huevo": 2, "uso_tomate": 0},
                    {"nombre": "Tomate fresco", "modo": "kg", "precio_bulto": 3000, "cantidad_bulto": 1, "uso_muzza": 0, "uso_huevo": 0, "uso_tomate": 150},
                    {"nombre": "Caja de Pizza", "modo": "unidad", "precio_bulto": 35000, "cantidad_bulto": 100, "uso_muzza": 1, "uso_huevo": 1, "uso_tomate": 1},
                    {"nombre": "Bolsa / Packaging", "modo": "unidad", "precio_bulto": 5000, "cantidad_bulto": 100, "uso_muzza": 1, "uso_huevo": 1, "uso_tomate": 1},
                ]
                supabase.table("pizzas_insumos").insert(plantilla_inicial).execute()
                st.success("✅ Lista base cargada. Abajo podés editar todos los precios y cantidades o borrar lo que no uses.")
                st.rerun()

    # Contenedor reactivo (fuera de st.form para que cambie en vivo entre Kilo y Unidad)
    with st.container(border=True):
        st.markdown("#### 📝 Cargar un Nuevo Insumo")
        ci1, ci2 = st.columns([2, 2])
        with ci1:
            ins_nombre = st.text_input(
                "Nombre del Insumo *",
                placeholder="Ej: Muzzarella, Harina, Bolsa camiseta, Caja...",
                key="input_nuevo_ins_nombre"
            )
        with ci2:
            ins_modo = st.selectbox(
                "¿Cómo se compra y calcula?",
                options=["kg", "unidad"],
                format_func=lambda x: (
                    "⚖️ Por Kilo / Bulto en Kg (Harina, Muzza, Salsa...)"
                    if x == "kg"
                    else "📦 Por Unidad / Pack (Cajas, Bolsas, Huevos...)"
                ),
                key="input_nuevo_ins_modo"
            )

        es_nuevo_kg = (ins_modo == "kg")
        ci3, ci4 = st.columns(2)
        with ci3:
            ins_precio_bulto = st.number_input(
                "💵 Precio pagado por el Bulto / Pack / Kilo ($)",
                min_value=0.0,
                step=500.0,
                value=0.0,
                key="input_nuevo_ins_precio"
            )
        with ci4:
            ins_cant_bulto = st.number_input(
                "⚖️ Kilos que trae el bulto (1 = 1 kg)" if es_nuevo_kg else "📦 Unidades que trae el pack (1 = 1 unidad)",
                min_value=0.01,
                step=1.0,
                value=1.0,
                help="Ej: Si es 1 kg suelto poné 1. Si es bolsa de 25kg poné 25. Si es un pack de 100 bolsas poné 100.",
                key="input_nuevo_ins_cant"
            )

        costo_unit_preview = ins_precio_bulto / ins_cant_bulto if ins_cant_bulto > 0 else 0.0
        unidad_preview_txt = "Kilo" if es_nuevo_kg else "Unidad"
        st.caption(f"💡 Costo calculado: **${costo_unit_preview:,.2f} por cada {unidad_preview_txt}**")

        if es_nuevo_kg:
            st.markdown("**¿Cuántos GRAMOS lleva 1 pizza de cada estilo?** *(Ej: `250` para 250 gramos)*")
        else:
            st.markdown("**¿Cuántas UNIDADES lleva 1 pizza de cada estilo?** *(Ej: `1` bolsa, `1` caja, `2` huevos)*")

        usos_nuevo_ins = {}
        cols_uso_nuevo = st.columns(3, vertical_alignment="bottom")
        for idx, var in enumerate(catalogo_pizzas):
            with cols_uso_nuevo[idx % 3]:
                sufijo_u = "g" if es_nuevo_kg else "unid."
                usos_nuevo_ins[var["slug"]] = st.number_input(
                    f"{var['emoji']} {var['nombre']} ({sufijo_u})",
                    min_value=0.0,
                    step=10.0 if es_nuevo_kg else 1.0,
                    value=0.0,
                    key=f"nuevo_uso_{var['slug']}"
                )

        if st.button("💾 Agregar Insumo a la Lista", type="primary", use_container_width=True):
            if not ins_nombre.strip():
                st.warning("⚠️ Escribí el nombre del insumo arriba antes de guardar.")
            else:
                usos_extra_dict = {
                    k: v for k, v in usos_nuevo_ins.items()
                    if k not in ("muzza", "huevo", "tomate") and v > 0
                }
                modo_guardar = empaquetar_modo_insumo(ins_modo, usos_extra_dict)
                supabase.table("pizzas_insumos").insert({
                    "nombre": ins_nombre.strip(),
                    "modo": modo_guardar,
                    "precio_bulto": float(ins_precio_bulto),
                    "cantidad_bulto": float(ins_cant_bulto),
                    "uso_muzza": float(usos_nuevo_ins.get("muzza", 0.0)),
                    "uso_huevo": float(usos_nuevo_ins.get("huevo", 0.0)),
                    "uso_tomate": float(usos_nuevo_ins.get("tomate", 0.0)),
                }).execute()
                st.success(f"✅ Insumo '{ins_nombre.strip()}' guardado.")
                st.rerun()

    st.divider()

    # Listado editable y visible de insumos cargados
    st.subheader(f"📋 Insumos Cargados ({len(insumos)}) — Editar o Borrar")
    if insumos:
        st.caption("Modificá cualquier nombre, precio o cantidad y tocá **💾 Guardar Cambios**, o tocá **🗑️ Borrar** para quitarlo.")
        for ins, det in zip(insumos, costos_pizza["detalle"]):
            es_kg = det["modo_base"] == "kg"
            unidad_txt = "kg" if es_kg else "unid."
            resumen_costos_var = " · ".join(
                f"{v['emoji']} {v['nombre']}: **\\${det['costos_variedad'].get(v['slug'], 0):,.0f}**"
                for v in catalogo_pizzas
            )

            with st.container(border=True):
                st.markdown(f"##### 🔧 {ins['nombre']}  *(Costo: \\${det['Costo x Kg/Unid']:,.2f} / {unidad_txt})*")
                st.markdown(f"Costo que suma por pizza: {resumen_costos_var}")

                ec0, ec1, ec2, ec3 = st.columns([2, 2, 2, 2], vertical_alignment="bottom")
                with ec0:
                    ed_nombre = st.text_input(
                        "Nombre",
                        value=ins["nombre"],
                        key=f"nom_{ins['id']}"
                    )
                with ec1:
                    ed_modo = st.selectbox(
                        "Modo",
                        options=["kg", "unidad"],
                        index=0 if es_kg else 1,
                        format_func=lambda x: "⚖️ Por Kg (uso en g)" if x == "kg" else "📦 Por Unidad/Pack",
                        key=f"modo_{ins['id']}"
                    )
                with ec2:
                    ed_precio = st.number_input(
                        "Precio Bulto/Kg ($)",
                        min_value=0.0,
                        value=float(ins.get("precio_bulto") or 0),
                        step=500.0,
                        key=f"prec_{ins['id']}"
                    )
                with ec3:
                    ed_cant = st.number_input(
                        "Cant. del bulto",
                        min_value=0.01,
                        value=float(ins.get("cantidad_bulto") or 1),
                        step=1.0,
                        key=f"cant_{ins['id']}"
                    )

                es_ed_kg = (ed_modo == "kg")
                uso_ed_label = "g" if es_ed_kg else "unid."
                ed_usos = {}
                cols_ed_u = st.columns(3, vertical_alignment="bottom")
                for idx, var in enumerate(catalogo_pizzas):
                    slug = var["slug"]
                    with cols_ed_u[idx % 3]:
                        ed_usos[slug] = st.number_input(
                            f"{var['emoji']} {var['nombre']} ({uso_ed_label})",
                            min_value=0.0,
                            value=float(det["usos_variedad"].get(slug, 0.0)),
                            step=10.0 if es_ed_kg else 1.0,
                            key=f"u_{slug}_{ins['id']}"
                        )

                eb1, eb2 = st.columns([3, 1])
                with eb1:
                    if st.button("💾 Guardar Cambios", key=f"save_ins_{ins['id']}", type="primary", use_container_width=True):
                        extras_ed = {
                            k: v for k, v in ed_usos.items()
                            if k not in ("muzza", "huevo", "tomate") and v > 0
                        }
                        modo_ed_empaquetado = empaquetar_modo_insumo(ed_modo, extras_ed)
                        supabase.table("pizzas_insumos").update({
                            "nombre": ed_nombre.strip() or ins["nombre"],
                            "modo": modo_ed_empaquetado,
                            "precio_bulto": float(ed_precio),
                            "cantidad_bulto": float(ed_cant),
                            "uso_muzza": float(ed_usos.get("muzza", 0.0)),
                            "uso_huevo": float(ed_usos.get("huevo", 0.0)),
                            "uso_tomate": float(ed_usos.get("tomate", 0.0))
                        }).eq("id", ins["id"]).execute()
                        st.success(f"✅ '{ed_nombre}' actualizado.")
                        st.rerun()
                with eb2:
                    if st.button("🗑️ Borrar", key=f"del_ins_{ins['id']}", use_container_width=True):
                        supabase.table("pizzas_insumos").delete().eq("id", ins["id"]).execute()
                        st.rerun()
    else:
        st.info("Todavía no hay insumos cargados. Usá el botón rápido de arriba o completá el cuadro '📝 Cargar un Nuevo Insumo'.")


# =========================================================
# PESTAÑA 3: CAJA / DÍA (PRODUCCIÓN, WHATSAPP Y COMANDAS)
# =========================================================
with tab_caja:
    st.subheader("📊 Producción y Caja del Día")

    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        fecha_filtro = st.date_input("📅 Fecha a consultar", value=date.today(), key="fecha_caja")
    with col_f2:
        filtro_estado = st.selectbox(
            "Filtrar pedidos",
            options=["Todos", "Pendientes de entrega", "Pendientes de cobro", "Entregados", "Cancelados"]
        )

    res_pedidos = (
        supabase.table("pizzas_pedidos")
        .select("*")
        .eq("fecha", str(fecha_filtro))
        .order("created_at", desc=True)
        .execute()
    )
    pedidos_dia = res_pedidos.data or []

    # Cálculos dinámicos de producción por cada variedad del catálogo (excluyendo cancelados)
    totales_por_estilo = {v["slug"]: 0 for v in catalogo_pizzas}
    pendientes_por_estilo = {v["slug"]: 0 for v in catalogo_pizzas}
    pedidos_activos = []

    for p in pedidos_dia:
        est_limpio, _ = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))
        if est_limpio == "cancelado":
            continue
        pedidos_activos.append(p)
        for v in catalogo_pizzas:
            slug = v["slug"]
            c_var = obtener_cantidad_pedido_variedad(p, slug)
            totales_por_estilo[slug] += c_var
            if est_limpio != "entregado":
                pendientes_por_estilo[slug] += c_var

    tot_pizzas = sum(totales_por_estilo.values())
    pend_pizzas = sum(pendientes_por_estilo.values())

    plata_total = sum(float(p.get("total_plata") or 0) for p in pedidos_activos)
    plata_efectivo = sum(float(p.get("total_plata") or 0) for p in pedidos_activos if p.get("metodo_pago") == "efectivo")
    plata_transf = sum(float(p.get("total_plata") or 0) for p in pedidos_activos if p.get("metodo_pago") == "transferencia")
    plata_pendiente = sum(float(p.get("total_plata") or 0) for p in pedidos_activos if p.get("metodo_pago") == "pendiente")

    costo_mercaderia_dia = sum(
        totales_por_estilo[v["slug"]] * costos_pizza["por_variedad"].get(v["slug"], 0.0)
        for v in catalogo_pizzas
    )
    ganancia_neta_dia = plata_total - costo_mercaderia_dia

    # --- BLOQUE 1: QUÉ HAY QUE HORNEAR + BOTÓN WHATSAPP DEL DÍA ---
    st.markdown("##### 🔥 Resumen de Horneado / Producción")
    st.metric("🍕 Total Pizzas del Día", f"{tot_pizzas} pizzas", f"{pend_pizzas} pendientes de entregar")

    cols_prod = st.columns(3)
    for idx, var in enumerate(catalogo_pizzas):
        slug = var["slug"]
        with cols_prod[idx % 3]:
            st.metric(
                f"{var['emoji']} {var['nombre']}",
                f"{totales_por_estilo[slug]}",
                f"{pendientes_por_estilo[slug]} pendientes"
            )

    # --- BOTÓN PARA ENVIAR RESUMEN DE PIZZAS Y CAJA DEL DÍA POR WHATSAPP ---
    with st.container(border=True):
        st.markdown("##### 📲 Enviar Pedidos del Día y Resumen de Caja por WhatsApp")
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            wa_solo_pend = st.checkbox("Solo pizzas pendientes", value=False)
        with w_col2:
            wa_inc_clientes = st.checkbox("Incluir lista de clientes", value=True)
        with w_col3:
            wa_inc_caja = st.checkbox("Incluir resumen de caja ($)", value=True)

        wa_tel_destino = st.text_input(
            "N° de WhatsApp destino (opcional — dejalo vacío para elegir el chat al abrir WhatsApp):",
            placeholder="Ej: 11 2345-6789"
        )

        texto_wa_dia = armar_mensaje_produccion_whatsapp(
            fecha_obj=fecha_filtro,
            catalogo=catalogo_pizzas,
            totales_estilo=totales_por_estilo,
            pendientes_estilo=pendientes_por_estilo,
            pedidos_lista=pedidos_activos,
            solo_pendientes=wa_solo_pend,
            incluir_clientes=wa_inc_clientes,
            incluir_caja=wa_inc_caja,
            datos_caja={
                "total": plata_total,
                "efectivo": plata_efectivo,
                "transferencia": plata_transf,
                "pendiente": plata_pendiente,
                "ganancia": ganancia_neta_dia,
            }
        )

        num_limpio = re.sub(r"\D", "", wa_tel_destino)
        if num_limpio and not num_limpio.startswith("54"):
            num_limpio = "549" + num_limpio.lstrip("0")

        url_wa_resumen = (
            f"https://wa.me/{num_limpio}?text={quote(texto_wa_dia)}"
            if num_limpio
            else f"https://wa.me/?text={quote(texto_wa_dia)}"
        )

        st.link_button(
            f"📲 Enviar Resumen del Día ({fecha_filtro.strftime('%d/%m')}) por WhatsApp",
            url_wa_resumen,
            type="primary",
            use_container_width=True
        )
        with st.expander("👁️ Ver vista previa del mensaje de WhatsApp"):
            st.code(texto_wa_dia, language=None)

    # Desplegable con insumos totales necesarios para los pedidos del día
    if insumos and tot_pizzas > 0:
        with st.expander("🧺 Ver mercadería necesaria para los pedidos de este día"):
            filas_merc = []
            for ins, det in zip(insumos, costos_pizza["detalle"]):
                es_kg = det["modo_base"] == "kg"
                total_uso = sum(
                    totales_por_estilo[v["slug"]] * det["usos_variedad"].get(v["slug"], 0.0)
                    for v in catalogo_pizzas
                )
                if total_uso > 0:
                    if es_kg:
                        cant_legible = f"{total_uso:,.0f} g ({total_uso/1000:.2f} kg)"
                    else:
                        cant_legible = f"{total_uso:,.1f} unidades"
                    filas_merc.append({"Insumo": ins["nombre"], "Cantidad Total Necesaria": cant_legible})
            if filas_merc:
                st.dataframe(pd.DataFrame(filas_merc), use_container_width=True, hide_index=True)

    # --- BLOQUE 2: RESUMEN DE CAJA ---
    st.markdown("##### 💵 Resumen de Caja")
    cj1, cj2, cj3, cj4 = st.columns(4)
    with cj1:
        st.metric("💰 Venta Total", f"${plata_total:,.0f}", f"{len(pedidos_activos)} pedidos activos")
    with cj2:
        st.metric("🏦 Transferencia", f"${plata_transf:,.0f}")
    with cj3:
        st.metric("💵 Efectivo", f"${plata_efectivo:,.0f}")
    with cj4:
        st.metric("⏳ Falta Cobrar", f"${plata_pendiente:,.0f}", f"Ganancia est.: ${ganancia_neta_dia:,.0f}")

    st.divider()

    # --- BLOQUE 3: LISTADO DE PEDIDOS (CIERRE DE VENTAS) ---
    st.markdown("##### 📋 Comandas y Cierre de Ventas del Día")
    st.caption("💡 Cambiá el **Estado de Entrega** o el **Método de Pago** en cualquier tarjeta y **se guarda solo al instante**, actualizando la Caja arriba.")

    pedidos_mostrar = []
    for p in pedidos_dia:
        est_limpio, _ = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))
        if filtro_estado == "Pendientes de entrega" and est_limpio != "pendiente":
            continue
        if filtro_estado == "Pendientes de cobro" and (p.get("metodo_pago") != "pendiente" or est_limpio == "cancelado"):
            continue
        if filtro_estado == "Entregados" and est_limpio != "entregado":
            continue
        if filtro_estado == "Cancelados" and est_limpio != "cancelado":
            continue
        pedidos_mostrar.append(p)

    if not pedidos_mostrar:
        st.info("No hay pedidos para mostrar con este filtro.")
    else:
        for p in pedidos_mostrar:
            est_actual, extras_actuales = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))

            partes_pizza = []
            for v in catalogo_pizzas:
                c_v = obtener_cantidad_pedido_variedad(p, v["slug"])
                if c_v > 0:
                    partes_pizza.append(f"**{c_v}** {v['nombre']}")

            resumen_pizzas_txt = " · ".join(partes_pizza) if partes_pizza else "Sin pizzas"
            resumen_plano = ", ".join([s.replace("**", "") for s in partes_pizza])

            etiquetas_est = {
                "pendiente": "🕒 Pendiente",
                "entregado": "✅ Entregado",
                "cancelado": "❌ Cancelado / No había nadie"
            }
            etiquetas_pago = {
                "transferencia": "🏦 Transferencia",
                "efectivo": "💵 Efectivo",
                "pendiente": "⏳ Pendiente"
            }
            icono_est = {"pendiente": "🕒", "entregado": "✅", "cancelado": "❌"}.get(est_actual, "🕒")
            icono_pago = {"transferencia": "🏦", "efectivo": "💵", "pendiente": "⏳"}.get(p.get("metodo_pago"), "⏳")

            with st.container(border=True):
                top1, top2 = st.columns([3, 2])
                with top1:
                    st.markdown(f"#### {icono_est} {p['nombre_cliente']}")
                    st.markdown(f"🍕 {resumen_pizzas_txt}")
                    info_dir_tel = []
                    if p.get("direccion"):
                        info_dir_tel.append(f"📍 {p['direccion']}")
                    if p.get("telefono"):
                        info_dir_tel.append(f"📞 {p['telefono']}")
                    if info_dir_tel:
                        st.caption(" · ".join(info_dir_tel))
                with top2:
                    st.markdown(f"#### 💲 ${float(p.get('total_plata') or 0):,.0f}")
                    st.caption(f"Pago: {icono_pago} **{str(p.get('metodo_pago', 'pendiente')).capitalize()}**")
                    url_wa = link_whatsapp_cliente(
                        p.get("telefono") or "",
                        p["nombre_cliente"],
                        resumen_plano,
                        float(p.get("total_plata") or 0)
                    )
                    if url_wa:
                        st.link_button("📲 WhatsApp al Cliente", url_wa, use_container_width=True)

                b1, b2, b3 = st.columns([2, 2, 1], vertical_alignment="bottom")
                estados_opc = ["pendiente", "entregado", "cancelado"]
                pagos_opc = ["transferencia", "efectivo", "pendiente"]

                if est_actual not in estados_opc:
                    est_actual = "pendiente"
                pago_actual = p.get("metodo_pago") if p.get("metodo_pago") in pagos_opc else "transferencia"

                with b1:
                    nuevo_est = st.selectbox(
                        "Estado de Entrega",
                        options=estados_opc,
                        index=estados_opc.index(est_actual),
                        format_func=lambda x: etiquetas_est.get(x, x.capitalize()),
                        key=f"est_ped_{p['id']}"
                    )
                with b2:
                    nuevo_pago = st.selectbox(
                        "Método de Pago",
                        options=pagos_opc,
                        index=pagos_opc.index(pago_actual),
                        format_func=lambda x: etiquetas_pago.get(x, x.capitalize()),
                        key=f"pago_ped_{p['id']}"
                    )
                with b3:
                    if st.button("🗑️", key=f"del_ped_{p['id']}", help="Eliminar pedido definitivamente", use_container_width=True):
                        supabase.table("pizzas_pedidos").delete().eq("id", p["id"]).execute()
                        st.rerun()

                if nuevo_est != est_actual or nuevo_pago != pago_actual:
                    nuevo_estado_empaquetado = empaquetar_estado_y_extras_pedido(nuevo_est, extras_actuales)
                    supabase.table("pizzas_pedidos").update({
                        "estado_entrega": nuevo_estado_empaquetado,
                        "metodo_pago": nuevo_pago
                    }).eq("id", p["id"]).execute()
                    st.rerun()