import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date, datetime
import json
import os
import re
import uuid
import logging
from urllib.parse import quote
import html

# --- 1. CONFIGURACIÓN PRINCIPAL Y SEGURIDAD ---
st.set_page_config(
    page_title="Pizzas Martina · Gestión & Comandas",
    page_icon="🍕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PizzasMartina")

# --- ESTÉTICA PREMIUM DARK GASTRO UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #0B0D13;
        --bg-card: #141824;
        --bg-card-hover: #1A2030;
        --brand-orange: #FF6B00;
        --brand-red: #FF3D00;
        --brand-amber: #F59E0B;
        --emerald: #10B981;
        --sky: #0EA5E9;
        --rose: #EF4444;
        --text-main: #F8FAFC;
        --text-muted: #94A3B8;
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-glow: rgba(255, 107, 0, 0.45);
    }

    /* Fondo general con atmósfera cálida de horno */
    .stApp {
        background:
            radial-gradient(circle at 12% 5%, rgba(255, 107, 0, 0.11), transparent 38%),
            radial-gradient(circle at 88% 12%, rgba(239, 68, 68, 0.08), transparent 35%),
            linear-gradient(180deg, #0B0D13 0%, #0E1118 100%) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-main);
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* Limpiar barra superior de Streamlit */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 4rem !important;
        max-width: 880px !important;
    }

    /* Hero Banner Principal */
    .pm-hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(28, 32, 46, 0.92) 0%, rgba(18, 21, 31, 0.96) 100%);
        border: 1px solid rgba(255, 107, 0, 0.28);
        border-radius: 22px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 16px 40px -12px rgba(0, 0, 0, 0.65), 0 0 28px -8px rgba(255, 107, 0, 0.2);
    }
    .pm-hero::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 240px;
        height: 240px;
        background: radial-gradient(circle, rgba(255, 107, 0, 0.22) 0%, transparent 70%);
        pointer-events: none;
    }
    .pm-hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        flex-wrap: wrap;
    }
    .pm-brand {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .pm-logo-badge {
        width: 56px;
        height: 56px;
        border-radius: 16px;
        background: linear-gradient(135deg, #FF6B00 0%, #DC2626 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        box-shadow: 0 8px 20px rgba(255, 107, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.35);
        flex-shrink: 0;
    }
    .pm-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
        background: linear-gradient(90deg, #FFFFFF 0%, #FED7AA 60%, #FF6B00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .pm-subtitle {
        color: #94A3B8;
        font-size: 0.85rem;
        margin-top: 4px;
        font-weight: 500;
    }
    .pm-badges-row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .pm-pill-live {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34D399;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 5px 11px;
        border-radius: 999px;
    }
    .pm-dot-live {
        width: 7px;
        height: 7px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
    }
    .pm-pill-date {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #E2E8F0;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 5px 11px;
        border-radius: 999px;
    }

    /* Pestañas estilo Segmented Control / App Móvil */
    div[data-baseweb="tab-list"] {
        background: rgba(20, 24, 36, 0.9) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 6px !important;
        gap: 6px !important;
        margin-bottom: 18px !important;
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.5);
        overflow-x: auto;
    }
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
    }
    button[data-baseweb="tab"] {
        border-radius: 11px !important;
        padding: 10px 14px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        color: #94A3B8 !important;
        background: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
        flex: 1 1 auto !important;
        justify-content: center !important;
        white-space: nowrap !important;
    }
    button[data-baseweb="tab"]:focus,
    button[data-baseweb="tab"]:focus-visible,
    button[data-baseweb="tab"]:active {
        outline: none !important;
        border: none !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #F8FAFC !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #FF6B00 0%, #EA580C 55%, #DC2626 100%) !important;
        color: #FFFFFF !important;
        outline: none !important;
        border: none !important;
        box-shadow: 0 6px 16px -3px rgba(255, 107, 0, 0.5) !important;
        transform: translateY(-1px);
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Contenedores con borde (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, rgba(22, 27, 40, 0.92) 0%, rgba(16, 20, 30, 0.95) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 18px !important;
        padding: 16px !important;
        box-shadow: 0 10px 26px -10px rgba(0, 0, 0, 0.55) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(255, 107, 0, 0.28) !important;
    }

    /* Botones Principales y Secundarios */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"],
    a[data-testid="stBaseLinkButton-primary"] {
        background: linear-gradient(135deg, #FF6B00 0%, #EA580C 50%, #DC2626 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 13px !important;
        padding: 0.65rem 1.2rem !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 8px 20px -6px rgba(255, 107, 0, 0.55) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover,
    a[data-testid="stBaseLinkButton-primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 12px 24px -6px rgba(255, 107, 0, 0.75) !important;
        filter: brightness(1.06);
    }

    .stButton > button[kind="secondary"],
    .stFormSubmitButton > button[kind="secondary"],
    a[data-testid="stBaseLinkButton-secondary"],
    div[data-testid="stPopover"] > div > button {
        background: rgba(30, 36, 52, 0.85) !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 11px !important;
        font-weight: 600 !important;
        transition: all 0.18s ease !important;
    }
    .stButton > button[kind="secondary"]:hover,
    a[data-testid="stBaseLinkButton-secondary"]:hover,
    div[data-testid="stPopover"] > div > button:hover {
        border-color: #FF6B00 !important;
        color: #FFFFFF !important;
        background: rgba(255, 107, 0, 0.12) !important;
    }

    /* Inputs, Number Inputs y Selectboxes más modernos */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #111520 !important;
        border: 1px solid rgba(255, 255, 255, 0.11) !important;
        border-radius: 11px !important;
        transition: all 0.18s ease !important;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #FF6B00 !important;
        box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.18) !important;
    }

    /* Botones + y - de st.number_input más grandes y cómodos para celular */
    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"] {
        background: rgba(255, 107, 0, 0.12) !important;
        color: #FF8533 !important;
        border-radius: 8px !important;
        width: 34px !important;
        height: 30px !important;
        margin: 2px !important;
        transition: all 0.15s ease !important;
    }
    button[data-testid="stNumberInputStepUp"]:hover,
    button[data-testid="stNumberInputStepDown"]:hover {
        background: #FF6B00 !important;
        color: #FFFFFF !important;
    }

    /* Tarjetas del Catálogo de Pizzas (en Pedidos y Simulador) */
    .pm-pizza-card {
        background: linear-gradient(145deg, #171C2B 0%, #111521 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 12px 14px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .pm-pizza-card.active {
        background: linear-gradient(145deg, rgba(255, 107, 0, 0.16) 0%, rgba(23, 28, 43, 0.95) 100%);
        border: 1px solid rgba(255, 107, 0, 0.65);
        box-shadow: 0 6px 20px -6px rgba(255, 107, 0, 0.35);
    }
    .pm-pizza-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pm-pizza-emoji {
        width: 40px;
        height: 40px;
        border-radius: 11px;
        background: rgba(255, 107, 0, 0.12);
        border: 1px solid rgba(255, 107, 0, 0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        flex-shrink: 0;
    }
    .pm-pizza-name {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 0.98rem;
        color: #F8FAFC;
        line-height: 1.15;
    }
    .pm-pizza-price {
        font-size: 0.82rem;
        font-weight: 700;
        color: #FF8533;
        margin-top: 2px;
    }
    .pm-pizza-badge-qty {
        background: linear-gradient(135deg, #FF6B00, #EA580C);
        color: #FFF;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 3px 10px;
        border-radius: 999px;
        box-shadow: 0 4px 10px rgba(255, 107, 0, 0.4);
    }

    /* Ticket Digital de Resumen de Pedido */
    .pm-ticket {
        background: linear-gradient(135deg, rgba(20, 26, 40, 0.96) 0%, rgba(14, 18, 28, 0.98) 100%);
        border: 1px solid rgba(255, 107, 0, 0.38);
        border-left: 5px solid #FF6B00;
        border-radius: 16px;
        padding: 16px 20px;
        margin: 14px 0 18px 0;
        box-shadow: 0 12px 28px -10px rgba(0, 0, 0, 0.6);
    }
    .pm-ticket-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
    }
    .pm-ticket-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pm-ticket-total {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.5rem;
        color: #FF8533;
    }
    .pm-ticket-items {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 6px;
    }
    .pm-ticket-chip {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #E2E8F0;
        font-size: 0.83rem;
        font-weight: 600;
        padding: 4px 11px;
        border-radius: 8px;
    }
    .pm-ticket-saving {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34D399;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
        margin-top: 10px;
    }

    /* Tarjetas de Comanda (Cocina y Pedidos del Día) */
    .pm-comanda-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding-bottom: 12px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        flex-wrap: wrap;
    }
    .pm-comanda-client {
        font-family: 'Outfit', sans-serif;
        font-size: 1.22rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0 0 6px 0;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .pm-comanda-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        font-size: 0.82rem;
        color: #94A3B8;
        margin-top: 6px;
    }
    .pm-comanda-meta span {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(255, 255, 255, 0.04);
        padding: 3px 9px;
        border-radius: 7px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .pm-pizza-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin: 8px 0 4px 0;
    }
    .pm-pizza-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(255, 107, 0, 0.14);
        border: 1px solid rgba(255, 107, 0, 0.35);
        color: #FFEDD5;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        padding: 4px 11px;
        border-radius: 9px;
    }
    .pm-comanda-price-box {
        text-align: right;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 5px;
    }
    .pm-comanda-price {
        font-family: 'Outfit', sans-serif;
        font-size: 1.4rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.1;
    }

    /* Badges de estado y pago */
    .pm-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 4px 10px;
        border-radius: 999px;
    }
    .pm-badge-pendiente {
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(245, 158, 11, 0.45);
        color: #FBBF24;
    }
    .pm-badge-entregado {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(16, 185, 129, 0.45);
        color: #34D399;
    }
    .pm-badge-cancelado {
        background: rgba(239, 68, 68, 0.16);
        border: 1px solid rgba(239, 68, 68, 0.45);
        color: #F87171;
    }
    .pm-badge-pago-ok {
        background: rgba(14, 165, 233, 0.15);
        border: 1px solid rgba(14, 165, 233, 0.4);
        color: #38BDF8;
    }
    .pm-badge-pago-efec {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34D399;
    }
    .pm-badge-pago-debe {
        background: rgba(249, 115, 22, 0.18);
        border: 1px solid rgba(249, 115, 22, 0.45);
        color: #FB923C;
    }

    /* Tarjetas de KPIs y Producción */
    .pm-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
        gap: 12px;
        margin: 10px 0 18px 0;
    }
    .pm-kpi-card {
        background: linear-gradient(160deg, #171C2B 0%, #111520 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 15px 16px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.5);
    }
    .pm-kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--kpi-accent, #FF6B00);
    }
    .pm-kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
    }
    .pm-kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 1.55rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.15;
    }
    .pm-kpi-sub {
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 6px;
        color: var(--kpi-sub-color, #34D399);
    }

    /* Monitor de Horno / Producción */
    .pm-oven-banner {
        background: linear-gradient(135deg, rgba(255, 107, 0, 0.14) 0%, rgba(22, 27, 40, 0.95) 65%);
        border: 1px solid rgba(255, 107, 0, 0.35);
        border-radius: 18px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }
    .pm-progress-track {
        width: 100%;
        height: 9px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        overflow: hidden;
        margin-top: 10px;
    }
    .pm-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #FF6B00, #10B981);
        border-radius: 999px;
        transition: width 0.35s ease;
    }

    /* stMetric nativos mejorados por si se usan */
    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, #171C2B 0%, #111520 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        padding: 14px 16px !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.45) !important;
    }

    /* Separadores elegantes */
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
        margin: 1.5rem 0 !important;
    }

    /* Títulos de sección personalizados */
    .pm-sec-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 6px 0 12px 0;
    }
    .pm-sec-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }
    .pm-sec-sub {
        font-size: 0.84rem;
        color: #94A3B8;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR HÍBRIDO DE DATOS (SUPABASE CLOUD + FALLBACK LOCAL AUTOMÁTICO) ---
LOCAL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_locales.json")

def _crear_semilla_local() -> dict:
    """Crea una base de datos local inicial con insumos, clientes y pedidos de muestra."""
    hoy_str = str(date.today())
    ahora_iso = datetime.now().isoformat()
    return {
        "pizzas_clientes": [
            {"id": 101, "nombre": "Lucas Gómez", "telefono": "3573 40-2784", "direccion": "Belgrano 1230", "created_at": ahora_iso},
            {"id": 102, "nombre": "Mariana Sosa", "telefono": "3573 45-9912", "direccion": "San Martín 450 (Portón Negro)", "created_at": ahora_iso},
            {"id": 103, "nombre": "Familia Peralta", "telefono": "3573 51-8200", "direccion": "Av. Libertad 890", "created_at": ahora_iso},
            {"id": 104, "nombre": "Sofi (Retira x local)", "telefono": "3573 60-1123", "direccion": "Retira en mostrador", "created_at": ahora_iso},
        ],
        "pizzas_insumos": [
            {"id": 201, "nombre": "Harina 000 (Bolsa 25kg)", "modo": "kg", "precio_bulto": 18500, "cantidad_bulto": 25, "uso_muzza": 300, "uso_huevo": 300, "uso_tomate": 300, "created_at": "2026-10-01T10:00:00"},
            {"id": 202, "nombre": "Muzzarella Cilindro", "modo": "kg", "precio_bulto": 8800, "cantidad_bulto": 1, "uso_muzza": 250, "uso_huevo": 250, "uso_tomate": 250, "created_at": "2026-10-01T10:01:00"},
            {"id": 203, "nombre": "Salsa de Tomate Condimentada", "modo": "kg", "precio_bulto": 2600, "cantidad_bulto": 1, "uso_muzza": 120, "uso_huevo": 120, "uso_tomate": 120, "created_at": "2026-10-01T10:02:00"},
            {"id": 204, "nombre": "Huevo (Maple x 30 u.)", "modo": "unidad", "precio_bulto": 6000, "cantidad_bulto": 30, "uso_muzza": 0, "uso_huevo": 2, "uso_tomate": 0, "created_at": "2026-10-01T10:03:00"},
            {"id": 205, "nombre": "Tomate Fresco", "modo": "kg", "precio_bulto": 3200, "cantidad_bulto": 1, "uso_muzza": 0, "uso_huevo": 0, "uso_tomate": 150, "created_at": "2026-10-01T10:04:00"},
            {"id": 206, "nombre": "Caja de Pizza Reforzada", "modo": "unidad", "precio_bulto": 36000, "cantidad_bulto": 100, "uso_muzza": 1, "uso_huevo": 1, "uso_tomate": 1, "created_at": "2026-10-01T10:05:00"},
            {"id": 207, "nombre": "Bolsa / Separadores", "modo": "unidad", "precio_bulto": 5500, "cantidad_bulto": 100, "uso_muzza": 1, "uso_huevo": 1, "uso_tomate": 1, "created_at": "2026-10-01T10:06:00"},
        ],
        "pizzas_pedidos": [
            {
                "id": 301,
                "fecha": hoy_str,
                "nombre_cliente": "Mariana Sosa",
                "telefono": "3573 45-9912",
                "direccion": "San Martín 450 (Portón Negro)",
                "cant_muzza": 2,
                "cant_huevo": 0,
                "cant_tomate": 0,
                "total_plata": 13000.0,
                "estado_entrega": "entregado",
                "metodo_pago": "transferencia",
                "created_at": "2026-10-30T20:15:00"
            },
            {
                "id": 302,
                "fecha": hoy_str,
                "nombre_cliente": "Lucas Gómez",
                "telefono": "3573 40-2784",
                "direccion": "Belgrano 1230",
                "cant_muzza": 1,
                "cant_huevo": 1,
                "cant_tomate": 1,
                "total_plata": 22500.0,
                "estado_entrega": "pendiente",
                "metodo_pago": "efectivo",
                "created_at": "2026-10-30T20:45:00"
            },
            {
                "id": 303,
                "fecha": hoy_str,
                "nombre_cliente": "Familia Peralta",
                "telefono": "3573 51-8200",
                "direccion": "Av. Libertad 890",
                "cant_muzza": 0,
                "cant_huevo": 2,
                "cant_tomate": 0,
                "total_plata": 15000.0,
                "estado_entrega": "pendiente",
                "metodo_pago": "pendiente",
                "created_at": "2026-10-30T21:10:00"
            }
        ]
    }

def _leer_db_local() -> dict:
    if not os.path.exists(LOCAL_DB_FILE):
        semilla = _crear_semilla_local()
        try:
            with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(semilla, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return semilla
    try:
        with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _crear_semilla_local()

def _guardar_db_local(data: dict):
    try:
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as err:
        logger.warning("No se pudo escribir datos_locales.json: %s", str(err))

class _LocalResp:
    def __init__(self, data):
        self.data = data

class _HybridTableQuery:
    def __init__(self, real_client, table_name: str, status_tracker: dict):
        self.real_client = real_client
        self.table_name = table_name
        self.status_tracker = status_tracker
        self._op = "select"
        self._payload = None
        self._filters = []
        self._order_col = None
        self._order_desc = False

    def select(self, *_args, **_kwargs):
        self._op = "select"
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def delete(self):
        self._op = "delete"
        return self

    def eq(self, col: str, val):
        self._filters.append((col, val))
        return self

    def order(self, col: str, desc: bool = False):
        self._order_col = col
        self._order_desc = desc
        return self

    def _ejecutar_en_local(self):
        db = _leer_db_local()
        filas = list(db.get(self.table_name, []))

        if self._op == "select":
            for k, v in self._filters:
                filas = [r for r in filas if str(r.get(k)) == str(v)]
            if self._order_col:
                filas.sort(key=lambda r: str(r.get(self._order_col) or ""), reverse=self._order_desc)
            return _LocalResp(filas)

        elif self._op == "insert":
            items = self._payload if isinstance(self._payload, list) else [self._payload]
            max_id = max([int(r.get("id", 0)) for r in filas if str(r.get("id", "")).isdigit()] + [400])
            nuevos = []
            for idx, it in enumerate(items, start=1):
                nuevo = dict(it)
                if "id" not in nuevo:
                    nuevo["id"] = max_id + idx
                if "created_at" not in nuevo:
                    nuevo["created_at"] = datetime.now().isoformat()
                filas.append(nuevo)
                nuevos.append(nuevo)
            db[self.table_name] = filas
            _guardar_db_local(db)
            return _LocalResp(nuevos)

        elif self._op == "update":
            actualizados = []
            for r in filas:
                if all(str(r.get(k)) == str(v) for k, v in self._filters):
                    r.update(self._payload)
                    actualizados.append(r)
            db[self.table_name] = filas
            _guardar_db_local(db)
            return _LocalResp(actualizados)

        elif self._op == "delete":
            restantes = [
                r for r in filas
                if not all(str(r.get(k)) == str(v) for k, v in self._filters)
            ]
            db[self.table_name] = restantes
            _guardar_db_local(db)
            return _LocalResp([])

        return _LocalResp([])

    def execute(self):
        # Si ya detectamos que Supabase está offline en esta sesión, ir directo a local sin demora
        if not self.status_tracker.get("online", True):
            return self._ejecutar_en_local()

        try:
            q = self.real_client.table(self.table_name)
            if self._op == "select":
                q = q.select("*")
            elif self._op == "insert":
                q = q.insert(self._payload)
            elif self._op == "update":
                q = q.update(self._payload)
            elif self._op == "delete":
                q = q.delete()

            for k, v in self._filters:
                q = q.eq(k, v)
            if self._order_col:
                q = q.order(self._order_col, desc=self._order_desc)

            res = q.execute()
            self.status_tracker["online"] = True
            return res
        except Exception as err:
            logger.info("Supabase inaccesible (%s). Activando almacenamiento local automático.", str(err))
            self.status_tracker["online"] = False
            return self._ejecutar_en_local()

class HybridSupabaseClient:
    def __init__(self, raw_client):
        self.raw_client = raw_client
        self.status = {"online": True}

    def table(self, name: str) -> _HybridTableQuery:
        return _HybridTableQuery(self.raw_client, name, self.status)

@st.cache_resource
def init_connection() -> HybridSupabaseClient:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        raw = create_client(url, key)
    except Exception:
        raw = None
    return HybridSupabaseClient(raw)

supabase = init_connection()


# --- 3. FUNCIONES AUXILIARES DE DATOS, FORMATOS Y PROMOS ---
CONFIG_ROW_NAME = "__PRECIOS_VENTA__"
CATALOG_ROW_NAME = "__CATALOGO_PIZZAS__"
PROMOS_ROW_NAME = "__PROMOS_CONFIG__"

VARIEDADES_BASE = [
    {"slug": "muzza", "nombre": "Muzzarella", "emoji": "🧀", "precio": 7500.0, "base": True},
    {"slug": "huevo", "nombre": "Especial Huevo", "emoji": "🥚", "precio": 8500.0, "base": True},
    {"slug": "tomate", "nombre": "Especial Tomate", "emoji": "🍅", "precio": 8500.0, "base": True},
]

PROMOS_BASE = {
    "activa": True,
    "promo_comun": {
        "activa": True,
        "nombre": "Promo Común",
        "cantidad": 2,
        "precio": 13000.0,
        "variedad": "muzza"
    },
    "promo_especial": {
        "activa": True,
        "nombre": "Promo Especiales",
        "cantidad": 2,
        "precio": 15000.0,
        "variedades": ["huevo", "tomate"]
    }
}

def formato_moneda(monto) -> str:
    """Formato de moneda argentino: $ 15.000 (sin decimales para pesos) o $ 15.000,50 si tuviera decimales."""
    if monto is None:
        return "$0"
    try:
        val = float(monto)
        if val.is_integer():
            txt = f"{int(val):,}".replace(",", ".")
            return f"${txt}"
        else:
            txt = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"${txt}"
    except Exception:
        return f"${monto}"

def formatear_fecha_ar(f) -> str:
    """Convierte fechas (date, datetime o string 'YYYY-MM-DD') al formato argentino 'DD/MM/YYYY'."""
    if not f:
        return ""
    if isinstance(f, (date, datetime)):
        return f.strftime("%d/%m/%Y")
    try:
        s = str(f).split("T")[0].split(" ")[0]
        partes = s.split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
    except Exception:
        pass
    return str(f)

def safe_str(text: str) -> str:
    """Sanitiza entradas para prevenir inyecciones de Markdown y caracteres de control."""
    if not text:
        return ""
    s = str(text)
    for ch in ("*", "_", "`", "[", "]", "(", ")", "<", ">", "|"):
        s = s.replace(ch, "")
    return s.strip()

def safe_html(text: str) -> str:
    """Escapa texto para inserción segura en bloques HTML."""
    return html.escape(safe_str(text))

def limpiar_telefono_argentina(tel: str) -> str:
    """
    Normaliza teléfonos argentinos para WhatsApp eliminando 0 inicial y el '15' móvil tradicional.
    Garantiza prefijo internacional 549 requerido por WhatsApp.
    """
    if not tel:
        return ""
    nums = re.sub(r"\D", "", str(tel))
    if not nums:
        return ""
    if nums.startswith("549"):
        nums = nums[3:]
    elif nums.startswith("54"):
        nums = nums[2:]
        if nums.startswith("9"):
            nums = nums[1:]

    nums = nums.lstrip("0")

    m = re.match(r"^(\d{2,4})15(\d{6,8})$", nums)
    if m:
        nums = m.group(1) + m.group(2)

    return f"549{nums}"

def slugify(texto: str) -> str:
    """Genera un slug seguro y libre de colisiones."""
    limpio = re.sub(r"[^a-z0-9]+", "_", str(texto).lower().strip()).strip("_")
    if not limpio:
        limpio = f"var_{uuid.uuid4().hex[:6]}"
    return limpio[:30]

def parsear_modo_insumo(modo_raw: str):
    """Extrae el modo base ('kg' o 'unidad') y el diccionario de usos en variedades extra."""
    if not modo_raw:
        return "kg", {}
    if "|" in modo_raw:
        partes = modo_raw.split("|", 1)
        try:
            return partes[0], json.loads(partes[1])
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            logger.warning("Error parseando modo insumo: %s", str(err))
            return partes[0], {}
    return modo_raw, {}

def empaquetar_modo_insumo(modo_base: str, usos_extra: dict) -> str:
    base_limpia = modo_base.replace("|", "")
    usos_limpios = {k.replace("|", ""): float(v) for k, v in usos_extra.items() if float(v or 0) > 0}
    if not usos_limpios:
        return base_limpia
    return f"{base_limpia}|{json.dumps(usos_limpios)}"

def parsear_estado_y_extras_pedido(estado_raw: str):
    """Extrae el estado de entrega ('pendiente', 'entregado', 'cancelado') y cantidades de variedades extra."""
    if not estado_raw:
        return "pendiente", {}
    if "|" in estado_raw:
        partes = estado_raw.split("|", 1)
        try:
            return partes[0], json.loads(partes[1])
        except (json.JSONDecodeError, TypeError, ValueError) as err:
            logger.warning("Error parseando extras pedido: %s", str(err))
            return partes[0], {}
    return estado_raw, {}

def empaquetar_estado_y_extras_pedido(estado_limpio: str, cant_extras: dict) -> str:
    est_limpio = estado_limpio.replace("|", "")
    extras_limpios = {k.replace("|", ""): int(v) for k, v in cant_extras.items() if int(v or 0) > 0}
    if not extras_limpios:
        return est_limpio
    return f"{est_limpio}|{json.dumps(extras_limpios)}"

# --- CARGA CON CACHÉ DE LECTURA ---
@st.cache_data(ttl=300, show_spinner=False)
def obtener_clientes():
    try:
        res = supabase.table("pizzas_clientes").select("id, nombre, telefono, direccion").order("nombre").execute()
        return res.data or []
    except Exception as e:
        logger.error("Error obteniendo clientes: %s", str(e), exc_info=True)
        return []

@st.cache_data(ttl=300, show_spinner=False)
def obtener_insumos_catalogo_y_promos():
    try:
        res = supabase.table("pizzas_insumos").select("*").order("created_at").execute()
        filas = res.data or []
    except Exception as e:
        logger.error("Error obteniendo insumos y catálogo: %s", str(e), exc_info=True)
        filas = []

    catalogo = [dict(v) for v in VARIEDADES_BASE]
    id_catalogo = None
    id_precios_legacy = None
    precios_legacy = None

    promos_config = dict(PROMOS_BASE)
    id_promos = None

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
            except Exception as err:
                logger.warning("Error decodificando catálogo: %s", str(err))
        elif nombre_f == PROMOS_ROW_NAME and modo_f.startswith("promos|"):
            id_promos = f.get("id")
            try:
                datos_pr = json.loads(modo_f.split("|", 1)[1])
                if isinstance(datos_pr, dict):
                    promos_config = {**PROMOS_BASE, **datos_pr}
                    if "promo_comun" in datos_pr:
                        promos_config["promo_comun"] = {**PROMOS_BASE["promo_comun"], **datos_pr["promo_comun"]}
                    if "promo_especial" in datos_pr:
                        promos_config["promo_especial"] = {**PROMOS_BASE["promo_especial"], **datos_pr["promo_especial"]}
            except Exception as err:
                logger.warning("Error decodificando promociones: %s", str(err))
        elif nombre_f == CONFIG_ROW_NAME and modo_f == "config":
            id_precios_legacy = f.get("id")
            precios_legacy = {
                "muzza": float(f.get("uso_muzza") or 7500.0),
                "huevo": float(f.get("uso_huevo") or 8500.0),
                "tomate": float(f.get("uso_tomate") or 8500.0),
            }
        else:
            insumos.append(f)

    if not id_catalogo and precios_legacy:
        for v in catalogo:
            if v["slug"] in precios_legacy:
                v["precio"] = precios_legacy[v["slug"]]

    return insumos, catalogo, id_catalogo, promos_config, id_promos

def guardar_catalogo_pizzas(id_catalogo, lista_catalogo):
    modo_serializado = f"catalogo|{json.dumps(lista_catalogo, ensure_ascii=False)}"
    p_muzza = next((float(v["precio"]) for v in lista_catalogo if v["slug"] == "muzza"), 7500.0)
    p_huevo = next((float(v["precio"]) for v in lista_catalogo if v["slug"] == "huevo"), 8500.0)
    p_tomate = next((float(v["precio"]) for v in lista_catalogo if v["slug"] == "tomate"), 8500.0)

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
    st.cache_data.clear()

def guardar_promos_config(id_promos, config_dict):
    modo_serializado = f"promos|{json.dumps(config_dict, ensure_ascii=False)}"
    p_comun = float(config_dict.get("promo_comun", {}).get("precio", 13000.0))
    p_esp = float(config_dict.get("promo_especial", {}).get("precio", 15000.0))

    datos = {
        "nombre": PROMOS_ROW_NAME,
        "modo": modo_serializado,
        "precio_bulto": 0,
        "cantidad_bulto": 1,
        "uso_muzza": p_comun,
        "uso_huevo": p_esp,
        "uso_tomate": 0,
    }
    if id_promos:
        supabase.table("pizzas_insumos").update(datos).eq("id", id_promos).execute()
    else:
        supabase.table("pizzas_insumos").insert(datos).execute()
    st.cache_data.clear()

def calcular_total_con_promos(cantidades: dict, catalogo: list, promos: dict):
    """
    Motor determinístico de cálculo de promociones y totales.
    - Blindado contra ZeroDivisionError (pack_comun >= 1, pack_esp >= 1).
    - Ordenamiento determinístico: empareja primero especiales de mayor valor para máximo beneficio del cliente.
    """
    mapa_precios = {v["slug"]: float(v["precio"]) for v in catalogo}
    mapa_nombres = {v["slug"]: v["nombre"] for v in catalogo}

    total = 0.0
    desglose = []
    ahorro_total = 0.0

    p_comun = promos.get("promo_comun", {})
    p_esp = promos.get("promo_especial", {})

    comun_activa = p_comun.get("activa", True) and promos.get("activa", True)
    esp_activa = p_esp.get("activa", True) and promos.get("activa", True)

    slug_comun = p_comun.get("variedad", "muzza")
    slugs_esp = set(p_esp.get("variedades", ["huevo", "tomate"]))

    # 1. Promo Común
    cant_comun = int(cantidades.get(slug_comun, 0))
    if comun_activa and cant_comun > 0:
        pack_comun = max(1, int(p_comun.get("cantidad", 2)))
        precio_pack_comun = float(p_comun.get("precio", 13000.0))
        combos_c = cant_comun // pack_comun
        sobrante_c = cant_comun % pack_comun

        if combos_c > 0:
            sub = combos_c * precio_pack_comun
            total += sub
            costo_lista = combos_c * pack_comun * mapa_precios.get(slug_comun, 7500.0)
            ahorro_c = max(0.0, costo_lista - sub)
            ahorro_total += ahorro_c
            nombre_promo_c = p_comun.get("nombre", "Promo Común")
            desglose.append(f"{combos_c}x {nombre_promo_c} ({formato_moneda(sub)})")

        if sobrante_c > 0:
            precio_u = mapa_precios.get(slug_comun, 7500.0)
            sub = sobrante_c * precio_u
            total += sub
            nom_v = mapa_nombres.get(slug_comun, "Común")
            desglose.append(f"{sobrante_c}x {nom_v} individual ({formato_moneda(sub)})")
    elif cant_comun > 0:
        precio_u = mapa_precios.get(slug_comun, 7500.0)
        sub = cant_comun * precio_u
        total += sub
        nom_v = mapa_nombres.get(slug_comun, "Común")
        desglose.append(f"{cant_comun}x {nom_v} ({formato_moneda(sub)})")

    # 2. Promo Especiales (emparejamiento determinístico de mayor a menor valor)
    pizzas_esp_pedidas = []
    for var in catalogo:
        s = var["slug"]
        if s in slugs_esp:
            c = int(cantidades.get(s, 0))
            if c > 0:
                pizzas_esp_pedidas.extend([s] * c)

    pizzas_esp_pedidas.sort(key=lambda s: mapa_precios.get(s, 0.0), reverse=True)

    cant_esp = len(pizzas_esp_pedidas)
    if esp_activa and cant_esp > 0:
        pack_esp = max(1, int(p_esp.get("cantidad", 2)))
        precio_pack_esp = float(p_esp.get("precio", 15000.0))
        combos_e = cant_esp // pack_esp
        sobrante_e = cant_esp % pack_esp

        if combos_e > 0:
            sub = combos_e * precio_pack_esp
            total += sub
            costo_lista = sum(mapa_precios.get(s, 8500.0) for s in pizzas_esp_pedidas[:combos_e * pack_esp])
            ahorro_e = max(0.0, costo_lista - sub)
            ahorro_total += ahorro_e
            nombre_promo_e = p_esp.get("nombre", "Promo Especiales")
            desglose.append(f"{combos_e}x {nombre_promo_e} ({formato_moneda(sub)})")

        if sobrante_e > 0:
            for s in pizzas_esp_pedidas[combos_e * pack_esp:]:
                precio_u = mapa_precios.get(s, 8500.0)
                total += precio_u
                nom_v = mapa_nombres.get(s, "Especial")
                desglose.append(f"1x {nom_v} individual ({formato_moneda(precio_u)})")
    elif cant_esp > 0:
        for s in pizzas_esp_pedidas:
            precio_u = mapa_precios.get(s, 8500.0)
            total += precio_u
            nom_v = mapa_nombres.get(s, "Especial")
            desglose.append(f"1x {nom_v} ({formato_moneda(precio_u)})")

    # 3. Otras variedades
    for v in catalogo:
        s = v["slug"]
        if s != slug_comun and s not in slugs_esp:
            c = int(cantidades.get(s, 0))
            if c > 0:
                precio_u = mapa_precios.get(s, 0.0)
                sub = c * precio_u
                total += sub
                desglose.append(f"{c}x {v['nombre']} ({formato_moneda(sub)})")

    return total, desglose, ahorro_total

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
        cant_bulto = max(0.01, float(ins.get("cantidad_bulto") or 1))

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
    tel_limpio = limpiar_telefono_argentina(telefono)
    if not tel_limpio:
        return None
    msg = f"Hola {safe_str(nombre)}! Te escribimos de *Pizzas Martina* por tu pedido ({detalle_txt} - Total: {formato_moneda(total)})."
    return f"https://wa.me/{tel_limpio}?text={quote(msg)}"

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
    titulo_modo = "PENDIENTES DE HORNEAR / ENTREGAR" if solo_pendientes else "RESUMEN DEL DÍA"

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
            dir_txt = f" ({safe_str(p.get('direccion'))})" if p.get("direccion") else ""
            monto_txt = f" - {formato_moneda(float(p.get('total_plata') or 0))}"
            lineas.append(f"- *{safe_str(p['nombre_cliente'])}*{dir_txt}: {txt_pizzas}{monto_txt}")

    if incluir_caja and datos_caja:
        lineas.append("")
        lineas.append("*RESUMEN DE CAJA:*")
        lineas.append(f"- Venta Total: *{formato_moneda(datos_caja['total'])}*")
        lineas.append(f"- Transferencia: {formato_moneda(datos_caja['transferencia'])}")
        lineas.append(f"- Efectivo: {formato_moneda(datos_caja['efectivo'])}")
        lineas.append(f"- Falta Cobrar: {formato_moneda(datos_caja['pendiente'])}")
        lineas.append(f"- Ganancia limpia est.: *{formato_moneda(datos_caja['ganancia'])}*")

    return "\n".join(lineas)


# --- COMPONENTES VISUALES HTML ---
def st_html(raw_html: str):
    """Renderiza HTML eliminando sangrías de 4+ espacios y líneas vacías para evitar bloques <pre><code> en Markdown."""
    limpio = "\n".join(line.strip() for line in raw_html.splitlines() if line.strip())
    st.markdown(limpio, unsafe_allow_html=True)

def render_pizza_card_top(var: dict, cant_actual: int = 0):
    """Renderiza el encabezado visual de cada tarjeta de pizza."""
    clase_activa = "active" if cant_actual > 0 else ""
    badge_html = f'<span class="pm-pizza-badge-qty">x{cant_actual}</span>' if cant_actual > 0 else ""
    st_html(f"""
    <div class="pm-pizza-card {clase_activa}">
        <div class="pm-pizza-left">
            <div class="pm-pizza-emoji">{var['emoji']}</div>
            <div>
                <div class="pm-pizza-name">{safe_html(var['nombre'])}</div>
                <div class="pm-pizza-price">{formato_moneda(var['precio'])} c/u</div>
            </div>
        </div>
        {badge_html}
    </div>
    """)

def render_ticket_resumen(tot_pizzas: int, desglose: list, total_calc: float, ahorro_calc: float):
    """Renderiza un ticket digital moderno con el desglose del pedido y ahorros por promo."""
    if tot_pizzas <= 0:
        return
    chips_html = "".join(f'<span class="pm-ticket-chip">🍕 {safe_html(item)}</span>' for item in desglose)
    saving_html = ""
    if ahorro_calc > 0:
        saving_html = f'<div class="pm-ticket-saving">🔥 ¡Promo activada! El cliente ahorra {formato_moneda(ahorro_calc)}</div>'

    st_html(f"""
    <div class="pm-ticket">
        <div class="pm-ticket-header">
            <div class="pm-ticket-title">
                <span>🧾 Resumen del Pedido</span>
                <span class="pm-pizza-badge-qty">{tot_pizzas} {"pizza" if tot_pizzas == 1 else "pizzas"}</span>
            </div>
            <div class="pm-ticket-total">{formato_moneda(total_calc)}</div>
        </div>
        <div class="pm-ticket-items">{chips_html}</div>
        {saving_html}
    </div>
    """)

def render_comanda_card_header(p: dict, catalogo: list):
    """Renderiza la cabecera visual estilo comanda gastronómica para un pedido."""
    est_limpio, _ = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))
    pago_actual = str(p.get("metodo_pago") or "pendiente").lower()

    badge_est_map = {
        "pendiente": ('pm-badge-pendiente', '🕒 En Horno / Pendiente'),
        "entregado": ('pm-badge-entregado', '✅ Entregado'),
        "cancelado": ('pm-badge-cancelado', '❌ Cancelado')
    }
    cls_est, txt_est = badge_est_map.get(est_limpio, ('pm-badge-pendiente', '🕒 Pendiente'))

    badge_pago_map = {
        "transferencia": ('pm-badge-pago-ok', '🏦 Transferencia'),
        "efectivo": ('pm-badge-pago-efec', '💵 Efectivo'),
        "pendiente": ('pm-badge-pago-debe', '⏳ Falta Cobrar')
    }
    cls_pago, txt_pago = badge_pago_map.get(pago_actual, ('pm-badge-pago-debe', '⏳ Pendiente'))

    tags_pizzas = []
    for v in catalogo:
        c_v = obtener_cantidad_pedido_variedad(p, v["slug"])
        if c_v > 0:
            tags_pizzas.append(f'<span class="pm-pizza-tag">{v["emoji"]} {c_v}x {safe_html(v["nombre"])}</span>')
    tags_html = "".join(tags_pizzas) if tags_pizzas else '<span class="pm-pizza-tag">Sin pizzas</span>'

    meta_items = []
    if p.get("direccion"):
        meta_items.append(f'<span>📍 {safe_html(p["direccion"])}</span>')
    if p.get("telefono"):
        meta_items.append(f'<span>📞 {safe_html(p["telefono"])}</span>')
    meta_html = f'<div class="pm-comanda-meta">{"".join(meta_items)}</div>' if meta_items else ""

    total_fmt = formato_moneda(float(p.get("total_plata") or 0))

    st_html(f"""
    <div class="pm-comanda-header">
        <div style="flex: 1; min-width: 220px;">
            <div class="pm-comanda-client">
                <span>{safe_html(p.get('nombre_cliente') or 'Cliente')}</span>
                <span class="pm-badge {cls_est}">{txt_est}</span>
            </div>
            <div class="pm-pizza-tags">{tags_html}</div>
            {meta_html}
        </div>
        <div class="pm-comanda-price-box">
            <div class="pm-comanda-price">{total_fmt}</div>
            <span class="pm-badge {cls_pago}">{txt_pago}</span>
        </div>
    </div>
    """)


