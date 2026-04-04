import re
from typing import Optional

# Dictionary mapping identifying keys to scripted markdown responses and CTAs
SCRIPTED_ANSWERS = {
    "danh_sach_truong": {
        "text": """🏫 *Danh sách các trường đại học liên kết tiêu biểu với SIGE (Kỳ 3/2026):*

Viện SIGE hiện liên kết chiến lược với nhiều ngôi trường đại học cao cấp tại Đài Loan, tiêu biểu gồm:

1. *Đại học Minh Truyền (MCU):* Đạt chuẩn MSCHE (Hoa Kỳ). Hệ 1+4 kỳ 3/2026 chỉ còn ~50 suất ưu tiên. 
2. *Đại học Lĩnh Đông (LTU):* Top 100 Thiết kế. Đặc biệt: Hệ VHVL Chăm sóc sắc đẹp (20 suất) tặng học bổng 100% học phí kỳ 1 (nếu có TOCFL A2) hoặc 50% (nếu có A1).
3. *Đại học Đài Cương (TSU):* Bán dẫn & Kỹ thuật. Miễn 100% học phí & KTX toàn khóa + trợ cấp ~8M/tháng.
4. *Đại học Trung Tín (CTBC):* Trực thuộc ngân hàng lớn nhất ĐL. Miễn 100% học phí & KTX kỳ đầu.
5. *Đại học John (St. John's):* Tại Đài Bắc. Miễn 100% học phí & KTX kỳ đầu cho hệ tự túc.
6. *Đại học Quốc lập Ky Nam (NCNU):* Trường công lập xanh nhất thế giới. Miễn học phí 2 năm đầu (Hệ tự túc) hoặc 1 năm đầu (Thạc sĩ).

👉 Bạn muốn nhận thông tin chi tiết về yêu cầu đầu vào của trường nào?""",
        "buttons": [
            {"text": "📞 Kiểm tra GPA nhận Học bổng", "callback": "start_lead_form"},
            {"text": "📂 Xem hồ sơ cần chuẩn bị", "callback": "ask_hoso"}
        ]
    },

    "hoc_bong_14": {
        "text": """🎯 *Chương trình Hệ chuyên ban Quốc tế 1+4 (Dự bị Đại học):*

Đây là lộ trình du học ưu tiên của SIGE dành cho kỳ tuyển sinh tháng 3/2026.
*Điều kiện & Quy định (Kỳ 3/2026):*
- *Học thuật:* Tốt nghiệp THPT, GPA mỗi học kỳ từ *6.0 trở lên*. 
- *Chỉ tiêu:* Riêng trường Minh Truyền (MCU) dự kiến chỉ có 50-60 suất (ưu tiên đối tác chiến lược).
- *Ngoại ngữ:* Không cần bằng lúc nộp hồ sơ, đạt *TOCFL A2* sau 1 năm.
- *Học bổng:* Miễn 100% học phí năm đầu (Bộ Giáo dục hỗ trợ). Các năm sau dựa trên GPA > 80.

👉 Nên nộp hồ sơ sớm vì hệ này chốt chỉ tiêu rất nhanh!""",
        "buttons": [
            {"text": "📥 Nhận danh sách 50 suất ưu tiên", "callback": "start_lead_form"},
            {"text": "🏫 Xem danh sách trường", "callback": "ask_truong"}
        ]
    },

    "dieu_kien_tuyen_sinh": {
        "text": """📝 *Yêu cầu & Điều kiện tuyển sinh chi tiết (Cập nhật 2026):*

Viện SIGE áp dụng các tiêu chuẩn mới cho kỳ tuyển sinh 3/2026:

1. *Hệ 1+4 & VHVL:* 
   - GPA từng kỳ cấp 3 tối thiểu *6.0*. 
   - Độ tuổi: 18 - 22 (Đẹp nhất là 18-20 cho hệ 1+4).
   - Ngoại ngữ: Ưu tiên TOCFL A1/A2 để tăng tỷ lệ Visa thẳng.

2. *Hệ Thạc sĩ:*
   - Tốt nghiệp ĐH/CĐ. TOCFL A2 (Bản giấy). Tuổi < 40.
   - Học bổng: Lĩnh Đông (100% chuyên ngành QTDN/MBA/Du lịch), Ky Nam (Miễn học phí năm 1).

3. *Hệ Tự túc:*
   - GPA từ 6.0. TOCFL A2 (hoặc IELTS 5.0+). 

*Điều kiện chung:*
- *Tài chính:* Sổ tiết kiệm từ 150 - 180 triệu VNĐ.
- *Sức khỏe:* Khám theo mẫu Đài Loan.
- *Pháp lý:* Lý lịch tư pháp số 2 sạch.""",
        "buttons": [
            {"text": "✅ Kiểm tra điều kiện ngay", "callback": "start_lead_form"}
        ]
    },

    "ho_so_chuan_bi": {
        "text": """📂 *Danh mục hồ sơ cần chuẩn bị (7 Bước):*

1. *Học tập:* Bằng tốt nghiệp & Học bạ gốc.
2. *Nhân thân:* Hộ chiếu (gốc), CCCD, Giấy khai sinh mẫu mới.
3. *Pháp lý:* Lý lịch tư pháp số 2.
4. *Sức khỏe:* Khám theo thông báo của Viện.
5. *Tài chính:* Sổ tiết kiệm 150 - 180 triệu VNĐ.
6. *Ảnh:* 05 ảnh thẻ 4x6 chuẩn VP Đài Bắc.

Viện SIGE sẽ hỗ trợ trọn gói từ khâu dịch thuật đến nộp Visa!""",
        "buttons": [
            {"text": "🚀 Bắt đầu quy trình làm hồ sơ", "callback": "ask_quytrinh"}
        ]
    },

    "quy_trinh_dang_ky": {
        "text": """🚀 *Quy trình hồ sơ tại SIGE (7 Bước):*

1. *Ký Hợp đồng:* Đặt cọc 10-20M VNĐ.
2. *Nộp hồ sơ:* Chuẩn bị 5 mục giấy tờ cơ bản.
3. *Phỏng vấn trường:* Viết tự truyện, kế hoạch học tập.
4. *Chuẩn bị Visa:* Khám sức khỏe, chứng chỉ tiếng, Sổ tiết kiệm.
5. *Nộp Visa:* SIGE nộp hoặc hỗ trợ nộp.
6. *Đặt vé & Bay:* Xuất vé máy bay, tập trung tại sân bay. 
7. *Hạ cánh:* Trường đón về KTX tại Đài Loan.

👉 Toàn bộ lộ trình được SIGE đồng hành sát sao!""",
        "buttons": [
            {"text": "✍️ Đăng ký tư vấn lộ trình", "callback": "start_lead_form"}
        ]
    },

    "hoc_bong_chung": {
        "text": """💰 *Chính sách Học bổng & Các gói Dịch vụ tại SIGE:*

Viện SIGE cung cấp các gói dịch vụ minh bạch cho mọi đối tượng:
- *Gói Cơ bản (36M):* Hồ sơ, dịch thuật, luyện phỏng vấn, Visa lần 1.
- *Gói VIP (55M):* Gồm Gói Cơ bản + Học tiếng, Vé máy bay, Thẻ lưu trú, Bảo hiểm, Tư trang.
- *Gói IELTS (70M):* Cam kết đầu ra IELTS 5.0 và trọn bộ dịch vụ VIP.

⚠️ *Lưu ý:* Tổng chi phí có thể được *giảm trừ cực sâu* dựa trên quỹ Học bổng Doanh nghiệp mà bạn săn được (lên tới 100% học phí). 

Để biết mức phí chính xác sau khi đã áp dụng học bổng cá nhân của bạn, hãy nhấn nút bên dưới! 👇""",
        "buttons": [
            {"text": "💰 Tính phí cá nhân (Sau giảm trừ)", "callback": "start_lead_form"},
            {"text": "📞 Gặp tư vấn viên ngay", "callback": "show_contact"}
        ]
    },

    "co_hoi_viec_lam": {
        "text": """💼 *Thực tập & Việc làm (Chính sách 2026):*

SIGE cam kết lộ trình thực nghiệp an toàn:
- *Hệ VHVL:* Thực tập theo chỉ định của trường. Lương ~28.590 TWD/tháng.
- *Hệ Tự túc:* Sau 6 tháng học tiếng được làm 20h/tuần.
- *Cam kết đầu ra:* Lương kĩ sư chính thức từ 31.150 TWD/tháng trở lên.
- *Hỗ trợ định cư:* Chuyển đổi Visa Kỹ sư sau tốt nghiệp.""",
        "buttons": [
            {"text": "💼 Tìm việc làm lương cao", "callback": "start_lead_form"}
        ]
    },

    "du_hoc_dai_loan": {
        "text": """🇹🇼 *Tại sao chọn Hệ sinh thái SIGE (Kỳ 3/2026)?*

Viện Khoa học Giáo dục Toàn Cầu hỗ trợ SV tiếp cận các chương trình độc quyền:
- *Joint Degree 3+1:* Lấy song bằng Anh/Úc & Đài Loan.
- *Chương trình 2+2+3 (Mỹ):* Đã hết chỉ tiêu kỳ 3/2026. Vui lòng liên hệ để đặt chỗ kỳ 9/2026.
- *Hệ sinh thái VIP:* Bảo trợ trọn gói từ lúc bay đến khi ổn định tại KTX.

✨ *Vibe từ Viện trưởng:*
> *"Với mạng lưới 20 năm tâm huyết tại Đài Loan của tôi, SIGE không chỉ đưa bạn đi học, mà là đưa bạn vào một hệ sinh thái bảo trợ trọn đời."* 
— *ThS. Nguyễn Thị Điệp* (Viện trưởng SIGE)

📞 Hotline: *0938491111*""",
        "buttons": [
            {"text": "🚀 Đăng Ký Tư Vấn VIP 1-1", "url": "https://zalo.me/0938491111"}
        ]
    }
}

