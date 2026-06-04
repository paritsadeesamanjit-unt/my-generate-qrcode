import streamlit as st
import qrcode
import requests
import re
import pandas as pd
import zipfile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ตั้งค่าหน้าตาของโปรแกรม
st.set_page_config(page_title="Universal QR Code Generator", page_icon="⚙️", layout="centered")

# ฟังก์ชันแปลงลิงก์ Google Drive ทั่วไป ให้เป็น Direct Link
def convert_google_drive_link(url):
    if "drive.google.com" in str(url):
        match = re.search(r'/d/([^/]+)', str(url))
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={file_id}"
    return str(url)

# ฟังก์ชันสร้าง QR Code และวาดข้อความลงไปในเนื้อภาพ
def generate_qr_with_text(data, label_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    clean_label = label_text[:25] + "..." if len(label_text) > 28 else label_text
    qr_w, qr_h = qr_img.size
    padding, text_space = 20, 50 
    
    canvas = Image.new("RGB", (qr_w + (padding * 2), qr_h + text_space + padding), "white")
    canvas.paste(qr_img, (padding, padding))
    
    draw = ImageDraw.Draw(canvas)
    font = None
    for f in ["tahoma.ttf", "arial.ttf", "cordia.ttf"]:
        try: font = ImageFont.truetype(f, 18); break
        except: continue
    if font is None:
        try: font = ImageFont.load_default(size=18)
        except: font = ImageFont.load_default()
            
    try: text_w = draw.textlength(clean_label, font=font)
    except: text_w = draw.textsize(clean_label, font=font)[0] if hasattr(draw, 'textsize') else 150
        
    draw.text(((canvas.size[0] - text_w) // 2, qr_h + padding + 10), clean_label, fill="black", font=font)
    buf = BytesIO(); canvas.save(buf, format="PNG")
    return buf.getvalue(), clean_label


# --- 🛠️ ส่วนของเมนูด้านข้าง ---
st.sidebar.title("📋 เมนูใช้งานระบบ")
menu = st.sidebar.radio(
    "เลือกประเภท QR Code ที่ต้องการสร้าง:",
    ["📄 เอกสาร SDS (PDF)", "✍️ ข้อความ & ตัวเลขทั่วไป", "🌐 ลิงก์เว็บ & รูปภาพ", "📶 เชื่อมต่อ Wi-Fi"]
)

# =========================================================================
# MENU 1: เอกสาร SDS (PDF) - เพิ่มระบบ Batch ผ่าน Excel
# =========================================================================
if menu == "📄 เอกสาร SDS (PDF)":
    st.title("📄 ระบบสร้าง QR Code สำหรับเอกสาร SDS")
    
    # เพิ่มแท็บที่ 3 ขึ้นมาเพื่อรองรับงานสเกลใหญ่ครับ
    tab1, tab2, tab3 = st.tabs(["🔗 ใช้ลิงก์ Google Drive (ทีละไฟล์)", "📁 อัปโหลดไฟล์ตรง (ทีละไฟล์)", "📊 สร้างพร้อมกันหลายไฟล์ (Excel)"])
    
    with tab1:
        st.subheader("วิธีที่ 1: วางลิงก์ไฟล์ (ทีละไฟล์)")
        pdf_url = st.text_input("วาง URL ของไฟล์ที่นี่:", placeholder="เช่น https://drive.google.com/file/d/.../view")
        if st.button("สร้าง QR Code จากลิงก์", key="btn_sds_url"):
            if pdf_url:
                with st.spinner("กำลังสร้าง..."):
                    final_link = convert_google_drive_link(pdf_url)
                    extracted_name = pdf_url.split("/")[-1].split("?")[0]
                    filename_clean = extracted_name[:-4] if extracted_name.lower().endswith('.pdf') else "SDS_Document"
                    qr_bytes, name = generate_qr_with_text(final_link, filename_clean)
                    st.success("🎉 สร้างสำเร็จ!")
                    st.image(qr_bytes, width=300)
                    st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name=f"{name}_qr.png", mime="image/png")
            else: st.error("กรุณากรอก URL ก่อนครับ")
            
    with tab2:
        st.subheader("วิธีที่ 2: อัปโหลดไฟล์ตรงจากเครื่อง (ทีละไฟล์)")
        uploaded_file = st.file_uploader("เลือกไฟล์ PDF จากเครื่อง", type=["pdf"])
        if st.button("อัปโหลดและสร้าง QR Code", key="btn_sds_upload"):
            if uploaded_file is not None:
                with st.spinner("กำลังประมวลผลไฟล์..."):
                    try:
                        # ระบบอัปโหลดชั่วคราว (Fallback)
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        response = requests.post("https://file.io/?expires=1d", files=files)
                        if response.status_code == 200 and response.json().get("success"):
                            direct_link = response.json().get("link")
                            filename_clean = uploaded_file.name[:-4] if uploaded_file.name.lower().endswith('.pdf') else uploaded_file.name
                            qr_bytes, name = generate_qr_with_text(direct_link, filename_clean)
                            st.success("🎉 สร้างสำเร็จ!")
                            st.image(qr_bytes, width=300)
                            st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name=f"{name}_qr.png", mime="image/png")
                        else: st.error("เซิร์ฟเวอร์ขัดข้อง กรุณาลองใหม่หรือใช้วิธีที่ 1 ครับ")
                    except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")
            else: st.error("กรุณาเลือกไฟล์ก่อนครับ")

    # ✨ [แท็บใหม่] บรรลุความต้องการสร้างทีละเยอะๆ ด้วย Excel ✨
    with tab3:
        st.subheader("วิธีที่ 3: อัปโหลดไฟล์ Excel เพื่อสร้าง QR Code ทีละหลายไฟล์")
        st.write("📝 **รูปแบบตารางใน Excel ที่คุณต้องเตรียม:**")
        
        # แสดงตัวอย่างตารางให้ผู้ใช้เข้าใจง่าย
        example_df = pd.DataFrame({
            "ชื่อสารเคมี (แสดงใต้ QR)": ["Acetone", "Ethanol_95", "Sulfuric_Acid"],
            "ลิงก์ Google Drive": [
                "https://drive.google.com/file/d/xxxxxx/view",
                "https://drive.google.com/file/d/yyyyyy/view",
                "https://drive.google.com/file/d/zzzzzz/view"
            ]
        })
        st.table(example_df)
        
        uploaded_excel = st.file_uploader("เลือกไฟล์ Excel (.xlsx) หรือ CSV ของคุณ", type=["xlsx", "csv"])
        
        if st.button("🚀 เริ่มสร้าง QR Code ทั้งหมดแบบกลุ่ม", key="btn_batch_excel"):
            if uploaded_excel is not None:
                with st.spinner("🔄 ระบบกำลังอ่านไฟล์ Excel และสลักชื่อลงใน QR Code ทุกตัว..."):
                    try:
                        # 1. อ่านไฟล์ตามประเภท (.xlsx หรือ .csv)
                        if uploaded_excel.name.endswith('.xlsx'):
                            df = pd.read_excel(uploaded_excel)
                        else:
                            df = pd.read_csv(uploaded_excel)
                            
                        # ตรวจสอบว่ามีข้อมูลอย่างน้อย 2 คอลัมน์ไหม
                        if df.shape[1] < 2:
                            st.error("ไฟล์ Excel ต้องมีอย่างน้อย 2 คอลัมน์ (คอลัมน์แรก: ชื่อ, คอลัมน์สอง: ลิงก์)")
                            st.stop()
                            
                        # 2. เตรียมสร้างไฟล์ ZIP ในหน่วยความจำชั่วคราว
                        zip_buffer = BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                            success_count = 0
                            
                            # วิ่งลูปอ่านตารางทีละแถว
                            for index, row in df.iterrows():
                                chem_name = str(row.iloc[0]).strip() # คอลัมน์แรก
                                drive_url = str(row.iloc[1]).strip() # คอลัมน์สอง
                                
                                # ข้ามแถวที่ข้อมูลว่างเปล่า
                                if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]):
                                    continue
                                    
                                # แปลงลิงก์ Google Drive เป็นลิงก์ตรงอัตโนมัติ
                                final_link = convert_google_drive_link(drive_url)
                                
                                # สร้าง QR Code ฝังชื่อสารเคมี
                                qr_bytes, clean_name = generate_qr_with_text(final_link, chem_name)
                                
                                # เขียนไฟล์ภาพเข้าไปในแพ็คเกจ ZIP
                                zip_file.writestr(f"{clean_name}_qr.png", qr_bytes)
                                success_count += 1
                        
                        # 3. เมื่อทำครบทุกตัวแล้ว ให้แสดงปุ่มดาวน์โหลดไฟล์ ZIP
                        if success_count > 0:
                            st.success(f"🎉 ประมวลผลเสร็จสิ้น! สร้าง QR Code สำเร็จทั้งหมด {success_count} รายการ")
                            
                            st.download_button(
                                label="📥 ดาวน์โหลดไฟล์ QR_Codes_All.zip",
                                data=zip_buffer.getvalue(),
                                file_name="QR_Codes_All.zip",
                                mime="application/zip"
                            )
                        else:
                            st.warning("ไม่พบข้อมูลที่สามารถนำมาสร้าง QR Code ได้ในไฟล์ของคุณ")
                            
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ Excel: {e}")
            else:
                st.error("กรุณาอัปโหลดไฟล์ Excel ก่อนกดปุ่มครับ")