def render_formulario_editar_pedido(p: dict, catalogo: list, promos: dict, contexto: str = "caja"):
    """Formulario interactivo completo para modificar un pedido existente."""
    pid = p["id"]
    st.markdown(f"""
    <div class="pm-sec-header">
        <div>
            <div class="pm-sec-title">✏️ Modificar Pedido — {safe_html(p['nombre_cliente'])}</div>
            <div class="pm-sec-sub">Ajustá cantidades, datos del cliente o estado y guardá los cambios.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    f_orig = p.get("fecha")
    try:
        if isinstance(f_orig, str):
            f_val = date.fromisoformat(f_orig.split("T")[0])
        elif isinstance(f_orig, date):
            f_val = f_orig
        else:
            f_val = date.today()
    except Exception:
        f_val = date.today()

    fe1, fe2 = st.columns([2, 1])
    with fe1:
        nom_ed = st.text_input("Nombre del Cliente *", value=p.get("nombre_cliente", ""), max_chars=80, key=f"ed_nom_{pid}_{contexto}")
    with fe2:
        f_ed = st.date_input("Fecha del pedido", value=f_val, format="DD/MM/YYYY", key=f"ed_f_{pid}_{contexto}")

    ce1, ce2 = st.columns(2)
    with ce1:
        tel_ed = st.text_input("Teléfono / WhatsApp", value=p.get("telefono") or "", max_chars=25, key=f"ed_tel_{pid}_{contexto}")
    with ce2:
        dir_ed = st.text_input("Dirección", value=p.get("direccion") or "", max_chars=120, key=f"ed_dir_{pid}_{contexto}")

    st.markdown("##### 🍕 Modificar Cantidades de Pizzas")
    cants_ed = {}
    cols_ed_p = st.columns(3)
    for idx_v, var in enumerate(catalogo):
        with cols_ed_p[idx_v % 3]:
            c_orig = obtener_cantidad_pedido_variedad(p, var["slug"])
            key_ed_c = f"ed_cant_{var['slug']}_{pid}_{contexto}"
            val_actual_ed = st.session_state.get(key_ed_c, int(c_orig))
            render_pizza_card_top(var, int(val_actual_ed))
            cants_ed[var["slug"]] = st.number_input(
                f"Cantidad {var['nombre']}",
                min_value=0,
                step=1,
                value=int(c_orig),
                key=key_ed_c,
                label_visibility="collapsed"
            )

    tot_calc_ed, desgl_ed, ahorro_ed = calcular_total_con_promos(cants_ed, catalogo, promos)
    render_ticket_resumen(sum(cants_ed.values()), desgl_ed, tot_calc_ed, ahorro_ed)

    key_tot_ed = f"ed_tot_{pid}_{contexto}"
    key_prev_calc_ed = f"ed_prev_calc_{pid}_{contexto}"

    if key_prev_calc_ed not in st.session_state:
        st.session_state[key_tot_ed] = float(p.get("total_plata") or tot_calc_ed)
        st.session_state[key_prev_calc_ed] = float(tot_calc_ed)
    elif st.session_state[key_prev_calc_ed] != tot_calc_ed:
        st.session_state[key_tot_ed] = float(tot_calc_ed)
        st.session_state[key_prev_calc_ed] = float(tot_calc_ed)

    est_limpio_actual, _ = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))
    pago_actual = p.get("metodo_pago", "transferencia")
    estados_opc = ["pendiente", "entregado", "cancelado"]
    pagos_opc = ["transferencia", "efectivo", "pendiente"]
    idx_est = estados_opc.index(est_limpio_actual) if est_limpio_actual in estados_opc else 0
    idx_pago = pagos_opc.index(pago_actual) if pago_actual in pagos_opc else 0

    te1, te2, te3 = st.columns(3)
    with te1:
        tot_ed_input = st.number_input(
            "💵 Total a cobrar ($)",
            min_value=0.0,
            value=float(st.session_state[key_tot_ed]),
            step=500.0,
            format="%.0f",
            key=key_tot_ed
        )
        if tot_ed_input != tot_calc_ed and sum(cants_ed.values()) > 0:
            if st.button("🔄 Restablecer a total de pizzas/promos", key=f"btn_recalc_{pid}_{contexto}", help="Vuelve a calcular según pizzas y promos"):
                st.session_state[key_tot_ed] = float(tot_calc_ed)
                st.session_state[key_prev_calc_ed] = float(tot_calc_ed)
                st.rerun()

        if sum(cants_ed.values()) > 0 and tot_calc_ed > 0 and tot_ed_input < (tot_calc_ed * 0.5):
            st.warning(f"⚠️ El monto ingresado ({formato_moneda(tot_ed_input)}) tiene más del 50% de descuento frente al cálculo de lista ({formato_moneda(tot_calc_ed)}).")

    with te2:
        pag_ed = st.selectbox(
            "Método de Pago",
            options=pagos_opc,
            index=idx_pago,
            format_func=lambda x: {"transferencia": "🏦 Transferencia", "efectivo": "💵 Efectivo", "pendiente": "⏳ Pendiente"}.get(x, x),
            key=f"ed_pag_{pid}_{contexto}"
        )
    with te3:
        est_ed = st.selectbox(
            "Estado de Entrega",
            options=estados_opc,
            index=idx_est,
            format_func=lambda x: {"pendiente": "🕒 Pendiente", "entregado": "✅ Entregado", "cancelado": "❌ Cancelado"}.get(x, x),
            key=f"ed_est_{pid}_{contexto}"
        )

    be1, be2 = st.columns([2, 1])
    with be1:
        if st.button("💾 Guardar Cambios en este Pedido", type="primary", use_container_width=True, key=f"btn_save_{pid}_{contexto}"):
            if not nom_ed.strip():
                st.warning("⚠️ El nombre del cliente no puede quedar vacío.")
            elif sum(cants_ed.values()) <= 0:
                st.warning("⚠️ El pedido debe tener al menos 1 pizza.")
            else:
                extras_ed = {
                    k: v for k, v in cants_ed.items()
                    if k not in ("muzza", "huevo", "tomate") and v > 0
                }
                est_empaquetado_ed = empaquetar_estado_y_extras_pedido(est_ed, extras_ed)
                try:
                    with st.spinner("Guardando modificaciones..."):
                        supabase.table("pizzas_pedidos").update({
                            "fecha": str(f_ed),
                            "nombre_cliente": safe_str(nom_ed),
                            "telefono": safe_str(tel_ed),
                            "direccion": safe_str(dir_ed),
                            "cant_muzza": int(cants_ed.get("muzza", 0)),
                            "cant_huevo": int(cants_ed.get("huevo", 0)),
                            "cant_tomate": int(cants_ed.get("tomate", 0)),
                            "total_plata": float(tot_ed_input),
                            "estado_entrega": est_empaquetado_ed,
                            "metodo_pago": pag_ed
                        }).eq("id", pid).execute()
                        st.cache_data.clear()

                    st.session_state["editando_pedido_id"] = None
                    st.toast(f"✅ Pedido de {safe_str(nom_ed)} actualizado con éxito", icon="🍕")
                    st.rerun()
                except Exception as err:
                    logger.error("Error al actualizar pedido: %s", str(err), exc_info=True)
                    st.error("⚠️ Error de conexión al guardar cambios. Reintentá.")

    with be2:
        if st.button("❌ Cancelar", use_container_width=True, key=f"btn_canc_{pid}_{contexto}"):
            st.session_state["editando_pedido_id"] = None
            st.rerun()


# --- 4. CARGA INICIAL DE DATOS ---
if "editando_pedido_id" not in st.session_state:
    st.session_state["editando_pedido_id"] = None

clientes = obtener_clientes()
insumos, catalogo_pizzas, id_catalogo, config_promos, id_promos = obtener_insumos_catalogo_y_promos()
costos_pizza = calcular_costos_por_pizza(insumos, catalogo_pizzas)

# --- 5. ENCABEZADO HERO Y NAVEGACIÓN ---
estado_conexion_txt = "Nube Activa" if supabase.status.get("online", True) else "Modo Local Activo"
col_hero, col_refresh = st.columns([6, 1], vertical_alignment="center")
with col_hero:
    st.markdown(f"""
    <div class="pm-hero">
        <div class="pm-hero-top">
            <div class="pm-brand">
                <div class="pm-logo-badge">🍕</div>
                <div>
                    <div class="pm-title">Pizzas Martina</div>
                    <div class="pm-subtitle">Comandas en Tiempo Real · Promos & Costos</div>
                </div>
            </div>
            <div class="pm-badges-row">
                <span class="pm-pill-live"><span class="pm-dot-live"></span> {estado_conexion_txt}</span>
                <span class="pm-pill-date">📅 {formatear_fecha_ar(date.today())}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_refresh:
    if st.button("🔄", help="Actualizar datos en vivo y limpiar caché", use_container_width=True):
        supabase.status["online"] = True
        st.cache_data.clear()
        st.toast("Datos actualizados", icon="🔄")
        st.rerun()

tab_pedidos, tab_promos, tab_clientes, tab_costos, tab_caja = st.tabs([
    "📝 Pedidos",
    "🔥 Promos",
    "👥 Clientes",
    "💰 Costos",
    "📊 Caja / Día"
])


# =========================================================
# PESTAÑA 1: PEDIDOS
# =========================================================
with tab_pedidos:
    if "reset_pedido_cnt" not in st.session_state:
        st.session_state["reset_pedido_cnt"] = 0
    if "msg_pedido_ok" in st.session_state:
        st.success(st.session_state.pop("msg_pedido_ok"))

    r_ped = st.session_state["reset_pedido_cnt"]

    with st.container(border=True):
        st.markdown("""
        <div class="pm-sec-header">
            <div>
                <div class="pm-sec-title">🍕 Tomar Nuevo Pedido</div>
                <div class="pm-sec-sub">Elegí un cliente de la agenda o usá Carga Rápida. Los combos se aplican solos.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        mapa_clientes = {
            f"📒 {safe_str(c['nombre'])} ({safe_str(c.get('direccion')) or 'Sin dirección'})": c
            for c in clientes
        }
        opciones_clientes = ["⚡ Carga Rápida (cliente de paso / sin agendar)"] + list(mapa_clientes.keys())

        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            seleccion_cli = st.selectbox(
                "👤 Cliente",
                options=opciones_clientes,
                index=None,
                placeholder="🔍 Buscá un cliente o elegí Carga Rápida...",
                key=f"sel_cli_{r_ped}"
            )
        with col_top2:
            fecha_pedido = st.date_input("📅 Fecha de entrega", value=date.today(), format="DD/MM/YYYY", key=f"fecha_ped_{r_ped}")

        cliente_elegido = mapa_clientes.get(seleccion_cli) if seleccion_cli else None
        guardar_nuevo_cliente_agenda = False

        if cliente_elegido:
            nombre_final = safe_str(cliente_elegido["nombre"])
            telefono_final = safe_str(cliente_elegido.get("telefono") or "")
            direccion_final = safe_str(cliente_elegido.get("direccion") or "")
            st.markdown(f"""
            <div class="pm-comanda-meta" style="margin: 2px 0 12px 0;">
                <span>👤 <b>{safe_html(nombre_final)}</b></span>
                <span>📍 {safe_html(direccion_final or 'Sin dirección')}</span>
                <span>📞 {safe_html(telefono_final or 'Sin teléfono')}</span>
            </div>
            """, unsafe_allow_html=True)
        elif seleccion_cli == "⚡ Carga Rápida (cliente de paso / sin agendar)":
            nombre_rapido = st.text_input(
                "Nombre o referencia rápida para este pedido *",
                placeholder="Ej: Lucas (retira), Vecino 3°B, Mostrador...",
                max_chars=80,
                key=f"nom_rap_{r_ped}"
            )
            rc1, rc2 = st.columns(2)
            with rc1:
                tel_rapido = st.text_input("Teléfono / WhatsApp (opcional)", placeholder="Ej: 3573 40-2784", max_chars=25, key=f"tel_rap_{r_ped}")
            with rc2:
                dir_rapido = st.text_input("Dirección (opcional)", placeholder="Ej: Belgrano 1230", max_chars=120, key=f"dir_rap_{r_ped}")

            guardar_nuevo_cliente_agenda = st.checkbox("💾 Guardar también este cliente en la agenda habitual", value=False, key=f"chk_agendar_{r_ped}")

            nombre_final = safe_str(nombre_rapido)
            telefono_final = safe_str(tel_rapido)
            direccion_final = safe_str(dir_rapido)
        else:
            nombre_final = ""
            telefono_final = ""
            direccion_final = ""

        st.markdown("##### 🧀 Seleccioná las Pizzas")
        cantidades_elegidas = {}
        cols_pizzas = st.columns(3)
        for idx, var in enumerate(catalogo_pizzas):
            with cols_pizzas[idx % 3]:
                key_cant_input = f"ped_cant_{var['slug']}_{r_ped}"
                val_actual = int(st.session_state.get(key_cant_input, 0))
                render_pizza_card_top(var, val_actual)
                cantidades_elegidas[var["slug"]] = st.number_input(
                    f"Cantidad de {var['nombre']}",
                    min_value=0,
                    step=1,
                    value=0,
                    key=key_cant_input,
                    label_visibility="collapsed"
                )

        total_calculado, desglose_calculo, ahorro_calculado = calcular_total_con_promos(
            cantidades_elegidas, catalogo_pizzas, config_promos
        )

        tot_pizzas_elegidas = sum(cantidades_elegidas.values())
        render_ticket_resumen(tot_pizzas_elegidas, desglose_calculo, total_calculado, ahorro_calculado)

        key_tot_ped = f"tot_plata_{r_ped}"
        key_prev_calc = f"prev_calc_{r_ped}"

        if key_prev_calc not in st.session_state or st.session_state[key_prev_calc] != total_calculado:
            st.session_state[key_tot_ped] = float(total_calculado)
            st.session_state[key_prev_calc] = float(total_calculado)

        if key_tot_ped not in st.session_state:
            st.session_state[key_tot_ped] = float(total_calculado)

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            total_plata = st.number_input(
                "💵 Total a cobrar ($)",
                min_value=0.0,
                value=float(st.session_state[key_tot_ped]),
                step=500.0,
                format="%.0f",
                help="Se actualiza automáticamente al elegir pizzas y combos. Podés editarlo a mano si hay envío o descuento.",
                key=key_tot_ped
            )
            if total_plata != total_calculado and tot_pizzas_elegidas > 0:
                if st.button("🔄 Restablecer precio promo", key=f"btn_reset_tot_{r_ped}", help="Vuelve a calcular según pizzas y promos"):
                    st.session_state[key_tot_ped] = float(total_calculado)
                    st.session_state[key_prev_calc] = float(total_calculado)
                    st.rerun()

            if tot_pizzas_elegidas > 0 and total_calculado > 0 and total_plata < (total_calculado * 0.5):
                st.warning(f"⚠️ El monto ingresado ({formato_moneda(total_plata)}) tiene más del 50% de descuento frente al cálculo de lista ({formato_moneda(total_calculado)}).")

        with col_p2:
            metodo_pago = st.selectbox(
                "💳 Método de Pago",
                options=["transferencia", "efectivo", "pendiente"],
                format_func=lambda x: {
                    "transferencia": "🏦 Transferencia",
                    "efectivo": "💵 Efectivo",
                    "pendiente": "⏳ Pendiente"
                }.get(x, x.capitalize()),
                key=f"met_pago_{r_ped}"
            )
        with col_p3:
            estado_entrega = st.selectbox(
                "🛵 Estado de Entrega",
                options=["pendiente", "entregado", "cancelado"],
                format_func=lambda x: {
                    "pendiente": "🕒 Pendiente",
                    "entregado": "✅ Entregado",
                    "cancelado": "❌ Cancelado / No había nadie"
                }.get(x, x.capitalize()),
                key=f"est_ent_{r_ped}"
            )

        if st.button("🔥 Confirmar y Cargar Pedido", type="primary", use_container_width=True):
            if not nombre_final:
                st.warning("⚠️ Primero buscá un cliente en el casillero 'Cliente' o elegí '⚡ Carga Rápida'.")
            elif tot_pizzas_elegidas <= 0:
                st.warning("⚠️ Agregá al menos 1 pizza al pedido.")
            else:
                extras_pedido = {
                    k: v for k, v in cantidades_elegidas.items()
                    if k not in ("muzza", "huevo", "tomate") and v > 0
                }
                estado_empaquetado = empaquetar_estado_y_extras_pedido(estado_entrega, extras_pedido)

                try:
                    with st.spinner("Registrando pedido..."):
                        if guardar_nuevo_cliente_agenda and nombre_final:
                            supabase.table("pizzas_clientes").insert({
                                "nombre": nombre_final,
                                "telefono": telefono_final,
                                "direccion": direccion_final
                            }).execute()

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

                        st.cache_data.clear()

                    st.session_state["reset_pedido_cnt"] += 1
                    st.session_state["msg_pedido_ok"] = f"✅ Pedido de **{nombre_final}** cargado correctamente ({formato_moneda(total_plata)})."
                    st.toast("✅ ¡Pedido registrado con éxito!", icon="🍕")
                    st.rerun()
                except Exception as err:
                    logger.error("Error al registrar pedido: %s", str(err), exc_info=True)
                    st.error("⚠️ Error de conexión al guardar el pedido. Por favor, reintentá.")

    # --- LISTA RÁPIDA DE PEDIDOS DEL DÍA ---
    st.markdown(f"""
    <div class="pm-sec-header" style="margin-top: 22px;">
        <div>
            <div class="pm-sec-title">📋 Comandas del {formatear_fecha_ar(fecha_pedido)}</div>
            <div class="pm-sec-sub">Revisá los pedidos cargados hoy o tocá <b>✏️ Modificar</b> para ajustar cualquier dato.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        res_ped_hoy = (
            supabase.table("pizzas_pedidos")
            .select("*")
            .eq("fecha", str(fecha_pedido))
            .order("created_at", desc=True)
            .execute()
        )
        pedidos_hoy = res_ped_hoy.data or []
    except Exception as e:
        logger.error("Error consultando pedidos del día: %s", str(e), exc_info=True)
        pedidos_hoy = []

    if not pedidos_hoy:
        st.info(f"Todavía no hay pedidos guardados para el {formatear_fecha_ar(fecha_pedido)}.")
    else:
        for ph in pedidos_hoy:
            if st.session_state.get("editando_pedido_id") == ph["id"]:
                with st.container(border=True):
                    render_formulario_editar_pedido(ph, catalogo_pizzas, config_promos, contexto="tab_pedidos")
            else:
                with st.container(border=True):
                    render_comanda_card_header(ph, catalogo_pizzas)
                    b_ed, b_wa, b_del = st.columns([3, 3, 1])
                    with b_ed:
                        if st.button("✏️ Modificar Pedido", key=f"btn_edit_hoy_{ph['id']}", use_container_width=True):
                            st.session_state["editando_pedido_id"] = ph["id"]
                            st.rerun()
                    with b_wa:
                        partes_wa_h = [
                            f"{obtener_cantidad_pedido_variedad(ph, v['slug'])} {v['nombre']}"
                            for v in catalogo_pizzas if obtener_cantidad_pedido_variedad(ph, v["slug"]) > 0
                        ]
                        url_wa_h = link_whatsapp_cliente(
                            ph.get("telefono") or "",
                            ph["nombre_cliente"],
                            ", ".join(partes_wa_h),
                            float(ph.get("total_plata") or 0)
                        )
                        if url_wa_h:
                            st.link_button("📲 WhatsApp", url_wa_h, use_container_width=True)
                        else:
                            st.button("📵 Sin Teléfono", disabled=True, key=f"no_tel_h_{ph['id']}", use_container_width=True)
                    with b_del:
                        with st.popover("🗑️", help="Eliminar pedido"):
                            st.write("¿Eliminar este pedido definitivamente?")
                            if st.button("Sí, eliminar", key=f"del_confirm_hoy_{ph['id']}", type="primary", use_container_width=True):
                                try:
                                    with st.spinner("Eliminando..."):
                                        supabase.table("pizzas_pedidos").delete().eq("id", ph["id"]).execute()
                                        st.cache_data.clear()
                                    st.toast("🗑️ Pedido eliminado", icon="🍕")
                                    st.rerun()
                                except Exception as err:
                                    logger.error("Error al eliminar pedido: %s", str(err), exc_info=True)
                                    st.error("Error eliminando pedido.")


# =========================================================
# PESTAÑA 2: PROMOS
# =========================================================
with tab_promos:
    p_comun = config_promos.get("promo_comun", {})
    p_esp = config_promos.get("promo_especial", {})

    precio_muzza_actual = next((float(v["precio"]) for v in catalogo_pizzas if v["slug"] == "muzza"), 7500.0)
    cant_c_actual = int(p_comun.get("cantidad", 2))
    prec_c_actual = float(p_comun.get("precio", 13000.0))
    ahorro_c_actual = max(0.0, (cant_c_actual * precio_muzza_actual) - prec_c_actual)

    cant_e_actual = int(p_esp.get("cantidad", 2))
    prec_e_actual = float(p_esp.get("precio", 15000.0))

    st.markdown(f"""
    <div class="pm-kpi-grid">
        <div class="pm-kpi-card" style="--kpi-accent: #FF6B00;">
            <div class="pm-kpi-label">🧀 PROMO COMÚN ({'ACTIVA' if p_comun.get('activa', True) else 'PAUSADA'})</div>
            <div class="pm-kpi-value">{cant_c_actual}x Muzzarella · {formato_moneda(prec_c_actual)}</div>
            <div class="pm-kpi-sub">Ahorro cliente: {formato_moneda(ahorro_c_actual)} por combo</div>
        </div>
        <div class="pm-kpi-card" style="--kpi-accent: #10B981;">
            <div class="pm-kpi-label">🥚🍅 PROMO ESPECIALES ({'ACTIVA' if p_esp.get('activa', True) else 'PAUSADA'})</div>
            <div class="pm-kpi-value">{cant_e_actual}x Especiales · {formato_moneda(prec_e_actual)}</div>
            <div class="pm-kpi-sub">Combinables iguales o surtidas (1 y 1)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_config_promos"):
        st.markdown("#### ⚙️ Configurar Reglas y Precios de Combos")
        st.caption("Las promos se aplican solas al cargar pedidos. Si piden 1 sola pizza, se cobra a precio individual de lista.")

        st.markdown("##### 🧀 1. Promo Común (Muzzarella)")
        pc1, pc2, pc3 = st.columns([1, 2, 2])
        with pc1:
            comun_activa = st.checkbox("Activa", value=bool(p_comun.get("activa", True)), key="cfg_comun_activa")
        with pc2:
            comun_cant = st.number_input("Cantidad de pizzas en el combo", min_value=2, max_value=10, value=cant_c_actual, step=1, key="cfg_comun_cant")
        with pc3:
            comun_precio = st.number_input("Precio del Combo ($)", min_value=0.0, value=prec_c_actual, step=500.0, format="%.0f", key="cfg_comun_precio")

        st.divider()

        st.markdown("##### 🥚🍅 2. Promo Especiales (Huevo y/o Tomate)")
        pe1, pe2, pe3 = st.columns([1, 2, 2])
        with pe1:
            esp_activa = st.checkbox("Activa", value=bool(p_esp.get("activa", True)), key="cfg_esp_activa")
        with pe2:
            esp_cant = st.number_input("Cantidad de pizzas en el combo", min_value=2, max_value=10, value=cant_e_actual, step=1, key="cfg_esp_cant")
        with pe3:
            esp_precio = st.number_input("Precio del Combo ($)", min_value=0.0, value=prec_e_actual, step=500.0, format="%.0f", key="cfg_esp_precio")

        variedades_disponibles = [v for v in catalogo_pizzas if v["slug"] != "muzza"]
        slugs_esp_guardados = p_esp.get("variedades", ["huevo", "tomate"])

        esp_vars_seleccionadas = st.multiselect(
            "Variedades que combinan en la promo especial (pueden ser 2 iguales o 1 y 1):",
            options=[v["slug"] for v in variedades_disponibles],
            default=[s for s in slugs_esp_guardados if s in [v["slug"] for v in variedades_disponibles]] or ["huevo", "tomate"],
            format_func=lambda s: next((f"{v['emoji']} {v['nombre']} ({formato_moneda(v['precio'])})" for v in catalogo_pizzas if v["slug"] == s), s),
            key="cfg_esp_variedades"
        )

        if st.form_submit_button("💾 Guardar Configuración de Promociones", type="primary", use_container_width=True):
            nueva_config = {
                "activa": True,
                "promo_comun": {
                    "activa": comun_activa,
                    "nombre": f"Promo {comun_cant} Comunes",
                    "cantidad": int(comun_cant),
                    "precio": float(comun_precio),
                    "variedad": "muzza"
                },
                "promo_especial": {
                    "activa": esp_activa,
                    "nombre": f"Promo {esp_cant} Especiales",
                    "cantidad": int(esp_cant),
                    "precio": float(esp_precio),
                    "variedades": esp_vars_seleccionadas or ["huevo", "tomate"]
                }
            }
            try:
                with st.spinner("Guardando promociones..."):
                    guardar_promos_config(id_promos, nueva_config)
                st.toast("✅ Promociones guardadas", icon="🍕")
                st.rerun()
            except Exception as err:
                logger.error("Error al guardar promos: %s", str(err), exc_info=True)
                st.error("⚠️ Error guardando promociones.")

    with st.container(border=True):
        st.markdown("""
        <div class="pm-sec-header">
            <div>
                <div class="pm-sec-title">🧪 Simulador de Combos en Vivo</div>
                <div class="pm-sec-sub">Probá cualquier combinación de pizzas para verificar precios y descuentos al instante.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        sim_cants = {}
        sim_cols = st.columns(3)
        for idx_s, var_s in enumerate(catalogo_pizzas):
            with sim_cols[idx_s % 3]:
                key_sim = f"sim_cant_{var_s['slug']}"
                default_sim = 1 if var_s["slug"] in ("huevo", "tomate") else 0
                val_sim_actual = int(st.session_state.get(key_sim, default_sim))
                render_pizza_card_top(var_s, val_sim_actual)
                sim_cants[var_s["slug"]] = st.number_input(
                    f"Simular {var_s['nombre']}",
                    min_value=0,
                    step=1,
                    value=default_sim,
                    key=key_sim,
                    label_visibility="collapsed"
                )

        tot_sim, desgl_sim, ahorro_sim = calcular_total_con_promos(sim_cants, catalogo_pizzas, config_promos)
        render_ticket_resumen(sum(sim_cants.values()), desgl_sim, tot_sim, ahorro_sim)


# =========================================================
# PESTAÑA 3: AGENDA DE CLIENTES HABITUALES
# =========================================================
with tab_clientes:
    if "reset_cli_cnt" not in st.session_state:
        st.session_state["reset_cli_cnt"] = 0
    if "msg_cli_ok" in st.session_state:
        st.success(st.session_state.pop("msg_cli_ok"))

    r_cli = st.session_state["reset_cli_cnt"]

    with st.container(border=True):
        st.markdown("""
        <div class="pm-sec-header">
            <div>
                <div class="pm-sec-title">👤 Agendar Nuevo Cliente</div>
                <div class="pm-sec-sub">Guardá clientes frecuentes para seleccionarlos con 1 toque al cargar pedidos.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            ag_nom = st.text_input("Nombre y Apellido *", placeholder="Ej: Juan Pérez", max_chars=80, key=f"nuevo_cli_nom_{r_cli}")
        with ac2:
            ag_tel = st.text_input("Teléfono / WhatsApp", placeholder="Ej: 3573 40-2784", max_chars=25, key=f"nuevo_cli_tel_{r_cli}")
        with ac3:
            ag_dir = st.text_input("Dirección / Entrecalles", placeholder="Ej: Belgrano 1230", max_chars=120, key=f"nuevo_cli_dir_{r_cli}")

        if st.button("💾 Guardar Cliente en la Agenda", type="primary", use_container_width=True):
            if not ag_nom.strip():
                st.warning("⚠️ Escribí al menos el nombre del cliente.")
            else:
                try:
                    with st.spinner("Guardando cliente..."):
                        supabase.table("pizzas_clientes").insert({
                            "nombre": safe_str(ag_nom),
                            "telefono": safe_str(ag_tel),
                            "direccion": safe_str(ag_dir)
                        }).execute()
                        st.cache_data.clear()

                    st.session_state["reset_cli_cnt"] += 1
                    st.session_state["msg_cli_ok"] = f"✅ Cliente **{safe_str(ag_nom)}** guardado en la agenda."
                    st.toast("✅ Cliente guardado", icon="👥")
                    st.rerun()
                except Exception as err:
                    logger.error("Error guardando cliente: %s", str(err), exc_info=True)
                    st.error("⚠️ Error al guardar cliente.")

    st.markdown(f"""
    <div class="pm-sec-header" style="margin-top: 20px;">
        <div>
            <div class="pm-sec-title">📒 Clientes en Agenda ({len(clientes)})</div>
            <div class="pm-sec-sub">Buscá por nombre, calle o teléfono y abrí chat directo en WhatsApp.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if clientes:
        busqueda_cli = st.text_input("🔍 Buscar cliente por nombre, dirección o teléfono:", max_chars=50, key="busq_cli", placeholder="Escribí para filtrar...")
        busq_lower = busqueda_cli.lower().strip()
        clientes_filtrados = [
            c for c in clientes
            if busq_lower in (c.get("nombre") or "").lower()
            or busq_lower in (c.get("direccion") or "").lower()
            or busq_lower in (c.get("telefono") or "").lower()
        ]
        if not clientes_filtrados:
            st.info("No se encontraron clientes con esa búsqueda.")

        clientes_mostrar = clientes_filtrados[:100]
        if len(clientes_filtrados) > 100:
            st.caption(f"Mostrando los primeros 100 de {len(clientes_filtrados)} clientes coincidentes.")

        for c in clientes_mostrar:
            with st.container(border=True):
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    ed_cli_nom = st.text_input("Nombre", value=c.get("nombre") or "", max_chars=80, key=f"cnom_{c['id']}")
                with cc2:
                    ed_cli_tel = st.text_input("Teléfono", value=c.get("telefono") or "", max_chars=25, key=f"ctel_{c['id']}")
                with cc3:
                    ed_cli_dir = st.text_input("Dirección", value=c.get("direccion") or "", max_chars=120, key=f"cdir_{c['id']}")

                cb1, cb2, cb3 = st.columns([2, 2, 1])
                with cb1:
                    if st.button("💾 Guardar Cambios", key=f"save_cli_{c['id']}", use_container_width=True):
                        try:
                            with st.spinner("Actualizando..."):
                                supabase.table("pizzas_clientes").update({
                                    "nombre": safe_str(ed_cli_nom) or c["nombre"],
                                    "telefono": safe_str(ed_cli_tel),
                                    "direccion": safe_str(ed_cli_dir)
                                }).eq("id", c["id"]).execute()
                                st.cache_data.clear()
                            st.toast("✅ Cliente actualizado", icon="👥")
                            st.rerun()
                        except Exception as err:
                            logger.error("Error al actualizar cliente: %s", str(err), exc_info=True)
                            st.error("Error al actualizar cliente.")

                with cb2:
                    tel_wa = limpiar_telefono_argentina(ed_cli_tel or "")
                    if tel_wa:
                        st.link_button(
                            "📲 Abrir WhatsApp",
                            f"https://wa.me/{tel_wa}",
                            use_container_width=True
                        )
                    else:
                        st.button("📵 Sin WhatsApp", disabled=True, key=f"nowa_cli_{c['id']}", use_container_width=True)
                with cb3:
                    with st.popover("🗑️", help="Eliminar cliente"):
                        st.write("¿Eliminar este cliente?")
                        if st.button("Confirmar", key=f"del_confirm_cli_{c['id']}", type="primary", use_container_width=True):
                            try:
                                with st.spinner("Eliminando..."):
                                    supabase.table("pizzas_clientes").delete().eq("id", c["id"]).execute()
                                    st.cache_data.clear()
                                st.toast("🗑️ Cliente eliminado", icon="👥")
                                st.rerun()
                            except Exception as err:
                                logger.error("Error borrando cliente: %s", str(err), exc_info=True)
                                st.error("Error al eliminar cliente.")
    else:
        st.info("Todavía no hay clientes guardados. Cargalos arriba para tenerlos listos cuando arranquen las ventas.")


# =========================================================
# PESTAÑA 4: PRECIOS, VARIEDADES DE PIZZA Y COSTOS (BELÉN)
# =========================================================
with tab_costos:
    st.markdown("""
    <div class="pm-sec-header">
        <div>
            <div class="pm-sec-title">💰 Precios de Lista y Margen por Pizza</div>
            <div class="pm-sec-sub">Comparativa en tiempo real entre el costo de insumos y el precio de venta al público.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cards_rent_html = []
    for var in catalogo_pizzas:
        slug = var["slug"]
        costo_v = costos_pizza["por_variedad"].get(slug, 0.0)
        precio_v = float(var["precio"])
        ganancia_v = precio_v - costo_v
        margen_pct = max(0.0, min(100.0, (ganancia_v / precio_v * 100) if precio_v > 0 else 0.0))
        cards_rent_html.append(
            f'<div class="pm-kpi-card" style="--kpi-accent: #FF6B00;">'
            f'<div class="pm-kpi-label">{var["emoji"]} {safe_html(var["nombre"])}</div>'
            f'<div class="pm-kpi-value">{formato_moneda(precio_v)}</div>'
            f'<div class="pm-kpi-sub" style="color: #34D399;">Ganancia: {formato_moneda(ganancia_v)} ({margen_pct:.0f}%)</div>'
            f'<div style="font-size: 0.76rem; color: #94A3B8; margin-top: 4px;">Costo receta: <b>{formato_moneda(costo_v)}</b></div>'
            f'<div class="pm-progress-track"><div class="pm-progress-fill" style="width: {margen_pct:.0f}%;"></div></div>'
            f'</div>'
        )
    st.markdown(f'<div class="pm-kpi-grid">{"".join(cards_rent_html)}</div>', unsafe_allow_html=True)

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        with st.expander("✏️ Cambiar Precios de Venta Individuales", expanded=False):
            with st.form("form_precios_venta"):
                nuevos_precios = {}
                for var in catalogo_pizzas:
                    nuevos_precios[var["slug"]] = st.number_input(
                        f"{var['emoji']} {var['nombre']} ($)",
                        min_value=0.0,
                        value=float(var["precio"]),
                        step=500.0,
                        format="%.0f",
                        key=f"pv_edit_{var['slug']}"
                    )
                if st.form_submit_button("💾 Guardar Precios", type="primary", use_container_width=True):
                    for var in catalogo_pizzas:
                        var["precio"] = float(nuevos_precios[var["slug"]])
                    try:
                        with st.spinner("Guardando precios..."):
                            guardar_catalogo_pizzas(id_catalogo, catalogo_pizzas)
                        st.toast("✅ Precios actualizados", icon="💰")
                        st.rerun()
                    except Exception as err:
                        logger.error("Error guardando precios: %s", str(err), exc_info=True)
                        st.error("Error al guardar precios.")

    with col_exp2:
        with st.expander("🍕 Agregar / Quitar Variedad de Pizza", expanded=False):
            with st.form("form_nueva_variedad", clear_on_submit=True):
                nv_nombre = st.text_input("Nombre del nuevo estilo *", placeholder="Ej: Fugazzeta, Calabresa, Jamón y Morrón", max_chars=50)
                nv_c1, nv_c2 = st.columns(2)
                with nv_c1:
                    nv_emoji = st.selectbox("Ícono", ["🍕", "🧅", "🌶️", "🥓", "🍄", "🫒", "🧄", "🧀"])
                with nv_c2:
                    nv_precio = st.number_input("Precio de Venta ($)", min_value=0.0, value=10000.0, step=500.0, format="%.0f")

                if st.form_submit_button("➕ Crear Estilo de Pizza", type="primary", use_container_width=True):
                    nombre_limpio = safe_str(nv_nombre)
                    if not nombre_limpio:
                        st.warning("Escribí el nombre de la nueva variedad.")
                    else:
                        nuevo_slug = slugify(nombre_limpio)
                        slugs_actuales = [v["slug"] for v in catalogo_pizzas]
                        if nuevo_slug in slugs_actuales:
                            st.warning("Ya existe una variedad con ese identificador o nombre.")
                        else:
                            catalogo_pizzas.append({
                                "slug": nuevo_slug,
                                "nombre": nombre_limpio,
                                "emoji": nv_emoji,
                                "precio": float(nv_precio),
                                "base": False
                            })
                            try:
                                with st.spinner("Guardando variedad..."):
                                    guardar_catalogo_pizzas(id_catalogo, catalogo_pizzas)
                                st.toast(f"✅ Estilo '{nombre_limpio}' creado", icon="🍕")
                                st.rerun()
                            except Exception as err:
                                logger.error("Error agregando variedad: %s", str(err), exc_info=True)
                                st.error("Error al guardar la nueva variedad.")

            variedades_extra = [v for v in catalogo_pizzas if not v.get("base")]
            if variedades_extra:
                st.markdown("**Variedades agregadas:**")
                for ve in variedades_extra:
                    ce1, ce2 = st.columns([3, 1])
                    with ce1:
                        st.write(f"{ve['emoji']} **{ve['nombre']}** ({formato_moneda(ve['precio'])})")
                    with ce2:
                        with st.popover("🗑️", help="Quitar variedad"):
                            st.write(f"¿Quitar {ve['nombre']}?")
                            if st.button("Confirmar", key=f"del_confirm_var_{ve['slug']}", type="primary"):
                                nuevo_cat = [v for v in catalogo_pizzas if v["slug"] != ve["slug"]]
                                guardar_catalogo_pizzas(id_catalogo, nuevo_cat)
                                st.rerun()

    st.divider()

    # --- CALCULADORA DE INSUMOS DE BELÉN ---
    st.markdown("""
    <div class="pm-sec-header">
        <div>
            <div class="pm-sec-title">⚖️ Calculadora de Costos e Insumos (Recetario)</div>
            <div class="pm-sec-sub">Cargá harinas, muzzarella, salsa, cajas y bolsas por kilo o pack para obtener el costo exacto por pizza.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not insumos:
        with st.container(border=True):
            st.info("💡 **¿Querés arrancar más rápido?** Podés cargar una lista base con los insumos más comunes y después solo editás los precios.")
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
                st.cache_data.clear()
                st.toast("✅ Lista base cargada", icon="⚖️")
                st.rerun()

    with st.container(border=True):
        st.markdown("#### 📝 Cargar un Nuevo Insumo")
        ci1, ci2 = st.columns([2, 2])
        with ci1:
            ins_nombre = st.text_input(
                "Nombre del Insumo *",
                placeholder="Ej: Muzzarella, Harina, Bolsa camiseta, Caja...",
                max_chars=80,
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
                format="%.0f",
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

        cant_segura = max(0.01, ins_cant_bulto)
        costo_unit_preview = ins_precio_bulto / cant_segura
        unidad_preview_txt = "Kilo" if es_nuevo_kg else "Unidad"
        st.caption(f"💡 Costo calculado: **{formato_moneda(costo_unit_preview)} por cada {unidad_preview_txt}**")

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
            nombre_ins_seguro = safe_str(ins_nombre)
            if not nombre_ins_seguro:
                st.warning("⚠️ Escribí el nombre del insumo arriba antes de guardar.")
            else:
                usos_extra_dict = {
                    k: v for k, v in usos_nuevo_ins.items()
                    if k not in ("muzza", "huevo", "tomate") and v > 0
                }
                modo_guardar = empaquetar_modo_insumo(ins_modo, usos_extra_dict)
                try:
                    with st.spinner("Guardando insumo..."):
                        supabase.table("pizzas_insumos").insert({
                            "nombre": nombre_ins_seguro,
                            "modo": modo_guardar,
                            "precio_bulto": float(ins_precio_bulto),
                            "cantidad_bulto": float(ins_cant_bulto),
                            "uso_muzza": float(usos_nuevo_ins.get("muzza", 0.0)),
                            "uso_huevo": float(usos_nuevo_ins.get("huevo", 0.0)),
                            "uso_tomate": float(usos_nuevo_ins.get("tomate", 0.0)),
                        }).execute()
                        st.cache_data.clear()
                    st.toast(f"✅ Insumo '{nombre_ins_seguro}' guardado", icon="⚖️")
                    st.rerun()
                except Exception as err:
                    logger.error("Error guardando insumo: %s", str(err), exc_info=True)
                    st.error("Error al registrar insumo.")

    st.markdown(f"""
    <div class="pm-sec-header" style="margin-top: 20px;">
        <div>
            <div class="pm-sec-title">📋 Insumos Activos ({len(insumos)})</div>
            <div class="pm-sec-sub">Actualizá el precio de compra de cualquier bulto y el costo de todas las pizzas se recalculará al instante.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if insumos:
        for ins, det in zip(insumos, costos_pizza["detalle"]):
            es_kg = det["modo_base"] == "kg"
            unidad_txt = "kg" if es_kg else "unid."
            resumen_costos_var = " · ".join(
                f"{v['emoji']} {v['nombre']}: **{formato_moneda(det['costos_variedad'].get(v['slug'], 0))}**"
                for v in catalogo_pizzas
            )

            with st.container(border=True):
                st.markdown(f"##### 🔧 {safe_str(ins['nombre'])}  *(Costo unitario: {formato_moneda(det['Costo x Kg/Unid'])} / {unidad_txt})*")
                st.caption(f"Impacto por pizza: {resumen_costos_var}")

                ec0, ec1, ec2, ec3 = st.columns([2, 2, 2, 2], vertical_alignment="bottom")
                with ec0:
                    ed_nombre = st.text_input(
                        "Nombre",
                        value=ins["nombre"],
                        max_chars=80,
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
                        format="%.0f",
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
                        try:
                            with st.spinner("Actualizando insumo..."):
                                supabase.table("pizzas_insumos").update({
                                    "nombre": safe_str(ed_nombre) or ins["nombre"],
                                    "modo": modo_ed_empaquetado,
                                    "precio_bulto": float(ed_precio),
                                    "cantidad_bulto": max(0.01, float(ed_cant)),
                                    "uso_muzza": float(ed_usos.get("muzza", 0.0)),
                                    "uso_huevo": float(ed_usos.get("huevo", 0.0)),
                                    "uso_tomate": float(ed_usos.get("tomate", 0.0))
                                }).eq("id", ins["id"]).execute()
                                st.cache_data.clear()
                            st.toast(f"✅ Insumo '{safe_str(ed_nombre)}' actualizado", icon="⚖️")
                            st.rerun()
                        except Exception as err:
                            logger.error("Error al actualizar insumo: %s", str(err), exc_info=True)
                            st.error("Error al actualizar insumo.")
                with eb2:
                    with st.popover("🗑️", help="Eliminar insumo"):
                        st.write("¿Eliminar este insumo definitivamente?")
                        if st.button("Confirmar", key=f"del_confirm_ins_{ins['id']}", type="primary"):
                            try:
                                with st.spinner("Eliminando..."):
                                    supabase.table("pizzas_insumos").delete().eq("id", ins["id"]).execute()
                                    st.cache_data.clear()
                                st.toast("🗑️ Insumo eliminado", icon="⚖️")
                                st.rerun()
                            except Exception as err:
                                logger.error("Error al borrar insumo: %s", str(err), exc_info=True)
                                st.error("Error al eliminar insumo.")
    else:
        st.info("Todavía no hay insumos cargados. Usá el botón rápido de arriba o completá el cuadro '📝 Cargar un Nuevo Insumo'.")


# =========================================================
# PESTAÑA 5: CAJA / DÍA (PRODUCCIÓN, WHATSAPP Y COMANDAS)
# =========================================================
with tab_caja:
    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        fecha_filtro = st.date_input("📅 Fecha de jornada", value=date.today(), format="DD/MM/YYYY", key="fecha_caja")
    with col_f2:
        filtro_estado = st.selectbox(
            "🔍 Filtrar comandas por estado",
            options=["Todos", "Pendientes de entrega", "Pendientes de cobro", "Entregados", "Cancelados"]
        )

    try:
        res_pedidos = (
            supabase.table("pizzas_pedidos")
            .select("*")
            .eq("fecha", str(fecha_filtro))
            .order("created_at", desc=True)
            .execute()
        )
        pedidos_dia = res_pedidos.data or []
    except Exception as e:
        logger.error("Error obteniendo pedidos de caja: %s", str(e), exc_info=True)
        pedidos_dia = []

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
    entregadas_pizzas = max(0, tot_pizzas - pend_pizzas)
    pct_entregadas = (entregadas_pizzas / tot_pizzas * 100) if tot_pizzas > 0 else 0

    plata_total = sum(float(p.get("total_plata") or 0) for p in pedidos_activos)
    plata_efectivo = sum(float(p.get("total_plata") or 0) for p in pedidos_activos if p.get("metodo_pago") == "efectivo")
    plata_transf = sum(float(p.get("total_plata") or 0) for p in pedidos_activos if p.get("metodo_pago") == "transferencia")
    plata_pendiente = sum(float(p.get("total_plata") or 0) for p in pedidos_activos if p.get("metodo_pago") == "pendiente")

    costo_mercaderia_dia = sum(
        totales_por_estilo[v["slug"]] * costos_pizza["por_variedad"].get(v["slug"], 0.0)
        for v in catalogo_pizzas
    )
    ganancia_neta_dia = plata_total - costo_mercaderia_dia

    # --- BLOQUE 1: MONITOR DE HORNO Y PRODUCCIÓN ---
    st.markdown(f"""
    <div class="pm-oven-banner">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #FF8533; text-transform: uppercase; letter-spacing: 0.06em;">
                    🔥 MONITOR DE HORNO · {formatear_fecha_ar(fecha_filtro)}
                </div>
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.75rem; font-weight: 800; color: #FFFFFF; margin-top: 2px;">
                    {tot_pizzas} Pizzas en Total
                </div>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="pm-badge pm-badge-pendiente">🕒 {pend_pizzas} por salir</span>
                <span class="pm-badge pm-badge-entregado">✅ {entregadas_pizzas} entregadas ({pct_entregadas:.0f}%)</span>
            </div>
        </div>
        <div class="pm-progress-track">
            <div class="pm-progress-fill" style="width: {pct_entregadas:.0f}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cards_prod_html = []
    for var in catalogo_pizzas:
        slug = var["slug"]
        t_v = totales_por_estilo[slug]
        p_v = pendientes_por_estilo[slug]
        sub_color = "#FBBF24" if p_v > 0 else "#34D399"
        sub_txt = f"🕒 {p_v} pendientes de hornear" if p_v > 0 else "✅ Todo entregado"
        cards_prod_html.append(
            f'<div class="pm-kpi-card" style="--kpi-accent: #FF6B00;">'
            f'<div class="pm-kpi-label">{var["emoji"]} {safe_html(var["nombre"])}</div>'
            f'<div class="pm-kpi-value">{t_v} <span style="font-size: 0.95rem; font-weight: 600; color: #94A3B8;">pizzas</span></div>'
            f'<div class="pm-kpi-sub" style="color: {sub_color};">{sub_txt}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="pm-kpi-grid">{"".join(cards_prod_html)}</div>', unsafe_allow_html=True)

    # --- BLOQUE 2: RESUMEN DE CAJA FINANCIERO ---
    st.markdown(f"""
    <div class="pm-sec-header">
        <div>
            <div class="pm-sec-title">💵 Balance de Caja del Día</div>
            <div class="pm-sec-sub">Ingresos según medio de cobro y ganancia limpia descontando insumos.</div>
        </div>
    </div>
    <div class="pm-kpi-grid">
        <div class="pm-kpi-card" style="--kpi-accent: #FF6B00;">
            <div class="pm-kpi-label">💰 VENTA TOTAL</div>
            <div class="pm-kpi-value">{formato_moneda(plata_total)}</div>
            <div class="pm-kpi-sub" style="color: #FF8533;">{len(pedidos_activos)} pedidos activos</div>
        </div>
        <div class="pm-kpi-card" style="--kpi-accent: #0EA5E9;">
            <div class="pm-kpi-label">🏦 TRANSFERENCIA</div>
            <div class="pm-kpi-value">{formato_moneda(plata_transf)}</div>
            <div class="pm-kpi-sub" style="color: #38BDF8;"> acreditado digital</div>
        </div>
        <div class="pm-kpi-card" style="--kpi-accent: #10B981;">
            <div class="pm-kpi-label">💵 EFECTIVO</div>
            <div class="pm-kpi-value">{formato_moneda(plata_efectivo)}</div>
            <div class="pm-kpi-sub" style="color: #34D399;">en mano / mostrador</div>
        </div>
        <div class="pm-kpi-card" style="--kpi-accent: #F59E0B;">
            <div class="pm-kpi-label">⏳ FALTA COBRAR</div>
            <div class="pm-kpi-value">{formato_moneda(plata_pendiente)}</div>
            <div class="pm-kpi-sub" style="color: #34D399;">Ganancia neta: {formato_moneda(ganancia_neta_dia)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- BOTÓN PARA ENVIAR RESUMEN POR WHATSAPP ---
    with st.container(border=True):
        st.markdown("##### 📲 Exportar Reporte del Día por WhatsApp")
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            wa_solo_pend = st.checkbox("Solo pizzas pendientes", value=False)
        with w_col2:
            wa_inc_clientes = st.checkbox("Incluir lista de clientes", value=True)
        with w_col3:
            wa_inc_caja = st.checkbox("Incluir resumen de caja ($)", value=True)

        wa_tel_destino = st.text_input(
            "N° de WhatsApp destino (opcional — dejalo vacío para elegir el chat al abrir WhatsApp):",
            placeholder="Ej: 3573 40-2784",
            max_chars=25
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

        num_normalizado = limpiar_telefono_argentina(wa_tel_destino)
        url_wa_resumen = (
            f"https://wa.me/{num_normalizado}?text={quote(texto_wa_dia)}"
            if num_normalizado
            else f"https://wa.me/?text={quote(texto_wa_dia)}"
        )

        st.link_button(
            f"📲 Enviar Resumen del Día ({fecha_filtro.strftime('%d/%m/%Y')}) por WhatsApp",
            url_wa_resumen,
            type="primary",
            use_container_width=True
        )
        with st.expander("👁️ Ver vista previa del mensaje de WhatsApp"):
            st.code(texto_wa_dia, language=None)

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

    # --- BLOQUE 3: COMANDAS Y CIERRE DE VENTAS DEL DÍA ---
    st.markdown("""
    <div class="pm-sec-header" style="margin-top: 18px;">
        <div>
            <div class="pm-sec-title">📋 Tablero de Comandas y Entregas</div>
            <div class="pm-sec-sub">Cambiá el estado de entrega o cobro con un toque o editá el pedido completo.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
            if st.session_state.get("editando_pedido_id") == p["id"]:
                with st.container(border=True):
                    render_formulario_editar_pedido(p, catalogo_pizzas, config_promos, contexto="tab_caja")
            else:
                est_actual, extras_actuales = parsear_estado_y_extras_pedido(p.get("estado_entrega", "pendiente"))

                partes_pizza = []
                for v in catalogo_pizzas:
                    c_v = obtener_cantidad_pedido_variedad(p, v["slug"])
                    if c_v > 0:
                        partes_pizza.append(f"{c_v} {v['nombre']}")
                resumen_plano = ", ".join(partes_pizza)

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

                with st.container(border=True):
                    render_comanda_card_header(p, catalogo_pizzas)

                    b1, b2, b3, b4, b5 = st.columns([3, 3, 2, 2, 1], vertical_alignment="bottom")
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
                            key=f"est_ped_{p['id']}",
                            label_visibility="collapsed"
                        )
                    with b2:
                        nuevo_pago = st.selectbox(
                            "Método de Pago",
                            options=pagos_opc,
                            index=pagos_opc.index(pago_actual),
                            format_func=lambda x: etiquetas_pago.get(x, x.capitalize()),
                            key=f"pago_ped_{p['id']}",
                            label_visibility="collapsed"
                        )
                    with b3:
                        url_wa = link_whatsapp_cliente(
                            p.get("telefono") or "",
                            p["nombre_cliente"],
                            resumen_plano,
                            float(p.get("total_plata") or 0)
                        )
                        if url_wa:
                            st.link_button("📲 WhatsApp", url_wa, use_container_width=True)
                        else:
                            st.button("📵 Sin Tel.", disabled=True, key=f"no_wa_{p['id']}", use_container_width=True)
                    with b4:
                        if st.button("✏️ Editar", key=f"btn_edit_caja_{p['id']}", use_container_width=True):
                            st.session_state["editando_pedido_id"] = p["id"]
                            st.rerun()
                    with b5:
                        with st.popover("🗑️", help="Eliminar pedido definitivamente"):
                            st.write("¿Eliminar este pedido?")
                            if st.button("Confirmar", key=f"del_confirm_caja_{p['id']}", type="primary", use_container_width=True):
                                try:
                                    with st.spinner("Eliminando..."):
                                        supabase.table("pizzas_pedidos").delete().eq("id", p["id"]).execute()
                                        st.cache_data.clear()
                                    st.toast("🗑️ Pedido eliminado", icon="🍕")
                                    st.rerun()
                                except Exception as err:
                                    logger.error("Error al eliminar pedido: %s", str(err), exc_info=True)
                                    st.error("Error al eliminar pedido.")

                    if nuevo_est != est_actual or nuevo_pago != pago_actual:
                        nuevo_estado_empaquetado = empaquetar_estado_y_extras_pedido(nuevo_est, extras_actuales)
                        try:
                            supabase.table("pizzas_pedidos").update({
                                "estado_entrega": nuevo_estado_empaquetado,
                                "metodo_pago": nuevo_pago
                            }).eq("id", p["id"]).execute()
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as err:
                            logger.error("Error al actualizar estado/pago: %s", str(err), exc_info=True)
                            st.error("Error al actualizar estado.")
