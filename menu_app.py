import streamlit as st
import base64
from openai import OpenAI

# ================= 設定區 =================
# 請在這裡填入你的 OpenAI API Key (以 sk- 開頭)
# 從雲端設定讀取密碼，而不是直接寫在這裡
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    # 為了方便你在本機測試，這裡可以保留讓使用者手動輸入的防呆機制，或者直接報錯
    st.error("找不到 API Key，請設定 Secrets")
    st.stop()
# =========================================

st.set_page_config(page_title="AI 菜單翻譯+發音", page_icon="🥘")

st.title("🥘 菜單翻譯 & 點餐語音助理")
st.write("拍菜單 -> 翻譯 -> 幫你唸出來！")

# 檢查 API Key
if not api_key or "請填入" in api_key:
    st.error("⚠️ 請先在程式碼中填入你的 OpenAI API Key 才能使用喔！")
    st.stop()

client = OpenAI(api_key=api_key)

# 1. 使用者禁忌
preferences = st.text_input("🚫 飲食禁忌 (例如：不吃辣、不吃牛)", "")

# 2. 上傳圖片
uploaded_files = st.file_uploader("請拍攝/上傳菜單...", 
                                  type=["jpg", "jpeg", "png"], 
                                  accept_multiple_files=True)

# 存放翻譯結果，讓發音功能可以參考
if "last_translation" not in st.session_state:
    st.session_state.last_translation = ""

if uploaded_files:
    if st.button('🚀 開始翻譯'):
        progress_bar = st.progress(0)
        
        for index, uploaded_file in enumerate(uploaded_files):
            st.divider()
            st.subheader(f"📄 菜單 {index + 1}")
            st.image(uploaded_file, caption='原始菜單', use_container_width=True)

            with st.spinner(f'AI 正在分析並翻譯...'):
                try:
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')

                    prompt_text = f"""
                    你是一個精通全球美食的導遊。請分析這張菜單。
                    使用者禁忌：{preferences}

                    請偵測幣別與菜色風格：
                    - 若是 IDR/Rp：這裡是印尼/峇里島。
                    - 若是 USD：這裡是美國。

                    請用 Markdown 表格輸出：
                    1. **原文菜名**
                    2. **當地名稱** (若原文是英文但賣當地菜，請還原。如 Fried Rice -> Nasi Goreng)
                    3. **中文翻譯與口感介紹**
                    4. **價格**
                    5. **約略台幣**

                    若為峇里島，請提醒辣度(Sambal)與肉類(Babi/Bebek)。
                    若為IDR，請提示價格可能需加收 Tax & Service。
                    """

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                        max_tokens=1500
                    )
                    
                    result_text = response.choices[0].message.content
                    st.session_state.last_translation = result_text # 存起來
                    st.markdown("### 📋 翻譯結果")
                    st.markdown(result_text)

                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
            
            progress_bar.progress((index + 1) / len(uploaded_files))
        st.success("翻譯完成！往下捲動可以使用「語音幫手」喔！👇")

# ==========================================
# 🗣️ 新增功能：點餐語音幫手 (TTS)
# ==========================================
st.divider()
st.header("🗣️ 點餐語音幫手")
st.info("想點哪道菜？把上面的「原文」或「當地名稱」複製貼在下面，我唸給店員聽！")

# 讓使用者輸入想聽的字
text_to_speak = st.text_input("貼上你想唸的菜名 (例如: Nasi Goreng)", "")

# 選擇語音風格
voice_option = st.selectbox("選擇語音風格", ["alloy (中性)", "echo (沈穩)", "fable (活潑)", "onyx (低沈)", "nova (溫柔)", "shimmer (清晰)"], index=4)
selected_voice = voice_option.split(" ")[0]

if st.button("🔊 播放發音"):
    if text_to_speak:
        with st.spinner("正在生成語音..."):
            try:
                # 呼叫 OpenAI TTS API
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=selected_voice,
                    input=text_to_speak
                )
                
                # 直接播放
                st.audio(response.content, format="audio/mp3")
                st.success(f"正在播放：{text_to_speak}")
                
            except Exception as e:
                st.error(f"語音生成失敗：{str(e)}")
    else:
        st.warning("請先輸入或是貼上文字喔！")

# 懶人按鈕區
st.write("或者直接點選常用句：")
col1, col2 = st.columns(2)
with col1:
    if st.button("🇮🇩 印尼文：我不吃辣"):
        res = client.audio.speech.create(model="tts-1", voice=selected_voice, input="Saya tidak makan pedas.")
        st.audio(res.content)
with col2:
    if st.button("🇮🇩 印尼文：請給我這個"):
        res = client.audio.speech.create(model="tts-1", voice=selected_voice, input="Saya mau pesan ini.")
        st.audio(res.content)
