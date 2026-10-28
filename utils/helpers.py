import streamlit as st
from config import APP_NAME, APP_TAGLINE

def apply_custom_css():
    """Apply modern SaaS styling, dark theme accents, glassmorphism, and responsive layout."""
    css = """
    <style>
    /* Main App Background & Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Gradient & Tagline Styling */
    .app-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 1.8rem 2rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.3);
    }
    .app-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff;
    }
    .app-tagline {
        font-size: 0.95rem;
        color: #c7d2fe;
        margin-top: 0.4rem;
        font-weight: 400;
    }
    
    /* Card Component */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4338ca;
        line-height: 1;
    }
    .metric-lbl {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }

    /* Badges */
    .badge-strong {
        background-color: #dcfce7;
        color: #15803d;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-moderate {
        background-color: #fef9c3;
        color: #a16207;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-weak {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }

    /* Source Citation Pill */
    .source-box {
        background-color: #f8fafc;
        border-left: 4px solid #6366f1;
        padding: 0.8rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.8rem;
        font-size: 0.85rem;
        color: #334155;
    }
    
    /* Custom Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        color: #f8fafc;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #e2e8f0 !important;
    }
    
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_header(title_suffix: str = ""):
    """Render application header banner."""
    title = APP_NAME
    if title_suffix:
        title += f" — {title_suffix}"
    
    html = f"""
    <div class="app-header">
        <div class="app-title">⚡ {title}</div>
        <div class="app-tagline">{APP_TAGLINE}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
