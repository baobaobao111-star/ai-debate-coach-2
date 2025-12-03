import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder # Thư viện ghi âm mới

# --- CẤU HÌNH (Thay Key của bạn vào) ---
API_KEY = st.secrets["GEMINI_API_KEY"] 
MODEL_NAME = "gemini-2.5-flash"

st.set_page_config(page_title="AI Debate Master", page_icon="🎤")
st.title("🎤 AI Debate Master - Đối Thủ Tranh Biện")

# Kết nối Google AI
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"Lỗi cấu hình API: {str(e)}")

# --- BỘ NHỚ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model", 
        "content": "Chào bạn! Tôi đã sẵn sàng. Hãy bấm nút 'Ghi âm' bên dưới để bắt đầu tranh biện!"
    })

# --- THANH CÀI ĐẶT ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    topic = st.text_input("Chủ đề:", value="Nên cấm TikTok")
    side = st.radio("Phe của bạn:", ["Ủng hộ", "Phản đối"])
    if st.button("🔄 Reset Trận đấu"):
        st.session_state.messages = []
        st.rerun()

# --- HIỂN THỊ CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- HÀM XỬ LÝ AI ---
def get_ai_response(user_input, audio_bytes=None):
    system_instruction = f"""
    Bạn là Huấn luyện viên Tranh biện Quốc tế. Chủ đề: {topic}. Bạn phe ĐỐI LẬP.
    
    NHIỆM VỤ ĐẶC BIỆT:
    Nếu có âm thanh, hãy nghe kỹ ngữ điệu (run rẩy hay tự tin, có nói lắp không).
    
    CẤU TRÚC TRẢ LỜI:
    1. 🎙️ NHẬN XÉT GIỌNG NÓI: (Ngắn gọn về độ tự tin/lưu loát)
    2. 🛡️ PHẢN BIỆN LOGIC: (Tấn công luận điểm)
    3. 📊 ĐIỂM SỐ (0-10): Logic, Bằng chứng, Phong thái.
    4. 🎯 CÂU HỎI PHẢN BIỆN LẠI.
    """
    
    chat_session = model.start_chat(history=[])
    try:
        parts = [system_instruction]
        if audio_bytes:
            parts.append({"mime_type": "audio/wav", "data": audio_bytes})
            parts.append("Nghe và phản biện.")
        else:
            parts.append(f"Luận điểm: {user_input}")

        response = chat_session.send_message(parts)
        return response.text
    except Exception as e:
        return f"⚠️ Lỗi: {str(e)}"

# --- KHU VỰC NHẬP LIỆU ---
st.divider()
col1, col2 = st.columns([1, 3])

with col1:
    st.write("🔴 **Bấm để nói:**")
    # Nút ghi âm mới: Bấm Start để nói, Bấm Stop để gửi
    audio_data = mic_recorder(
        start_prompt="Bắt đầu Ghi âm",
        stop_prompt="Dừng & Gửi",
        key='recorder',
        format="wav" # Quan trọng: Gửi định dạng WAV cho Gemini dễ đọc
    )

# Xử lý khi có file ghi âm mới
if audio_data is not None:
    # Lấy dữ liệu bytes
    audio_bytes = audio_data['bytes']
    
    # Kiểm tra để tránh AI trả lời lặp lại
    # Chúng ta dùng ID của file ghi âm làm dấu mốc
    current_audio_id = str(len(audio_bytes)) 
    if st.session_state.get("last_audio_id") != current_audio_id:
        st.session_state.last_audio_id = current_audio_id # Lưu dấu mốc mới
        
        st.chat_message("user").markdown("🎤 [Đã gửi đoạn ghi âm]")
        st.session_state.messages.append({"role": "user", "content": "🎤 [Đã gửi đoạn ghi âm]"})
        
        with st.spinner("Đang nghe và phân tích..."):
            ai_reply = get_ai_response("", audio_bytes=audio_bytes)
            
        st.chat_message("model").markdown(ai_reply)
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        st.rerun() # Làm mới trang để hiện tin nhắn

with col2:
    if prompt := st.chat_input("Hoặc nhập văn bản tại đây..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Đang suy nghĩ..."):
            ai_reply = get_ai_response(prompt)
            
        st.chat_message("model").markdown(ai_reply)
        st.session_state.messages.append({"role": "model", "content": ai_reply})