import streamlit as st
import whisper
import tempfile
import os
from pathlib import Path
import time

# Configuração da página
st.set_page_config(
    page_title="Transcritor Whisper AI",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilos customizados
st.markdown("""
    <style>
        /* Tema escuro moderno */
        .main {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        }
        
        /* Título principal */
        .title-container {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        
        .title-text {
            font-size: 2.5rem;
            font-weight: bold;
            color: white;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle-text {
            font-size: 1.1rem;
            color: #e0e0e0;
            margin-top: 0.5rem;
        }
        
        /* Área de texto */
        .stTextArea textarea {
            background-color: #2d2d44 !important;
            color: #e0e0e0 !important;
            border: 2px solid #667eea !important;
            border-radius: 10px !important;
            font-size: 16px !important;
            font-family: 'Segoe UI', sans-serif !important;
            padding: 15px !important;
        }
        
        /* Botões */
        .stButton button {
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        /* Cards de informação */
        .info-card {
            background: rgba(102, 126, 234, 0.1);
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Estatísticas */
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            margin: 0;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🎙️ Transcritor Whisper AI</h1>
        <p class="subtitle-text">Transcreva áudio e vídeo com inteligência artificial</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    modelo_escolhido = st.selectbox(
        "Modelo Whisper",
        ["tiny", "base", "small", "medium"],
        index=0,
        help="Modelos maiores são mais precisos, mas mais lentos"
    )
    
    st.info("""
    **Tamanhos dos modelos:**
    - 🚀 tiny: Rápido (~75MB)
    - ⚡ base: Equilibrado (~142MB)
    - 💎 small: Preciso (~466MB)
    - 🎯 medium: Muito preciso (~1.5GB)
    """)
    
    idioma = st.selectbox(
        "Idioma",
        ["pt", "en", "es", "fr", "de", "it"],
        format_func=lambda x: {
            "pt": "🇧🇷 Português",
            "en": "🇺🇸 Inglês",
            "es": "🇪🇸 Espanhol",
            "fr": "🇫🇷 Francês",
            "de": "🇩🇪 Alemão",
            "it": "🇮🇹 Italiano"
        }[x]
    )
    
    st.divider()
    
    st.markdown("""
    ### 📋 Formatos suportados
    - 🎵 Áudio: MP3, WAV, M4A
    - 🎬 Vídeo: MP4, MOV, MPEG
    
    ### 💡 Dicas
    - Arquivos menores são mais rápidos
    - Áudio limpo = melhor transcrição
    - Modelo tiny é ótimo para testes
    """)

# Garantir ffmpeg no PATH
ffmpeg_path = "/usr/bin"
if ffmpeg_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{ffmpeg_path}:{os.environ.get('PATH', '')}"

# Cache do modelo
@st.cache_resource
def carregar_modelo(nome_modelo):
    with st.spinner(f"Carregando modelo {nome_modelo}... ⏳"):
        return whisper.load_model(nome_modelo)

# Inicializar session state
if 'transcricao' not in st.session_state:
    st.session_state.transcricao = ""
if 'estatisticas' not in st.session_state:
    st.session_state.estatisticas = {}

# Upload de arquivo
st.markdown("### 📁 Enviar Arquivo")
arquivo = st.file_uploader(
    "Arraste seu arquivo aqui ou clique para selecionar",
    type=["mp3", "wav", "mp4", "m4a", "mov", "mpeg", "ogg", "flac"],
    help="Tamanho máximo recomendado: 100MB"
)

# Processar arquivo
if arquivo is not None:
    # Mostrar informações do arquivo
    col1, col2, col3 = st.columns(3)
    
    tamanho_mb = arquivo.size / (1024 * 1024)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <p class="stat-number">📄</p>
            <p class="stat-label">{arquivo.name[:20]}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <p class="stat-number">{tamanho_mb:.1f}</p>
            <p class="stat-label">MB</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <p class="stat-number">{Path(arquivo.name).suffix.upper()}</p>
            <p class="stat-label">Formato</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Botão para iniciar transcrição
    if st.button("🚀 Iniciar Transcrição", type="primary", use_container_width=True):
        # Salvar arquivo temporário
        suffix = Path(arquivo.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(arquivo.read())
            caminho_temp = tmp.name
        
        try:
            # Carregar modelo
            modelo = carregar_modelo(modelo_escolhido)
            
            # Barra de progresso animada
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            progress_text.markdown("🔄 Preparando transcrição...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            progress_text.markdown("🎯 Processando áudio...")
            progress_bar.progress(40)
            
            # Transcrever
            inicio = time.time()
            resultado = modelo.transcribe(
                caminho_temp,
                language=idioma,
                fp16=False,
                verbose=False
            )
            tempo_total = time.time() - inicio
            
            progress_bar.progress(100)
            progress_text.markdown("✅ Transcrição concluída!")
            time.sleep(1)
            
            # Salvar resultado
            st.session_state.transcricao = resultado["text"]
            st.session_state.estatisticas = {
                "palavras": len(resultado["text"].split()),
                "caracteres": len(resultado["text"]),
                "tempo": tempo_total,
                "modelo": modelo_escolhido
            }
            
            progress_text.empty()
            progress_bar.empty()
            
            st.success("🎉 Transcrição finalizada com sucesso!")
            st.balloons()
            
        except FileNotFoundError as e:
            st.error("❌ FFmpeg não encontrado no sistema")
            st.info("💡 Tente usar arquivos MP3 ou WAV que não requerem conversão")
            with st.expander("Detalhes do erro"):
                st.code(str(e))
                
        except Exception as e:
            st.error(f"❌ Erro durante a transcrição: {str(e)}")
            st.info("""
            **Possíveis soluções:**
            - Converta o arquivo para MP3
            - Verifique se o arquivo não está corrompido
            - Tente com um arquivo menor
            - Use um modelo menor (tiny ou base)
            """)
            
        finally:
            # Limpar arquivo temporário
            try:
                if os.path.exists(caminho_temp):
                    os.unlink(caminho_temp)
            except:
                pass

# Mostrar resultado da transcrição
if st.session_state.transcricao:
    st.markdown("### 📝 Resultado da Transcrição")
    
    # Estatísticas
    if st.session_state.estatisticas:
        stats = st.session_state.estatisticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Palavras", stats.get("palavras", 0))
        with col2:
            st.metric("Caracteres", stats.get("caracteres", 0))
        with col3:
            st.metric("Tempo", f"{stats.get('tempo', 0):.1f}s")
        with col4:
            st.metric("Modelo", stats.get("modelo", "N/A").upper())
    
    # Área de texto
    texto_editado = st.text_area(
        "Edite o texto se necessário:",
        st.session_state.transcricao,
        height=300,
        key="area_texto"
    )
    
    # Atualizar transcrição se editada
    st.session_state.transcricao = texto_editado
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="💾 Baixar TXT",
            data=st.session_state.transcricao,
            file_name="transcricao.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        if st.button("📋 Copiar", use_container_width=True):
            st.toast("✅ Texto copiado! Use Ctrl+V para colar")
    
    with col3:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.transcricao = ""
            st.session_state.estatisticas = {}
            st.rerun()

# Rodapé
st.divider()
st.markdown("""
    <div style='text-align: center; color: #888; padding: 1rem;'>
        <p>Desenvolvido com ❤️ usando Streamlit e OpenAI Whisper</p>
        <p style='font-size: 0.9rem;'>🔒 Seus arquivos são processados localmente e não são armazenados</p>
    </div>
""", unsafe_allow_html=True)