# =========================================================================
# ส่วนของเมนูอื่นๆ (✍️ ข้อความ, 🌐 ลิงก์เว็บ, 📶 Wi-Fi) ทำงานได้ตามปกติ...
# =========================================================================
elif menu == "✍️ ข้อความ & ตัวเลขทั่วไป":
    st.title("✍️ ระบบสร้าง QR Code จากข้อความทั่วไป")
    text_input = st.text_area("กรอกข้อความ / ตัวเลข / ประโยค ที่ต้องการ:")
    custom_label = st.text_input("ชื่อป้ายใต้ QR Code (เลือกระบุหรือไม่ระบุก็ได้):")
    if st.button("สร้าง QR Code ข้อความ"):
        if text_input:
            final_label = custom_label if custom_label else text_input
            qr_bytes, name = generate_qr_with_text(text_input, final_label)
            st.success("🎉 สร้างสำเร็จ!")
            st.image(qr_bytes, width=300)
            st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name="text_qr.png", mime="image/png")
        else: st.error("กรุณากรอกข้อความก่อนครับ")

elif menu == "🌐 ลิงก์เว็บ & รูปภาพ":
    st.title("🌐 ระบบสร้าง QR Code สำหรับลิงก์ หรือ รูปภาพ")
    tab_web, tab_img = st.tabs(["🔗 วางลิงก์เว็บไซต์ (URL)", "🖼️ อัปโหลดรูปภาพ (.png, .jpg)"])
    with tab_web:
        web_url = st.text_input("วางลิงก์ URL ที่ต้องการ:")
        url_label = st.text_input("ชื่อป้ายใต้ QR Code ของลิงก์นี้:")
        if st.button("สร้าง QR Code จากลิงก์เว็บ"):
            if web_url:
                final_label = url_label if url_label else "Web Link"
                qr_bytes, name = generate_qr_with_text(web_url, final_label)
                st.success("🎉 สร้างสำเร็จ!")
                st.image(qr_bytes, width=300)
                st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name="link_qr.png", mime="image/png")
            else: st.error("กรุณากรอกลิงก์ก่อนครับ")
    with tab_img:
        uploaded_img = st.file_uploader("เลือกไฟล์รูปภาพของคุณ", type=["png", "jpg", "jpeg"])
        if st.button("อัปโหลดและสร้าง QR Code รูปภาพ"):
            if uploaded_img is not None:
                with st.spinner("กำลังอัปโหลด..."):
                    try:
                        files = {"file": (uploaded_img.name, uploaded_img.getvalue(), uploaded_img.type)}
                        response = requests.post("https://file.io/?expires=1d", files=files)
                        if response.status_code == 200 and response.json().get("success"):
                            direct_img_link = response.json().get("link")
                            img_name_clean = uploaded_img.name.rsplit('.', 1)[0]
                            qr_bytes, name = generate_qr_with_text(direct_img_link, img_name_clean)
                            st.success("📤 อัปโหลดรูปภาพสำเร็จ!")
                            st.image(qr_bytes, width=300)
                            st.download_button("📥 ดาวน์โหลดภาพ QR Code (PNG)", data=qr_bytes, file_name=f"{name}_qr.png", mime="image/png")
                        else: st.error("ระบบฝากรูปขัดข้อง")
                    except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")

