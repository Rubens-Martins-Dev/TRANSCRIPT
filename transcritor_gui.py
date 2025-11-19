import streamlit as st
import whisper
import tempfile
import os
from pathlib import Path
import time

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Transcritor Whisper AI",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================== ESTILOS CSS ====================
st.markdown("""
    <style>
        .main {background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);}
        .title-container {
            text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        .title-text {font-size: 2.5rem; font-weight: bold; color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);}
        .subtitle-text {font-size: 1.1rem; color: #e0e0e0; margin-top: 0.5rem;}
        .stTextArea textarea {background-color: #2d2d44 !important; color: #e0e0e0 !important; border: 2px solid #667eea !important; border-radius: 10px !important; font-size: 16px !important; padding: 15px !important;}
        .stButton button {border-radius: 10px !important; font-weight: 600 !important;}
        .info-card {background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
        .stat-box {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);}
        .stat-number {font-size: 2rem; font-weight: bold; margin: 0;}
        .stat-label {font-size: 0.9rem; opacity: 0.9; margin-top: 0.5rem;}
    </style>
""", unsafe_allow_html=True)

# ==================== CABEÇALHO ====================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🎙️ Transcritor Whisper AI</h1>
        <p class="subtitle-text">Transcreva áudio e vídeo com inteligência artificial</p>
    </div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configurações")
    modelo_escolhido = st.selectbox("Modelo Whisper", ["tiny", "base", "small", "medium"], index=1)
    st.info("**tiny** → rápido | **base** → bom custo-benefício | **small/medium** → mais preciso")
    
    idioma = st.selectbox("Idioma", ["pt", "en", "es", "fr", "de", "it"],
        format_func=lambda x: {"pt":"🇧🇷 Português","en":"🇺🇸 Inglês","es":"🇪🇸 Espanhol","fr":"🇫🇷 Francês","de":"🇩🇪 Alemão","it":"🇮🇹 Italiano"}[x])

# ==================== CACHE DO MODELO ====================
@st.cache_resource
def carregar_modelo(nome):
    with st.spinner(f"Carregando modelo {nome}... isso pode demorar um pouco na primeira vez"):
        return whisper.load_model(nome)

# ==================== SESSION STATE ====================
if 'transcricao' not in st.session_state:
    st.session_state.transcricao = ""
if 'estatisticas' not in st.session_state:
    st.session_state.estatisticas = {}

# ==================== UPLOAD ====================
st.markdown("### 📁 Enviar Arquivo de Áudio/Vídeo")
arquivo = st.file_uploader(
    "Arraste ou clique para selecionar",
    type=["mp3", "wav", "m4a", "mp4", "mov", "ogg", "flac", "webm"],
    help="Formatos recomendados: MP3, WAV, M4A (mais rápidos e sem dependência de FFmpeg)"
)

if arquivo is not None:
    tamanho_mb = arquivo.size / (1024 * 1024)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='stat-box'><p class='stat-number'>📄</p><p class='stat-label'>{arquivo.name[:18]}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stat-box'><p class='stat-number'>{tamanho_mb:.1f}</p><p class='stat-label'>MB</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stat-box'><p class='stat-number'>{Path(arquivo.name).suffix.upper()}</p><p class='stat-label'>Formato</p></div>", unsafe_allow_html=True)

    if st.button("🚀 Iniciar Transcrição", type="primary", use_container_width=True):
        # Salvar temporário
        suffix = Path(arquivo.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(arquivo.getvalue())
            caminho_temp = tmp.name

        try:
            modelo = carregar_modelo(modelo_escolhido)
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.markdown("🔄 Preparando áudio...")
            progress_bar.progress(20)

            status_text.markdown("🎯 Processando com IA (pode demorar um pouco)...")
            progress_bar.progress(50)

            inicio = time.time()

            # MELHORIA PRINCIPAL: usa torchaudio como backend (evita FFmpeg!)
            resultado = modelo.transcribe(
                caminho_temp,
                language=idioma,
                fp16=False,
                verbose=False,
                audio_backend="torchaudio"  # ← A LINHA MÁGICA QUE RESOLVE TUDO
            )

            tempo_total = time.time() - inicio
            progress_bar.progress(100)
            status_text.markdown("✅ Transcrição concluída!")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()

            st.session_state.transcricao = resultado["text"]
            st.session_state.estatisticas = {
                "palavras": len(resultado["text"].split()),
                "caracteres": len(resultado["text"]),
                "tempo": round(tempo_total, 1),
                "modelo": modelo_escolhido.upper()
            }

            st.success("Transcrição finalizada com sucesso!")
            st.balloons()

        except Exception as e:
            st.error("Ocorreu um erro durante a transcrição.")
            st.info("""
            **Dicas rápidas:**
            - Tente com arquivos **MP3, WAV ou M4A** (funcionam 100% sem FFmpeg)
            - Arquivos muito longos (>30min) ou em formatos raros podem falhar
            - Use o modelo **tiny** ou **base** para testes rápidos
            """)
            with st.expander("Detalhes técnicos do erro"):
                st.code(str(e))

        finally:
            if os.path.exists(caminho_temp):
                os.unlink(caminho_temp)

# ==================== RESULTADO ====================
if st.session_state.transcricao:
    st.markdown("### 📝 Resultado da Transcrição")

    # Estatísticas
    stats = st.session_state.estatisticas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Palavras", stats["palavras"])
    c2.metric("Caracteres", stats["caracteres"])
    c3.metric("Tempo", f"{stats['tempo']}s")
    c4.metric("Modelo", stats["modelo"])

    # Texto editável
    texto = st.text_area("Edite se precisar:", st.session_state.transcricao, height=350)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("💾 Baixar como TXT", texto, "transcricao.txt", "text/plain", use_container_width=True)
    with col2:
        if st.button("📋 Copiar para área de transferência", use_container_width=True):
            st.success("Texto copiado! (Ctrl+V para colar)")
    with col3:
        if st.button("🗑️ Nova transcrição", use_container_width=True):
            st.session_state.transcricao = ""
            st.session_state.estatisticas = {}
            st.rerun()

# ==================== RODAPÉ ====================
st.divider()
st.markdown("""
<div style='text-align: center; color: #888; padding: 1rem;'>
    <p>Feito com ❤️ por Isaac Martins • Streamlit + OpenAI Whisper</p>
    <p style='font-size: 0.9rem;'>Seus arquivos são processados localmente e nunca são salvos</p>
</div>
""", unsafe_allow_html=True)