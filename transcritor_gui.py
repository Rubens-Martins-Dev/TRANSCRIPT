import streamlit as st
import whisper
import tempfile
import os
from pathlib import Path

# Configuração da página
st.set_page_config(page_title="Transcritor Whisper", layout="centered")

st.markdown("""
    <h1 style='text-align:center; color:white;'>Transcritor Whisper Online</h1>
""", unsafe_allow_html=True)

# Estilo escuro
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
        }
        .stTextArea textarea {
            background-color: #2d2d2d !important;
            color: white !important;
            border-radius: 8px;
            font-size: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# Adiciona ffmpeg ao PATH se não estiver
ffmpeg_path = "/usr/bin"
if ffmpeg_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{ffmpeg_path}:{os.environ.get('PATH', '')}"

# Upload de arquivo
arquivo = st.file_uploader(
    "Envie um arquivo de áudio ou vídeo (melhor com MP3 ou WAV)",
    type=["mp3", "wav", "mp4", "m4a", "mov", "mpeg"]
)

# Carregar modelo só uma vez
@st.cache_resource
def carregar_modelo():
    return whisper.load_model("tiny")

modelo = carregar_modelo()

# Inicializar variável no session_state
if 'texto_final' not in st.session_state:
    st.session_state.texto_final = ""

if arquivo is not None:
    # Salvar arquivo temporário com extensão correta
    suffix = Path(arquivo.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(arquivo.read())
        caminho_temp = tmp.name

    st.info("Transcrevendo... Aguarde ⏳")
    
    progress_bar = st.progress(0)
    
    try:
        # Configurar whisper para não usar fp16 (incompatível com CPU)
        progress_bar.progress(30)
        
        resultado = modelo.transcribe(
            caminho_temp,
            language="pt",
            fp16=False,
            verbose=False
        )
        
        progress_bar.progress(100)
        st.session_state.texto_final = resultado["text"]
        st.success("✅ Transcrição concluída!")
        
    except FileNotFoundError as e:
        st.error("❌ FFmpeg não encontrado. Tentando método alternativo...")
        st.info("💡 Por favor, tente enviar apenas arquivos MP3 ou WAV")
        st.code(str(e), language="text")
        
    except Exception as e:
        st.error(f"❌ Erro ao transcrever: {str(e)}")
        st.info("💡 Sugestões:")
        st.write("- Tente converter o arquivo para MP3")
        st.write("- Certifique-se de que o arquivo não está corrompido")
        st.write("- Tente com um arquivo menor (< 25MB)")
        
    finally:
        # Limpar arquivo temporário
        try:
            if os.path.exists(caminho_temp):
                os.unlink(caminho_temp)
        except:
            pass
        
        # Remover barra de progresso
        progress_bar.empty()

# Mostrar texto transcrito
if st.session_state.texto_final:
    st.text_area("Resultado", st.session_state.texto_final, height=350, key="resultado")

    col1, col2 = st.columns(2)
    
    with col1:
        st.info("💡 Selecione o texto e copie (Ctrl+C)")

    with col2:
        st.download_button(
            label="💾 Baixar .txt",
            data=st.session_state.texto_final,
            file_name="transcricao.txt",
            mime="text/plain"
        )
    
    # Botão para limpar
    if st.button("🗑️ Nova transcrição"):
        st.session_state.texto_final = ""
        st.rerun()