elif menu == "📶 เชื่อมต่อ Wi-Fi":
    st.title("📶 ระบบสร้าง QR Code สำหรับเชื่อมต่อ Wi-Fi")
    wifi_ssid = st.text_input("1. ชื่อสัญญาณ Wi-Fi (SSID):")
    wifi_password = st.text_input("2. รหัสผ่าน Wi-Fi (Password):", type="password")
    wifi_security = st.selectbox("3. ประเภทความปลอดภัย (Security Type):", ["WPA/WPA2", "WEP", "ไม่มีรหัสผ่าน (เปิดสาธารณะ)"])
    is_hidden = st.checkbox("เป็นเครือข่ายที่ซ่อนชื่อไว้ (Hidden Network)")
    if st.button("สร้าง QR Code สำหรับ Wi-Fi"):
        if wifi_ssid:
            sec_type = "WPA" if wifi_security == "WPA/WPA2" else ("WEP" if wifi_security == "WEP" else "nopass")
            hidden_status = "true" if is_hidden else "false"
            wifi_data_string = f"WIFI:S:{wifi_ssid};T:{sec_type};P:{wifi_password};H:{hidden_status};;"
            qr_bytes, name = generate_qr_with_text(wifi_data_string, f"Wi-Fi: {wifi_ssid}")
            st.success(f"🎉 สร้างสำเร็จ!")
            st.image(qr_bytes, width=300)
            st.download_button("📥 ดาวน์โหลดภาพ QR Code Wi-Fi (PNG)", data=qr_bytes, file_name=f"wifi_{wifi_ssid}_qr.png", mime="image/png")
        else: st.error("กรุณากรอกชื่อ Wi-Fi ก่อนครับ")