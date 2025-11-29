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

st.set_page_config(page_title="AI 旅遊菜單翻譯", page_icon="🌴")

st.title("🌴 峇里島/全球 菜單翻譯大師")
st.write("自動偵測幣別 (IDR/USD/JPY)，幫你換算台幣、解釋菜色、計算稅金！")

# 檢查 API Key
if not api_key or "請填入" in api_key:
    st.error("⚠️ 請先在程式碼中填入你的 OpenAI API Key 才能使用喔！")
    st.stop()

client = OpenAI(api_key=api_key)

# 1. 讓使用者輸入禁忌
preferences = st.text_input("🚫 飲食禁忌/過敏 (例如：不吃辣 No Spicy、不吃牛肉 No Beef)", "")

# 2. 上傳圖片
uploaded_files = st.file_uploader("請拍攝/上傳菜單 (支援多張)...", 
                                  type=["jpg", "jpeg", "png"], 
                                  accept_multiple_files=True)

if uploaded_files:
    if st.button('🚀 開始翻譯'):
        
        # 建立進度條
        progress_bar = st.progress(0)
        
        for index, uploaded_file in enumerate(uploaded_files):
            st.divider()
            st.subheader(f"📄 菜單 {index + 1}")
            st.image(uploaded_file, caption='原始菜單', use_container_width=True)

            with st.spinner(f'AI 正在分析幣別與菜色...'):
                try:
                    # 圖片轉碼
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')

                    # ==========================================
                    # 🌟 核心修改：針對峇里島優化的 Prompt
                    # ==========================================
                    prompt_text = f"""
                    你是一個精通全球旅遊的美食嚮導。請分析這張菜單圖片。

                    【使用者禁忌】：{preferences}

                    請先偵測圖片中的 **「貨幣單位」** 與 **「菜色風格」**，並依照以下邏輯處理：

                    1. **【場景判斷 - 關鍵！】**：
                       - 如果幣別是 **IDR (Rp, 印尼盾)** 或數字為 **k 結尾 (如 50k)**：你現在在印尼/峇里島。
                       - 如果幣別是 **USD ($)**：你現在在美國。
                       - 其他：依照當地習慣。

                    2. **【翻譯表格】** (請用 Markdown 表格輸出，包含以下欄位)：
                       - **原文菜名**
                       - **當地名稱** (若是英文菜單但賣當地菜，請還原。例如 Fried Rice -> Nasi Goreng；Duck -> Bebek)
                       - **中文翻譯與口感** (請解釋食材與烹飪方式。例如：Babi Guling 是香料烤乳豬)
                       - **價格** (原幣)
                       - **約略台幣** (若為 IDR，請以 1k ≈ 2.1 TWD 快速換算；若為其他請依現匯率)

                    3. **【峇里島/東南亞特別警示】** (若偵測到是此地區)：
                       - **辣度提醒**：若含 "Sambal", "Pedas" 或紅色標示，請標註 🌶️。
                       - **食材提醒**："Babi" 是豬肉 (峇里島常見)，"Ayam" 是雞肉，"Bebek" 是鴨肉，"Sapi" 是牛肉。
                       - **衛生提醒**：若看起來是路邊攤 (Warung)，提醒注意冰塊與生菜。

                    4. **【價格試算】**：
                       - 如果是印尼盾 (IDR)，請在表格下方列出：「💰 價格可能需加收 10%~21% (Tax & Service)，換算台幣約 NT$ XXX」。
                       - 如果是美金，請列出含稅+小費的預估金額。

                    請直接輸出結果。
                    """

                    # 呼叫 OpenAI
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
                    
                    # 顯示結果
                    result_text = response.choices[0].message.content
                    st.markdown("### 🌴 翻譯與分析結果")
                    st.markdown(result_text)

                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
            
            progress_bar.progress((index + 1) / len(uploaded_files))

        st.success("🎉 分析完成！祝你用餐愉快！")
