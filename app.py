import streamlit as st
import qrcode
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ตั้งค่าหน้าตาของโปรแกรม
st.set_page_config(page_title="Universal QR Code Generator", page_icon="⚙️", layout="centered")

# --- ฟังก์ชันหลัก: สร้าง QR Code และวาดข้อความลงไปในเนื้อภาพ ---
def generate_qr_with_text(data, label_text):
    # 1. สร้าง QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # จำกัดความยาวข้อความใต้ภาพไม่ให้ยาวเกินไปจนหลุดกรอบ (ถ้าเกินให้ตัดคำแล้วเติม ...)
    if len(label_text) > 28:
        clean_label = label_text[:25] + "..."
    else:
        clean_label = label_text

    qr_w, qr_h = qr_img.size
    padding = 20
    text_space = 50 
    
    # 2. สร้างผืนผ้าใบสีขาว
    canvas_w = qr_w + (padding * 2)
    canvas_h = qr_h + text_space + padding
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    canvas.paste(qr_img, (padding, padding))
    
    # 3. เขียนข้อความลงบนภาพ
    draw = ImageDraw.Draw(canvas)
    font = None
    system_fonts = ["tahoma.ttf", "arial.ttf", "cordia.ttf"]
    for f in system_fonts:
        try:
            font = ImageFont.truetype(f, 18)
            break
        except:
            continue
    if font is None:
        try: font = ImageFont.load_default(size=18)
        except: font = ImageFont.load_default()
            
    try: text_w = draw.textlength(clean_label, font=font)
    except: text_w = draw.textsize(clean_label, font=font)[0] if hasattr(draw, 'textsize') else 150
        
    text_x = (canvas_w - text_w) // 2
    text_y = qr_h + padding + 10
    
    draw.text((text_x, text_y), clean_label, fill="black", font=font)
    
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue(), clean_label


