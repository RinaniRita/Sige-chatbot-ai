import re
from typing import Optional

# Dictionary mapping identifying keys to scripted markdown responses
SCRIPTED_ANSWERS = {
    "danh_sach_truong": """🏫 **Danh sách các trường đại học liên kết tiêu biểu với SIGE (Kỳ 3/2026):**

Viện SIGE hiện liên kết chiến lược với nhiều ngôi trường đại học cao cấp tại Đài Loan, tiêu biểu gồm:

1. **Đại học Quốc tế Minh Truyền (MCU):** Đạt chuẩn MSCHE (Hoa Kỳ). Mạnh về Truyền thông, QTKD, CNTT.
2. **Đại học KHKT Lĩnh Đông (LTU):** Top 100 thế giới về Thiết kế. Có hệ VHVL Chăm sóc sắc đẹp cực "hot".
3. **Đại học Đài Cương (TSU):** Chuyên về Bán dẫn & Kỹ thuật. Có học bổng miễn 100% học phí & KTX + trợ cấp ~8M/tháng.
4. **Đại học Trung Tín (CTBC):** Trực thuộc ngân hàng lớn nhất Đài Loan. Mạnh về AI và Bán dẫn.
5. **Đại học John (St. John's):** Tại Đài Bắc, miễn 100% học phí & KTX kỳ đầu cho hệ tự túc.
6. **Đại học Quốc lập Ky Nam (NCNU):** Trường công lập xanh nhất thế giới, thế mạnh về Du lịch & CNTT.

👉 Bạn có muốn tìm hiểu kỹ hơn về lộ trình tuyển sinh của trường nào không?""",

    "hoc_bong_14": """🎯 **Chương trình Hệ chuyên ban Quốc tế 1+4 (Dự bị Đại học):**

Đây là lộ trình du học ưu tiên của SIGE dành cho kỳ tuyển sinh tháng 3/2026.
**Điều kiện & Quy định (Kỳ 3/2026):**
- **Học thuật:** Tốt nghiệp THPT, GPA mỗi học kỳ từ **6.0 trở lên**. 
- **Chỉ tiêu:** Riêng trường Minh Truyền (MCU) dự kiến chỉ có 50-60 suất (ưu tiên đối tác chiến lược).
- **Ngoại ngữ:** Không cần bằng lúc nộp hồ sơ, nhưng phải đạt **TOCFL A2** sau 1 năm học tiếng tại Đài Loan.
- **Học bổng:** Miễn 100% học phí năm đầu (Bộ Giáo dục hỗ trợ). Các năm sau dựa trên GPA > 80.

👉 Nên nộp hồ sơ sớm vì hệ này chốt chỉ tiêu rất nhanh!""",

    "dieu_kien_tuyen_sinh": """📝 **Yêu cầu & Điều kiện tuyển sinh chi tiết (Cập nhật 2026):**

Viện SIGE áp dụng các tiêu chuẩn mới cho kỳ tuyển sinh 3/2026:

1. **Hệ 1+4 & VHVL:** 
   - GPA trung bình mỗi năm từ **6.0** trở lên.
   - Độ tuổi: 18 - 22 (đẹp nhất là 18-20).
   - Ngoại ngữ: Ưu tiên TOCFL A1/A2 để tăng tỷ lệ đỗ Visa.

2. **Hệ Thạc sĩ:**
   - Tốt nghiệp ĐH/CĐ (có kinh nghiệm). 
   - TOCFL A2/B1. Tuổi dưới 40.

3. **Hệ Tự túc:**
   - GPA từ 6.0. TOCFL A2 (hoặc IELTS 5.0+). 
   - Tự do đi làm, không phụ thuộc doanh nghiệp chỉ định.

**Điều kiện chung:**
- **Tài chính:** Sổ tiết kiệm từ 150 - 180 triệu VNĐ nộp trước khi xin Visa.
- **Sức khỏe:** Khám theo mẫu Đài Loan (khu vực miền Trung/Nam khám tại cơ sở chỉ định).
- **Pháp lý:** Không tiền án tiền sự, lý lịch tư pháp số 2 sạch.""",

    "ho_so_chuan_bi": """📂 **Danh mục hồ sơ cần chuẩn bị (7 Bước):**

1. **Học tập:** Bằng tốt nghiệp & Học bạ gốc (Bắt buộc scan lại 1 bản để lưu).
2. **Nhân thân:** Hộ chiếu (gốc), CCCD, Giấy khai sinh mẫu mới.
3. **Pháp lý:** Lý lịch tư pháp số 2.
4. **Sức khỏe:** Khám theo thông báo của Viện (tại VN và sau đó tại Đài Loan).
5. **Tài chính:** Sổ tiết kiệm 150 - 180 triệu VNĐ (tên SV hoặc bố mẹ).
6. **Ảnh:** 05 ảnh thẻ 4x6 chuẩn VP Đài Bắc.

Viện SIGE sẽ hỗ trợ trọn gói từ khâu dịch thuật đến nộp Visa!""",

    "quy_trinh_dang_ky": """🚀 **Quy trình hồ sơ tại SIGE (7 Bước):**

1. **Ký Hợp đồng:** Đặt cọc 10-20M VNĐ tùy gói. Điền form up dữ liệu hệ thống.
2. **Nộp hồ sơ:** Chuẩn bị 5 mục giấy tờ cơ bản (Hộ chiếu, Bằng cấp, v.v.).
3. **Phỏng vấn trường:** Viết tự truyện, kế hoạch học tập. Phỏng vấn Online/Trực tiếp.
4. **Chuẩn bị Visa:** Khám sức khỏe, chứng chỉ tiếng, Sổ tiết kiệm (150-180M).
5. **Nộp Visa:** SIGE nộp (1+4/VHVL) hoặc SV tự nộp dưới sự hướng dẫn.
6. **Đặt vé & Bay:** Xuất vé máy bay, tập trung tại sân bay trước 3 tiếng. 
7. **Hạ cánh:** Trường đón về KTX tại Đài Loan.

👉 Toàn bộ lộ trình được SIGE đồng hành sát sao!""",

    "hoc_bong_chung": """💰 **Chính sách Học bổng & Các gói Dịch vụ tại SIGE:**

Viện SIGE cung cấp các gói dịch vụ minh bạch cho mọi đối tượng:
- **Gói Cơ bản (36M):** Hồ sơ, dịch thuật, luyện phỏng vấn, Visa lần 1.
- **Gói VIP (55M):** Gồm Gói Cơ bản + Học tiếng A1/A2, Vé máy bay, Thẻ lưu trú, Bảo hiểm, Tư trang (chăn/ga/gối) tại Đài Loan.
- **Gói IELTS (70M):** Cam kết đầu ra IELTS 5.0 và trọn bộ dịch vụ VIP.

**Học bổng tiêu biểu:**
- **Lĩnh Đông (VHVL Chăm sóc sắc đẹp):** Miễn 100% học phí kỳ 1 nếu đạt A2.
- **Đài Cương (Văn bằng 2):** Miễn học phí & KTX + hỗ trợ sinh hoạt ~8 triệu VNĐ/tháng.

Liên hệ hotline **0938491111** để nhận bảng phí chi tiết!""",

    "co_hoi_viec_lam": """💼 **Thực tập & Việc làm (Chính sách 2026):**

SIGE cam kết lộ trình thực nghiệp an toàn:
- **Hệ VHVL:** Thực tập theo chỉ định của trường kỳ 2/4. Lương thực tập ~28.590 TWD/tháng.
- **Hệ Tự túc:** Sau 2 kỳ học tiếng (6 tháng) được cấp thẻ lao động, làm 20h/tuần tùy chọn công việc.
- **Cam kết đầu ra:** Với các hệ liên kết, lương kĩ sư chính thức sau tốt nghiệp từ 31.150 TWD/tháng trở lên.
- **Hỗ trợ định cư:** Chuyển đổi Visa Kỹ sư cho SV sau khi tốt nghiệp.""",

    "du_hoc_dai_loan": """🇹🇼 **Tại sao chọn Hệ sinh thái SIGE (Kỳ 3/2026)?**

Viện Khoa học Giáo dục Toàn Cầu hỗ trợ SV tiếp cận các chương trình độc quyền:
- **Chương trình 2+2+3:** Học tại Đài Loan -> Sang Mỹ (Đại học Lincoln) với gói tài trợ 70.000 USD.
- **Joint Degree 3+1:** Lĩnh Đông liên kết Anh/Úc, lấy song bằng quốc tế.
- **Hệ sinh thái VIP:** Lo cho bạn từ bữa ăn hạ cánh đến tư trang cá nhân tại KTX.
- **Hành lang Pháp lý:** Hỗ trợ xử lý nhanh Visa thẳng (1+4, VHVL) và cam kết minh bạch tài chính.

📞 Hotline: **0938491111**
📍 Địa chỉ: Tầng 4, Tòa VINATA 2B, 289 Khuất Duy Tiến, Hà Nội."""
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

def get_scripted_response(query: str) -> Optional[str]:
    """
    Checks if the user query matches any scripted response keywords.
    Returns the markdown response if found, otherwise None.
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
