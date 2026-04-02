import re
from typing import Optional

# Dictionary mapping identifying keys to scripted markdown responses
SCRIPTED_ANSWERS = {
    "danh_sach_truong": """🏫 **Danh sách các trường đại học liên kết với SIGE:**

Viện SIGE hiện liên kết với **12 ngôi trường cao cấp** tại Đài Loan, trong đó có các trường tiêu biểu:

1. **Đại học Quốc tế Minh Truyền (MCU):** Tiên phong tại Châu Á đạt chuẩn MSCHE (Hoa Kỳ). Ngành mũi nhọn: Truyền thông, Thiết kế, QTKD, CNTT, Bán dẫn.
2. **Đại học Quốc lập Ky Nam (NCNU):** Top 44 trường đại học xanh nhất thế giới, tọa lạc tại Đầm Nhật Nguyệt.
3. **Đại học Công nghệ Trung Tín (CTBC):** Trực thuộc ngân hàng CTBC, mạnh về Bán dẫn, AI, Cơ khí (đảm bảo thực tập và đầu ra).
4. **Đại học KHKT Lĩnh Đông (LTU):** Tọa lạc tại Đài Trung, nổi tiếng với ngành Thiết kế thuộc Top 100 thế giới.

👉 Bạn muốn tìm hiểu chi tiết về trường nào trong danh sách trên không?""",

    "hoc_bong_14": """🎯 **Chương trình Hệ chuyên ban Quốc tế 1+4 (Dự bị Đại học):**

Đây là lộ trình học tập linh hoạt nhất dành cho sinh viên Việt Nam:
- **Cấu trúc:** 1 năm học tiếng Trung dự bị + 4 năm học chuyên ngành chính quy.
- **Ưu điểm vượt trội:** 
  ✅ KHÔNG yêu cầu chứng chỉ ngoại ngữ khi nộp hồ sơ ban đầu.
  ✅ Miễn 100% học phí năm đầu tiên (tùy trường).
  ✅ Được chọn ngành học yêu thích sau khi hoàn thành năm dự bị.
- **Yêu cầu:** Đạt TOCFL A2 sau 1 năm học tiếng để chuyển tiếp vào chuyên ngành.

Đây là lựa chọn lý tưởng nếu bạn chưa có nền tảng tiếng Trung nhưng muốn du học ngay!""",

    "dieu_kien_tuyen_sinh": """📝 **Điều kiện tuyển sinh du học Đài Loan tại SIGE:**

Để tham gia các chương trình, bạn cần đáp ứng các tiêu chuẩn cơ bản sau:
1. **Học thuật:** Tốt nghiệp THPT với GPA mỗi học kỳ từ **7.0 trở lên** (hệ ngôn ngữ có thể từ 6.5).
2. **Độ tuổi:** 
   - Hệ Đại học: 18 - 22 tuổi.
   - Hệ Ngôn ngữ: Dưới 28 tuổi.
   - Hệ Thạc sĩ: Dưới 40 tuổi.
3. **Sức khỏe:** Có giấy khám sức khỏe theo mẫu Đài Loan, không mắc bệnh truyền nhiễm.
4. **Tài chính:** Sổ tiết kiệm từ **120 - 200 triệu VNĐ** (tùy hệ).
5. **Pháp lý:** Không có tiền án tiền sự.

Bạn có thắc mắc cụ thể về điều kiện nào không?""",

    "ho_so_chuan_bi": """📂 **Hồ sơ du học Đài Loan cần chuẩn bị:**

Bạn nên chuẩn bị sẵn các giấy tờ sau để quá trình làm thủ tục diễn ra nhanh chóng:
1. **Học tập:** Học bạ và Bằng tốt nghiệp THPT/Đại học (bản gốc).
2. **Định danh:** CCCD (photo), Hộ chiếu (gốc, còn hạn), Giấy khai sinh.
3. **Ảnh thẻ:** 05 ảnh theo quy chuẩn Văn phòng Đài Bắc (nền trắng, áo có cổ).
4. **Ngoại ngữ:** Chứng chỉ IELTS hoặc TOCFL (nếu có).
5. **Tài chính:** Sổ tiết kiệm (120 - 200 triệu VNĐ).
6. **Y tế:** Giấy khám sức khỏe & Phiếu tiêm chủng.
7. **Pháp lý:** Phiếu lý lịch tư pháp số 2.

Viện SIGE sẽ hỗ trợ bạn hoàn thiện và công chứng các giấy tờ này!""",

    "quy_trinh_dang_ky": """🚀 **Quy trình đăng ký du học tại SIGE (6 bước):**

1. **Nộp hồ sơ:** Gửi hồ sơ về SIGE hoặc điền form trực tuyến.
2. **Phỏng vấn:** Tham gia phỏng vấn với đại diện trường/doanh nghiệp.
3. **Xác nhận:** Hoàn thành thủ tục đặt cọc và phí hành chính.
4. **Nhận thông báo:** Nhận Giấy báo nhập học (Admission Letter) từ Đài Loan.
5. **Xin Visa:** SIGE hướng dẫn và hỗ trợ nộp hồ sơ xin visa.
6. **Nhập học:** Bay sang Đài Loan và bắt đầu hành trình mới!

Toàn bộ quy trình thường kéo dài từ 2-4 tháng tùy kỳ nhập học.""",

    "hoc_bong_chung": """💰 **Chính sách Học bổng và Hỗ trợ Tài chính tại SIGE:**

SIGE cam kết đồng hành cùng sinh viên săn học bổng giá trị cao:
- **Học bổng Nhà trường:** Miễn 100% học phí năm đầu, các năm sau xét theo GPA & TOCFL.
- **Tài trợ Doanh nghiệp (ASE, Liteon):** Tài trợ toàn phần 4 năm học + cam kết việc làm sau tốt nghiệp.
- **Trợ cấp sinh hoạt:** Một số chương trình hỗ trợ từ 6.600 - 10.000 TWD/tháng.
- **Yêu cầu duy trì:** Thường cần GPA > 80 và chứng chỉ tiếng Trung nâng cao dần theo từng năm.

Liên hệ SIGE ngay để được thiết kế lộ trình học bổng riêng cho bạn!""",

    "co_hoi_viec_lam": """💼 **Cơ hội việc làm sau tốt nghiệp:**

SIGE đảm bảo lộ trình nghề nghiệp vững chắc cho du học sinh:
- **Thực tập có lương:** Ngay khi đang học, sinh viên được thực tập tại các tập đoàn lớn (ASE, Liteon) với mức lương hỗ trợ hấp dẫn (~28.590 TWD/tháng).
- **Cam kết đầu ra:** Sinh viên tốt nghiệp hệ tài trợ doanh nghiệp được làm việc tại tập đoàn 2 năm với mức lương kỹ sư chính thức.
- **Hỗ trợ định cư:** SIGE hỗ trợ thủ tục chuyển đổi visa kỹ sư để làm việc lâu dài tại Đài Loan.
- **Lương tham khảo:** Lương chính thức khởi điểm từ 31.150 TWD/tháng trở lên.

Bạn muốn tìm hiểu thêm về việc làm tại Đài Loan hay Việt Nam?""",

    "du_hoc_dai_loan": """🇹🇼 **Tổng quan về Du học Đài Loan tại SIGE:**

Đài Loan là điểm đến giáo dục hàng đầu với chi phí tối ưu và cơ hội sự nghiệp rộng mở. Viện SIGE cung cấp các lộ trình du học trọn gói:

✨ **Các hệ đào tạo tiêu biểu:**
- **Hệ 1+4 (Dự bị Đại học):** 1 năm học tiếng + 4 năm chuyên ngành. Không cần chứng chỉ ngoại ngữ ban đầu.
- **Hệ Vừa học vừa làm:** Thực tập có lương tại doanh nghiệp ngay từ năm 2.
- **Hệ Thạc sĩ & Tiến sĩ:** Dành cho sinh viên muốn nâng cao trình độ chuyên môn.
- **Hệ Chuyên ban Bán dẫn:** Đào tạo kỹ sư cho các tập đoàn công nghệ hàng đầu thế giới (ASE, Liteon).

🏥 **Hỗ trợ toàn diện từ SIGE:**
- Có văn phòng đại diện tại **Đài Bắc, Đào Viên và Cao Hùng** để hỗ trợ sinh viên ngay khi nhập cảnh.
- Hợp tác với hơn 12 trường đại học danh tiếng và các tập đoàn lớn.
- Cam kết học bổng và việc làm sau tốt nghiệp.

👉 Bạn đang quan tâm đến hệ đào tạo nào cụ thể không?"""
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
    r"chương trình du học": "du_hoc_dai_loan"
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
