import streamlit as st
import os
import zipfile
import io
from dotenv import load_dotenv

from summarizer import (
    generate_article, 
    generate_webpage, 
    parse_webpage_output
)

load_dotenv()

st.set_page_config(page_title="Gemini YouTube Summarizer", page_icon="🎬", layout="wide")

# Custom CSS for Premium UI/UX
st.markdown("""
    <style>
        /* Import premium fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Sora:wght@400;600;700;800&display=swap');
        
        /* Global Font Overrides */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        h1, h2, h3, .main-hero {
            font-family: 'Sora', sans-serif !important;
        }
        
        /* Main Title Styling */
        .main-hero {
            text-align: center;
            padding: 2.5rem 0 0.5rem 0;
            background: linear-gradient(135deg, #7C3AED 0%, #C026D3 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
        }
        
        .sub-hero {
            text-align: center;
            color: #94A3B8;
            font-size: 1.25rem;
            margin-bottom: 3.5rem;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.6;
        }

        /* Input Field Styling - Glassmorphism */
        div[data-baseweb="input"] {
            border-radius: 16px;
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(12px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            padding: 4px;
        }
        div[data-baseweb="input"]:focus-within {
            border-color: #7C3AED !important;
            box-shadow: 0 0 25px rgba(124, 58, 237, 0.2) !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
        }

        /* Button Styling - Premium Gradient */
        button[kind="primary"] {
            background: linear-gradient(135deg, #7C3AED 0%, #C026D3 100%) !important;
            border: none !important;
            border-radius: 16px !important;
            font-weight: 700 !important;
            height: 3.5rem !important;
            font-size: 1.1rem !important;
            letter-spacing: 0.5px !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
        }
        button[kind="primary"]:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 30px rgba(124, 58, 237, 0.4) !important;
        }
        button[kind="primary"]:active {
            transform: translateY(-1px) scale(0.98);
        }

        /* Tabs Styling - Minimalist Glass */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
            border-radius: 12px 12px 0 0 !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 10px 24px !important;
            color: #94A3B8 !important;
            transition: all 0.3s ease !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #F8FAFC !important;
            background-color: rgba(124, 58, 237, 0.1) !important;
            border-bottom: 3px solid #7C3AED !important;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Secondary Button (Download) */
        button[kind="secondary"] {
            border-radius: 16px !important;
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            padding: 0.75rem 1.5rem !important;
        }
        button[kind="secondary"]:hover {
            border-color: #7C3AED !important;
            background-color: rgba(124, 58, 237, 0.1) !important;
            color: #F8FAFC !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Status Elements */
        div[data-testid="stStatus"] {
            background-color: rgba(124, 58, 237, 0.05) !important;
            border: 1px solid rgba(124, 58, 237, 0.2) !important;
            border-radius: 16px !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-hero">🎬 YouTube Article Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-hero">Instantly transform any long-form video into a premium blog post and fully coded web page.</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_google = os.getenv("GOOGLE_API_KEY")
    
    if not api_key_google or "your_" in api_key_google:
        user_key = st.text_input("Enter Gemini API Key", type="password")
        if user_key:
            os.environ["GOOGLE_API_KEY"] = user_key
            st.success("API Key updated!")
    else:
        st.success("✅ Gemini API Key Found")

    model_name = st.selectbox("Select Gemini Model", ["gemini-2.5-flash", "gemini-2.5-pro"], index=0)
    
    if not os.path.exists("cookies.txt"):
        st.divider()
        st.markdown("**🛡️ Server Authorization Required**")
        uploaded_cookies = st.file_uploader("Upload cookies.txt file", type=["txt"], help="Admin Only: Upload cookies to bypass AWS IP blocks permanently.")
        if uploaded_cookies:
            with open("cookies.txt", "wb") as f:
                f.write(uploaded_cookies.getbuffer())
            st.success("✅ Server Authorized! Please refresh the page. This box will now disappear for all users.")

youtube_url = st.text_input("Enter YouTube URL", placeholder="https://youtu.be/...")
generate_clicked = st.button("🚀 Generate Content", use_container_width=True, type="primary")

if generate_clicked:
    if not youtube_url:
        st.error("Please enter a URL.")
    elif not os.getenv("GOOGLE_API_KEY"):
        st.error("Please provide a Gemini API Key.")
    else:
        try:
            with st.status("🚀 Initializing AI Engine...", expanded=True) as status:
                status.write("⏳ Extracting audio and summarizing content...")
                article_content = generate_article(youtube_url, model_name=model_name)
            
                status.write("🎨 Designing premium webpage layouts...")
                webpage_response = generate_webpage(article_content, model_name=model_name)
                codes = parse_webpage_output(webpage_response)

                status.update(label="✅ Content Generated Successfully!", state="complete", expanded=False)

            tab1, tab2, tab3, tab4 = st.tabs(["🖥️ Live Preview", "📄 Raw ArticleText", "💻 Code", "📦 Download"])
            with tab1:
                with st.container():
                    # Fuse CSS into HTML <style> for proper component rendering
                    fused_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>{codes.get('css', '')}</style>
                        <script>{codes.get('js', '')}</script>
                    </head>
                    <body>
                        {codes.get('html', '')}
                    </body>
                    </html>
                    """
                    import streamlit.components.v1 as components
                    components.html(fused_html, height=700, scrolling=True)
            with tab2: 
                st.markdown(article_content)
            with tab3:
                st.code(codes.get("html", ""), language="html")
                st.code(codes.get("css", ""), language="css")
            with tab4:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zf:
                    zf.writestr("index.html", codes.get("html", ""))
                    zf.writestr("style.css", codes.get("css", ""))
                st.download_button("📥 Download ZIP", data=zip_buffer.getvalue(), file_name="gemini_web.zip")
        except Exception as e:
            st.error(f"Error: {e}")
