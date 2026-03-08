import streamlit as st
import asyncio
import pandas as pd
import streamlit.components.v1 as components
from database import init_db, get_all_rules, add_rule, delete_rule
from docx_handler import extract_text
from utils import split_text_smartly, apply_replacement_rules, zip_mp3_files, is_important_sentence
from tts_logic import (
    get_voices_by_region, generate_audio_async, format_rate, format_pitch, 
    get_voice_display_name
)

# 初始化資料庫
init_db()

# --- 最終視覺全統一 CSS ---
st.set_page_config(page_title="專業文字轉語音工具", page_icon="🎙️", layout="centered")

st.markdown("""
    <style>
    /* 1. 寬度限制與置中 */
    .block-container {
        max-width: 720px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    .stApp { background-color: #FFFFFF !important; }
    
    /* 2. 側邊欄設計 */
    [data-testid="stSidebar"] {
        width: 260px !important;
        background-color: #F8F9FA !important;
        border-right: 3px solid #E8E2D6;
    }
    [data-testid="stSidebar"] label {
        color: #000000 !important;
        background-color: #E8E2D6 !important; 
        padding: 4px 10px;
        font-size: 0.9rem !important;
        font-weight: bold;
        display: block;
        border: 1px solid #D1C9B8;
    }
    
    /* 3. 標籤反白：PANTONE 10121 C */
    label, .stSubheader, h3, .stMarkdown h3 {
        background-color: #E8E2D6 !important; 
        color: #000000 !important; 
        padding: 6px 15px !important;
        border-radius: 4px !important;
        display: block !important;
        width: 100% !important;
        font-size: 1rem !important;
        font-weight: 800 !important;
        border: 1px solid #D1C9B8 !important;
        margin-bottom: 5px !important;
    }
    
    /* 4. 核心樣式統一：乾燥玫瑰色 (#B05B77) 
       包含：所有按鈕、下載按鈕、上傳按鈕、成功提示標籤 */
    div.stButton > button:first-child, 
    div.stDownloadButton > button:first-child,
    div[data-testid="stFileUploader"] section button,
    .stAlert {
        background-color: #B05B77 !important;
        color: #FFFFFF !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        box-shadow: 0px 3px 8px rgba(176, 91, 119, 0.2) !important;
        width: 100% !important;
    }
    
    /* 5. 懸停效果統一 */
    div.stButton > button:first-child:hover,
    div.stDownloadButton > button:first-child:hover,
    div[data-testid="stFileUploader"] section button:hover {
        background-color: #8E445D !important;
        transform: scale(1.01) !important;
    }
    
    /* 6. 狀態標籤文字強制白色 */
    .stAlert p, .stAlert span {
        color: #FFFFFF !important;
    }

    /* 文字內容樣式 */
    input, select, textarea, span, p, div[role="listbox"] {
        color: #000000 !important; font-weight: 600 !important; font-size: 0.95rem !important;
    }

    /* 主標題 */
    h1 {
        background-color: #E8E2D6 !important;
        color: #000000 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        border: 2px solid #D1C9B8 !important;
        text-align: center !important;
        font-size: 1.8rem !important;
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 主標題 ---
st.title("專業文字轉語音工具")
st.markdown("<h5 style='text-align: center; color: #3E2723; font-weight: 800;'>DOCX 轉存 自然語言MP3。</h5>", unsafe_allow_html=True)
st.markdown("---")

# 側邊欄
st.sidebar.header("⚙️ 系統設定")
region = st.sidebar.selectbox("服務區域", ["TW", "CN"])

async def fetch_voices(r): return await get_voices_by_region(r)
voices_list = asyncio.run(fetch_voices(region))
voice_options = {get_voice_display_name(v): v['ShortName'] for v in voices_list}

selected_voice_label = st.sidebar.selectbox("語音夥伴", list(voice_options.keys()))
selected_voice_id = voice_options[selected_voice_label]
speed = st.sidebar.slider("說話語速", 0.5, 2.0, 1.0, 0.1)
pitch_val = st.sidebar.slider("音調微調", -50, 50, 0, 1)

st.sidebar.markdown("---")
buddhist_mode = st.sidebar.checkbox("🤖 AI 智慧語氣優化", value=True)
st.sidebar.caption("< 附加 AI 自動調整語氣功能 >")
enable_notify = st.sidebar.checkbox("🔔 完成後桌面提醒", value=True)

if enable_notify:
    components.html("""<script>if(Notification.permission!=="granted")Notification.requestPermission();</script>""", height=0)

# --- 並行轉換邏輯 ---
async def process_conversion_parallel(text_parts, voice_id, speed, pitch_val, buddhist_mode, status_placeholder):
    sem = asyncio.Semaphore(3)
    mp3_results = [None] * len(text_parts)
    progress_bar = st.progress(0)
    completed_count = 0
    async def single_task(i, part):
        nonlocal completed_count
        async with sem:
            rate_str, pitch_str = format_rate(speed), format_pitch(pitch_val)
            if buddhist_mode and is_important_sentence(part):
                rate_str, pitch_str = "-10%", "+12Hz"
            try:
                audio = await generate_audio_async(part, voice_id, rate_str, pitch_str)
                mp3_results[i] = audio
                completed_count += 1
                progress_bar.progress(completed_count / len(text_parts))
                status_placeholder.write(f"🏃 正在處理：{completed_count}/{len(text_parts)} 段")
            except Exception as e: st.error(f"❌ 錯誤：{e}")
    tasks = [single_task(i, part) for i, part in enumerate(text_parts)]
    await asyncio.gather(*tasks)
    return mp3_results

# --- 主介面佈局 ---
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("📁 1. 上傳轉檔任務")
    up_file = st.file_uploader("請上傳 .docx 檔案", type=["docx"])
    
    if up_file:
        raw_text = extract_text(up_file)
        processed_text = apply_replacement_rules(raw_text, get_all_rules())
        text_parts = split_text_smartly(processed_text, max_chars=3000)
        st.info(f"📊 {len(raw_text)} 字 / {len(text_parts)} 段")
        
        if st.button("🚀 開始極速轉換"):
            with st.status("轉換中，請稍等，完成後會通知您...", expanded=True) as status:
                results = asyncio.run(process_conversion_parallel(
                    text_parts, selected_voice_id, speed, pitch_val, buddhist_mode, st
                ))
                final_mp3s = []
                for idx, data in enumerate(results):
                    if data: final_mp3s.append((f"{up_file.name.rsplit('.', 1)[0]}_{idx+1:02d}.mp3", data))
                
                if len(final_mp3s) == len(text_parts):
                    status.update(label="🏆 轉換成功，請點擊下載！", state="complete", expanded=False)
                    if enable_notify:
                        components.html("""<script>
                            if(Notification.permission==="granted") new Notification("✅ 轉檔完成！");
                            alert("🏆 轉換成功，請點擊下載！");
                        </script>""", height=0)
                    st.balloons()
                    
                    # --- 完成後通知區 (格式統一) ---
                    st.success("🏆 轉換成功，請點擊下載！")
                    zip_data = zip_mp3_files(final_mp3s)
                    st.download_button("📥 點此下載所有音檔 (ZIP)", zip_data, f"{up_file.name.rsplit('.', 1)[0]}.zip", "application/zip", use_container_width=True)
                    st.audio(final_mp3s[0][1], format="audio/mp3")

with col2:
    st.subheader("📋 2. 手動校正發音")
    with st.expander("📝 新增校正規則", expanded=True):
        orig_i = st.text_input("原本文字")
        targ_i = st.text_input("取代唸法")
        if st.button("確認儲存規則"):
            if orig_i: add_rule(orig_i, targ_i); st.rerun()
    rules = get_all_rules()
    if rules:
        df = pd.DataFrame([{"ID": r.id, "字": r.original_text, "唸": r.replace_with} for r in rules])
        st.dataframe(df, use_container_width=True, height=300)
        rid = st.number_input("移除 ID", min_value=1, step=1)
        if st.button("🗑️ 移除此規則"): 
            if delete_rule(rid): st.rerun()