# Mapping of common phrase patterns to keys
QUERY_MAPPING = {
    r"danh sách (các )?trường": "danh_sach_truong",
    r"trường nào": "danh_sach_truong",
    r"(hệ )?1\+4": "hoc_bong_14",
    r"chuyên ban quốc tế": "hoc_bong_14",
    r"điều kiện (tuyển sinh|du học)": "dieu_kien_tuyen_sinh",
    r"yêu cầu (đầu vào|tuyển sinh)": "dieu_kien_tuyen_sinh",
    r"hồ sơ (cần )?chuẩn bị": "ho_so_chuan_bi",
    r"cần chuẩn bị gì": "ho_so_chuan_bi",
    r"quy trình (đăng ký|làm hồ sơ)": "quy_trinh_dang_ky",
    r"các bước đăng ký": "quy_trinh_dang_ky",
    r"học bổng": "hoc_bong_chung",
    r"miễn học phí": "hoc_bong_chung",
    r"việc làm|tốt nghiệp xong làm gì": "co_hoi_viec_lam",
    r"thực tập có lương": "co_hoi_viec_lam",
    r"du học đài loan": "du_hoc_dai_loan",
    r"chương trình du học": "du_hoc_dai_loan",
    r"chi phí|giá|bao nhiêu tiền|gói dịch vụ": "hoc_bong_chung"
}

def get_scripted_response(query: str) -> Optional[dict]:
    """
    Checks if the user query matches any scripted response keywords.
    Returns the dictionary (text + buttons) if found, otherwise None.
    """
    query_clean = query.lower().strip()
    
    # 1. Exact match check (for button-passed text)
    if query_clean in SCRIPTED_ANSWERS:
        return SCRIPTED_ANSWERS[query_clean]
        
    # 2. Pattern match check (for user typed text)
    for pattern, key in QUERY_MAPPING.items():
        if re.search(pattern, query_clean):
            return SCRIPTED_ANSWERS[key]
            
    return None
