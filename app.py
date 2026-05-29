import streamlit as st
import qrcode
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ตั้งค่าหน้าตาของโปรแกรม
st.set_page_config(page_title="PDF to QR Code Generator", page_icon="📄", layout="centered")

st.title("📄 ระบบสร้าง QR Code ฝังชื่อไฟล์ลงในภาพ")
st.write("เมื่อกดสร้าง รูปภาพ QR Code จะมีชื่อไฟล์ปรากฏอยู่ที่ด้านล่างของภาพทันที สะดวกต่อการนำไปพิมพ์ใช้งาน")

# สร้างตัวเลือกในรูปแบบ Tabs
tab1, tab2 = st.tabs(["🔗 ใช้ลิงก์ PDF", "📁 อัปโหลดไฟล์ PDF โดยตรง"])

# ✨ ฟังก์ชันใหม่: สร้าง QR Code และวาดชื่อไฟล์ลงไปในเนื้อภาพ ✨
def generate_qr_with_text(url, filename):
    # 1. สร้าง QR Code ตามปกติ
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # 2. จัดการตัดนามสกุลไฟล์ออก (เช่น .pdf หรือ .PDF)
    if filename.lower().endswith('.pdf'):
        clean_name = filename[:-4]
    else:
        clean_name = filename
        
    qr_w, qr_h = qr_img.size
    padding = 20
    text_space = 50  # พื้นที่สำหรับเว้นไว้เขียนชื่อไฟล์ด้านล่าง
    
    # 3. สร้างผืนผ้าใบ (Canvas) สีขาวอันใหม่ให้ใหญ่กว่า QR Code เพื่อมีพื้นที่ใส่ตัวอักษร
    canvas_w = qr_w + (padding * 2)
    canvas_h = qr_h + text_space + padding
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    
    # 4. วางภาพ QR Code ลงไปบนผืนผ้าใบใหม่
    canvas.paste(qr_img, (padding, padding))
    
    # 5. เริ่มกระบวนการเขียนข้อความลงบนภาพ
    draw = ImageDraw.Draw(canvas)
    
    # พยายามโหลดฟอนต์ของระบบที่รองรับภาษาไทย (สำหรับ Windows)
    font = None
    system_fonts = ["tahoma.ttf", "arial.ttf", "cordia.ttf"]
    for f in system_fonts:
        try:
            font = ImageFont.truetype(f, 18)
            break
        except:
            continue
            
    # ถ้าดึงฟอนต์ระบบไม่ได้ ให้ใช้ฟอนต์เริ่มต้นของโปรแกรม
    if font is None:
        try:
            font = ImageFont.load_default(size=18)
        except:
            font = ImageFont.load_default()
            
    # 6. คำนวณความกว้างของข้อความ เพื่อจัดให้อยู่ตรงกลางภาพพอดี
    try:
        text_w = draw.textlength(clean_name, font=font)
    except:
        text_w = draw.textsize(clean_name, font=font)[0] if hasattr(draw, 'textsize') else 150
        
    text_x = (canvas_w - text_w) // 2
    text_y = qr_h + padding + 10  # ตำแหน่ง Y อยู่ใต้ QR Code พอดิบพอดี
    
    # 7. เขียนข้อความลงไปในภาพ (ตัวอักษรสีดำ)
    draw.text((text_x, text_y), clean_name, fill="black", font=font)
    
    # 8. แปลงไฟล์ภาพผลลัพธ์เป็น Bytes เพื่อส่งให้ Streamlit แสดงผลและดาวน์โหลด
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue(), clean_name

# ----------------- TAB 1: วางลิงก์ PDF -----------------
with tab1:
    st.subheader("วิธีที่ 1: นำลิงก์ PDF มาสร้าง QR Code")
    pdf_url = st.text_input("วาง URL ของไฟล์ PDF ที่นี่:", placeholder="https://example.com/myfile.pdf")
    
    if st.button("สร้าง QR Code จากลิงก์", key="btn_url"):
        if pdf_url:
            with st.spinner("กำลังสร้าง QR Code..."):
                # แกะชื่อไฟล์สั้นๆ ออกมาจาก URL
                extracted_name = pdf_url.split("/")[-1].split("?")[0]
                if not extracted_name.lower().endswith(".pdf"):
                    extracted_name = "PDF_Link"
                    
                qr_bytes, clean_name = generate_qr_with_text(pdf_url, extracted_name)
                
                st.success("🎉 สร้าง QR Code สำเร็จ!")
                st.image(qr_bytes, caption="ภาพนี้มีชื่อไฟล์ฝังอยู่ด้านล่างแล้ว", width=300)
                
                st.download_button(
                    label="📥 ดาวน์โหลดภาพ QR Code (PNG)",
                    data=qr_bytes,
                    file_name=f"{clean_name}_qr.png",
                    mime="image/png"
                )
        else:
            st.error("กรุณากรอก URL ก่อนกดปุ่มครับ")

# ----------------- TAB 2: อัปโหลดไฟล์ PDF -----------------
with tab2:
    st.subheader("วิธีที่ 2: อัปโหลดไฟล์ PDF จากเครื่อง")
    uploaded_file = st.file_uploader("เลือกไฟล์ PDF ของคุณ", type=["pdf"])
    
    if st.button("อัปโหลดและสร้าง QR Code", key="btn_upload"):
        if uploaded_file is not None:
            with st.spinner("กำลังอัปโหลดและสร้างภาพรวม..."):
                try:
                    # อัปโหลดไฟล์ไปยังเซิร์ฟเวอร์ฝากไฟล์ชั่วคราวเพื่อให้ได้ Direct Link
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post("https://tmpfiles.org/api/v1/upload", files=files)
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get("status") == "success":
                            original_link = res_data.get("data", {}).get("url")
                            direct_link = original_link.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                            
                            # เรียกใช้ฟังก์ชันสร้างภาพฝังชื่อไฟล์
                            qr_bytes, clean_name = generate_qr_with_text(direct_link, uploaded_file.name)
                            
                            st.success("📤 อัปโหลดและสร้างภาพฝังชื่อไฟล์สำเร็จ!")
                            st.image(qr_bytes, caption="ชื่อไฟล์ด้านล่างคือเนื้อเดียวกับรูปภาพแล้ว", width=300)
                            
                            st.download_button(
                                label="📥 ดาวน์โหลดภาพ QR Code (PNG)",
                                data=qr_bytes,
                                file_name=f"{clean_name}_qr.png",
                                mime="image/png"
                            )
                        else:
                            st.error("เซิร์ฟเวอร์ปฏิเสธการอัปโหลดไฟล์")
                    else:
                        st.error(f"ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ (Status: {response.status_code})")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            st.error("กรุณาเลือกไฟล์ PDF ก่อนครับ")