# --- 🛠️ ส่วนของเมนูด้านข้าง (Sidebar Navigation) ---
st.sidebar.title("📋 เมนูใช้งานระบบ")
menu = st.sidebar.radio(
    "เลือกประเภท QR Code ที่ต้องการสร้าง:",
    ["📄 เอกสาร SDS (PDF)", "✍️ ข้อความ & ตัวเลขทั่วไป", "🌐 ลิงก์เว็บ & รูปภาพ"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 เมื่อแก้ไขโค้ดและ Push ขึ้น GitHub ระบบบนหน้าเว็บจะอัปเดตอัตโนมัติ")


# =========================================================================
# MENU 1: เอกสาร SDS (PDF)
# =========================================================================
if menu == "📄 เอกสาร SDS (PDF)":
    st.title("📄 ระบบสร้าง QR Code สำหรับเอกสาร SDS")
    st.write("สร้าง QR Code สำหรับสแกนเปิดไฟล์ PDF ทันที (พร้อมฝังชื่อไฟล์ใต้ภาพ)")
    
    tab1, tab2 = st.tabs(["📁 อัปโหลดไฟล์ PDF จากเครื่อง", "🔗 ใช้ลิงก์ PDF ที่มีอยู่แล้ว"])
    
    with tab1:
        uploaded_file = st.file_uploader("เลือกไฟล์ PDF ของคุณ", type=["pdf"], key="sds_upload")
        if st.button("สร้าง QR Code (จากไฟล์อัปโหลด)", key="btn_sds_upload"):
            if uploaded_file is not None:
                with st.spinner("กำลังประมวลผลไฟล์..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        response = requests.post("https://tmpfiles.org/api/v1/upload", files=files)
                        if response.status_code == 200:
                            original_link = response.json().get("data", {}).get("url")
                            direct_link = original_link.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                            
                            # ตัดนามสกุลไฟล์ออก
                            filename_clean = uploaded_file.name[:-4] if uploaded_file.name.lower().endswith('.pdf') else uploaded_file.name
                            
                            qr_bytes, name = generate_qr_with_text(direct_link, filename_clean)
                            st.success("🎉 สร้างสำเร็จ!")
                            st.image(qr_bytes, width=300)
                            st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name=f"{name}_qr.png", mime="image/png")
                        else:
                            st.error("เซิร์ฟเวอร์ปลายทางขัดข้อง กรุณาลองใหม่")
                    except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")
            else: st.error("กรุณาเลือกไฟล์ก่อนครับ")
            
    with tab2:
        pdf_url = st.text_input("วาง URL ของไฟล์ PDF ที่นี่:", placeholder="https://example.com/sds-file.pdf", key="sds_url_input")
        if st.button("สร้าง QR Code (จากลิงก์)", key="btn_sds_url"):
            if pdf_url:
                with St.spinner("กำลังสร้าง..."):
                    extracted_name = pdf_url.split("/")[-1].split("?")[0]
                    filename_clean = extracted_name[:-4] if extracted_name.lower().endswith('.pdf') else "SDS_Document"
                    
                    qr_bytes, name = generate_qr_with_text(pdf_url, filename_clean)
                    st.success("🎉 สร้างสำเร็จ!")
                    st.image(qr_bytes, width=300)
                    st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name=f"{name}_qr.png", mime="image/png")
            else: st.error("กรุณากรอก URL ก่อนครับ")


# =========================================================================
# MENU 2: ข้อความ & ตัวเลขทั่วไป
# =========================================================================
elif menu == "✍️ ข้อความ & ตัวเลขทั่วไป":
    st.title("✍️ ระบบสร้าง QR Code จากข้อความทั่วไป")
    st.write("พิมพ์ข้อความ ตัวเลข รหัสสินค้า หรือประโยค เพื่อแปลงเป็น QR Code ได้ทันที")
    
    text_input = st.text_area("กรอกข้อความ / ตัวเลข / ประโยค ที่ต้องการ:", placeholder="เช่น รหัสสินค้า A-101, ข้อความบันทึก หรือหมายเลขโทรศัพท์")
    
    # ให้ผู้ใช้เลือกตั้งชื่อป้ายใต้ QR Code ได้ (ถ้าไม่กรอกจะใช้ข้อความที่พิมพ์ด้านบน)
    custom_label = st.text_input("ชื่อป้ายใต้ QR Code (เลือกระบุหรือไม่ระบุก็ได้):", placeholder="หากเว้นว่างไว้ ระบบจะดึงข้อความด้านบนมาแสดง")
    
    if st.button("สร้าง QR Code ข้อความ", key="btn_general_text"):
        if text_input:
            with st.spinner("กำลังสร้าง QR Code..."):
                # กำหนดข้อความที่จะแสดงใต้กรอบรูป
                final_label = custom_label if custom_label else text_input
                
                qr_bytes, name = generate_qr_with_text(text_input, final_label)
                
                st.success("🎉 สร้าง QR Code ข้อความสำเร็จ!")
                st.image(qr_bytes, width=300)
                st.download_button(
                    label="📥 ดาวน์โหลดภาพ QR Code (PNG)",
                    data=qr_bytes,
                    file_name="text_qr.png",
                    mime="image/png"
                )
        else:
            st.error("กรุณากรอกข้อความก่อนกดปุ่มครับ")


# =========================================================================
# MENU 3: ลิงก์เว็บ & รูปภาพ
# =========================================================================
elif menu == "🌐 ลิงก์เว็บ & รูปภาพ":
    st.title("🌐 ระบบสร้าง QR Code สำหรับลิงก์ หรือ รูปภาพ")
    st.write("สแกนแล้วเด้งไปที่หน้าเว็บไซต์ หรือเปิดรูปภาพเต็มจอทันที")
    
    tab_web, tab_img = st.tabs(["🔗 วางลิงก์เว็บไซต์ (URL)", "🖼️ อัปโหลดรูปภาพ (.png, .jpg)"])
    
    with tab_web:
        web_url = st.text_input("วางลิงก์ URL ที่ต้องการ (เช่น ลิงก์เว็บบริษัท, ลิงก์ฟอร์ม):", placeholder="https://www.google.com")
        url_label = st.text_input("ชื่อป้ายใต้ QR Code ของลิงก์นี้:", placeholder="เช่น Website Company")
        
        if st.button("สร้าง QR Code จากลิงก์เว็บ", key="btn_web_url"):
            if web_url:
                with st.spinner("กำลังสร้าง..."):
                    final_label = url_label if url_label else "Web Link"
                    qr_bytes, name = generate_qr_with_text(web_url, final_label)
                    st.success("🎉 สร้างสำเร็จ!")
                    st.image(qr_bytes, width=300)
                    st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name="link_qr.png", mime="image/png")
            else: st.error("กรุณากรอกลิงก์ URL ก่อนครับ")
            
    with tab_img:
        uploaded_img = st.file_uploader("เลือกไฟล์รูปภาพของคุณ", type=["png", "jpg", "jpeg"])
        if st.button("อัปโหลดและสร้าง QR Code รูปภาพ", key="btn_img_upload"):
            if uploaded_img is not None:
                with st.spinner("กำลังอัปโหลดรูปภาพไปยังเซิร์ฟเวอร์..."):
                    try:
                        # อัปโหลดรูปภาพไปที่ฝากไฟล์ชั่วคราว
                        files = {"file": (uploaded_img.name, uploaded_img.getvalue(), uploaded_img.type)}
                        response = requests.post("https://tmpfiles.org/api/v1/upload", files=files)
                        
                        if response.status_code == 200:
                            original_link = response.json().get("data", {}).get("url")
                            # เปลี่ยนเป็นดึงรูปตรงดิ่ง (/dl/) เพื่อเวลาสแกนจะกางรูปเต็มจอทันที
                            direct_img_link = original_link.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                            
                            # ตัดนามสกุลรูปภาพออกสำหรับทำป้ายใต้ QR Code
                            img_name_clean = uploaded_img.name.rsplit('.', 1)[0]
                            
                            qr_bytes, name = generate_qr_with_text(direct_img_link, img_name_clean)
                            st.success("📤 อัปโหลดรูปภาพและสร้าง QR Code สำเร็จ!")
                            st.image(qr_bytes, width=300)
                            st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name=f"{name}_qr.png", mime="image/png")
                        else:
                            st.error("เกิดข้อผิดพลาดจากเซิร์ฟเวอร์ฝากรูป")
                    except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")
            else: st.error("กรุณาเลือกไฟล์รูปภาพก่อนครับ")