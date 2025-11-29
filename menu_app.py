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

st.set_page_config(page_title="AI 多張菜單翻譯神器", page_icon="🍽️")

st.title("🍽️ AI 菜單翻譯器 (批次版)")
st.write("你可以一次上傳好幾張照片，我會一張一張幫你翻譯！")

if not api_key or "請填入" in api_key:
    st.error("⚠️ 請先在程式碼中填入你的 OpenAI API Key 才能使用喔！")
else:
    client = OpenAI(api_key=api_key)

    # 1. 修改點：accept_multiple_files=True (允許選多個檔案)
    uploaded_files = st.file_uploader("請選擇菜單圖片 (按住 Ctrl 可多選)...", 
                                      type=["jpg", "jpeg", "png"], 
                                      accept_multiple_files=True)

    # 確認使用者有上傳檔案
    if uploaded_files:
        st.write(f"你總共上傳了 {len(uploaded_files)} 張菜單。")
        
        if st.button('🚀 開始全部翻譯'):
            
            # 建立進度條
            progress_bar = st.progress(0)
            
            # 2. 修改點：使用 for 迴圈，一張一張處理
            for index, uploaded_file in enumerate(uploaded_files):
                
                # 顯示現在正在處理哪一張
                st.divider() # 分隔線
                st.subheader(f"📄 第 {index + 1} 張菜單：{uploaded_file.name}")
                st.image(uploaded_file, caption=f'原始圖片 - {uploaded_file.name}', use_container_width=True)

                with st.spinner(f'正在翻譯第 {index + 1} 張菜單，請稍候...'):
                    try:
                        # 圖片轉碼
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')

                        # 呼叫 OpenAI
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "你是一個專業的美食翻譯家。請將這張菜單圖片翻譯成繁體中文。請使用Markdown表格格式輸出，包含三欄：【原文菜名】、【中文翻譯】、【價格/備註】。"},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}"
                                            },
                                        },
                                    ],
                                }
                            ],
                            max_tokens=1000
                        )
                        
                        # 顯示結果
                        result_text = response.choices[0].message.content
                        st.markdown("### 🍳 翻譯結果")
                        st.markdown(result_text)

                    except Exception as e:
                        st.error(f"第 {index + 1} 張圖片發生錯誤：{str(e)}")
                
                # 更新進度條
                progress_bar.progress((index + 1) / len(uploaded_files))

            st.success("🎉 全部翻譯完成！")