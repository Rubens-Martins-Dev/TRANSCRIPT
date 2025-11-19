import streamlit as st
import whisper
import tempfile
import os
import sys

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

# Upload de arquivo
arquivo = st.file_uploader(
    "Envie um arquivo de áudio ou vídeo",
    type=["mp3", "wav", "mp4", "m4a", "mov"]
)

# Carregar modelo só uma vez (usando modelo tiny para economizar memória)
@st.cache_resource
def carregar_modelo():
    return whisper.load_model("tiny")

modelo = carregar_modelo()

# Inicializar variável no session_state
if 'texto_final' not in st.session_state:
    st.session_state.texto_final = ""

if arquivo is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.name)[1]) as tmp:
        tmp.write(arquivo.read())
        caminho_temp = tmp.name

    st.info("Transcrevendo... Aguarde ⏳")

    try:
        # Transcrever com configurações otimizadas
        resultado = modelo.transcribe(
            caminho_temp, 
            fp16=False,
            language="pt"  # Força português para melhor precisão
        )
        st.session_state.texto_final = resultado["text"]
        st.success("✅ Transcrição concluída!")
    except Exception as e:
        st.error(f"Erro ao transcrever: {str(e)}")
        st.info("💡 Tente converter o arquivo para MP3 antes de enviar")
    finally:
        # Limpar arquivo temporário
        try:
            if os.path.exists(caminho_temp):
                os.unlink(caminho_temp)
        except:
            pass

# Mostrar texto transcrito
if st.session_state.texto_final:
    st.text_area("Resultado", st.session_state.texto_final, height=350)

    st.info("💡 Selecione o texto acima e copie com Ctrl+C (ou Cmd+C no Mac)")

    st.download_button(
        label="💾 Baixar .txt",
        data=st.session_state.texto_final,
        file_name="transcricao.txt",
        mime="text/plain"
    )