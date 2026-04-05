import re
from typing import Optional

# Dictionary mapping identifying keys to scripted markdown responses and CTAs
# Note: Since the bot_server now splits text and buttons, we can use up to 2000 chars here.
SCRIPTED_ANSWERS = {
    "danh_sach_truong": {
        "text": """🏫 **DANH SÁCH CÁC TRƯỜNG ĐẠI HỌC LIÊN KẾT CHIẾN LƯỢC (Kỳ 3/2026)**

Viện SIGE tự hào là đối tác tuyển sinh trực tiếp của các ngôi trường hàng đầu tại Đài Loan. Dưới đây là thông tin chi tiết để bạn lựa chọn:

1️⃣ **Đại học Minh Truyền (MCU):** 
- Ngôi trường đạt chuẩn kiểm định MSCHE của Hoa Kỳ.
- **Hệ 1+4:** Kỳ tháng 3/2026 chỉ còn khoảng **50 - 60 suất ưu tiên**. Trường ưu tiên tuyển sinh các đối tác liên minh đã hợp tác tại Việt Nam thông qua Viện SIGE.
- **Điểm mạnh:** Môi trường quốc tế, bằng cấp được công nhận toàn cầu.

2️⃣ **Đại học Lĩnh Đông (LTU):**
- Top đầu về đào tạo Thiết kế và Thời trang tại Đài Trung.
- **Hệ VHVL (Chăm sóc sắc đẹp):** Tặng học bổng **100% học phí kỳ 1** cho SV đạt TOCFL A2, hoặc **50%** cho SV đạt TOCFL A1. Tặng toàn bộ học liệu 4 năm.

3️⃣ **Đại học Đài Cương (TSU):**
- Chuyên sâu về Công nghệ Bán dẫn và Kĩ thuật.
- **Học bổng Đặc biệt:** Miễn 100% học phí & KTX toàn khóa học. Hàng tháng hỗ trợ sinh hoạt phí lên tới **8 triệu VNĐ**.

4️⃣ **Đại học Quốc tế Trung Tín (CTBC):**
- Trực thuộc ngân hàng lớn nhất Đài Loan. Miễn 100% học phí và ký túc xá kỳ đầu tiên cho sinh viên ưu tú.

5️⃣ **Đại học Quốc lập Kỵ Nam (NCNU):**
- Trường công lập xanh nhất thế giới. Miễn hoàn toàn học phí 2 năm đầu hệ tự túc hoặc 1 năm đầu hệ Thạc sĩ.

👉 *Để nhận được bảng phân tích chi tiết về học phí và chuyên ngành cụ thể cho từng trường, bạn hãy nhấn nút đăng ký tư vấn phía dưới nhé!*""",
        "buttons": [
            {"text": "📞 Kiểm tra GPA", "callback": "start_lead_form"},
            {"text": "📂 Hồ sơ chuẩn bị", "callback": "ask_ho_so_chuan_bi"}
        ]
    },

    "hoc_bong_14": {
        "text": """🎯 **CHƯƠNG TRÌNH HỆ CHUYÊN BAN QUỐC TẾ 1+4 (DỰ BỊ ĐẠI HỌC)**

Đây là lộ trình du học "Hot" nhất tại SIGE dành cho kỳ tuyển sinh tháng 3/2026 nhờ chính sách hỗ trợ cực kỳ tốt từ Bộ Giáo dục Đài Loan.

✅ **Định nghĩa:** Bạn dành 1 năm đầu tiên để học tiếng Trung tập trung. Sau khi đạt trình độ A2, bạn sẽ chính thức bước vào 4 năm đại học chuyên ngành.

✨ **Chính sách ưu đãi:**
- **Năm nhất:** Phần lớn các trường sẽ được Bộ Giáo dục hỗ trợ **50% - 100% học phí**. Bạn chỉ cần đóng các khoản tạp phí nhỏ.
- **Năm 2 - Năm 5:** Học bổng dựa trên thành tích GPA hàng năm (thường duy trì mức học bổng nếu kết quả học tập tốt).

⚠️ **Lưu ý quan trọng:**
- **Học thuật:** GPA 3 năm THPT (cả 6 kỳ) tối thiểu đạt **6.0**. Tuổi từ 18-20 là đẹp nhất.
- **Tiếng Trung:** Không yêu cầu bằng cấp lúc apply, nhưng cần đạt TOCFL A2 sau 1 năm để ở lại Đài Loan. Nếu không đạt, sinh viên sẽ buộc phải về nước.

🔥 *Hệ 1+4 chốt hồ sơ rất sớm do giới hạn chỉ tiêu của từng trường. Hãy liên hệ SIGE ngay để giữ suất!*""",
        "buttons": [
            {"text": "📥 Nhận 50 suất ưu tiên", "callback": "start_lead_form"},
            {"text": "🏫 Xem danh sách trường", "callback": "ask_danh_sach_truong"}
        ]
    },

    "he_vhvl_detail": {
        "text": """💆 **HỆ VỪA HỌC VỪA LÀM (VHVL) - NGÀNH CHĂM SÓC SẮC ĐẸP**

Chương trình dành cho các bạn muốn học nghề chuyên sâu và có thu nhập ngay trong quá trình thực tập tại Đài Loan.

🎓 **Lộ trình học tập:** 
Sinh viên học 4 năm, kết hợp giữa học lý thuyết trên lớp và đi thực tập thực hành tại các doanh nghiệp do nhà trường chỉ định (thường là năm 2 và năm 4).

💰 **Lợi ích tài chính:**
- Hưởng mức lương thực tập theo quy định của Đài Loan (~28.590 TWD/tháng, khoảng 22 triệu VNĐ).
- **Học bổng LTU:** Hiện Viện SIGE có **20 suất độc quyền** tại ĐH Lĩnh Đông với mức học bổng 100% (nếu có A2) hoặc 50% (nếu có A1) học phí kỳ đầu.

📋 **Điều kiện ứng tuyển:**
- GPA 3 năm cấp 3 đạt tối thiểu **6.0**. Tuổi từ 18-22.
- Cần có chứng chỉ TOCFL A1 ngay khi nộp hồ sơ (và nỗ lực đạt A2 để tăng tỷ lệ đỗ Visa).

👉 *Đây là chương trình có tỷ lệ Visa thẳng rất cao, phù hợp cho những bạn yêu thích ngành thẩm mỹ và dịch vụ!*""",
        "buttons": [
            {"text": "✅ Đăng ký ưu tiên", "callback": "start_lead_form"},
            {"text": "🏫 Các hệ khác", "callback": "show_program_menu"}
        ]
    },

    "he_thac_si_detail": {
        "text": """🎓 **CHƯƠNG TRÌNH DU HỌC THẠC SĨ (Kỳ 3/2026)**

Nâng cao trình độ chuyên môn và mở rộng cơ hội nghề nghiệp quốc tế cùng hệ Thạc sĩ Đài Loan.

🏢 **Trường liên kết tiêu biểu:**
- **Đại học Lĩnh Đông (LTU):** Học bổng **100% học phí** chuyên ngành MBA (Quản trị doanh nghiệp). Các ngành Du lịch, Khách sạn hỗ trợ 50% tùy kỳ.
- **Đại học Quốc lập Kỵ Nam:** Miễn 100% học phí năm đầu tiên cho số ít sinh viên đăng ký sớm.
- **Đại học Minh Truyền:** Chương trình quốc tế giảng dạy bằng tiếng Anh hoặc tiếng Trung.

📋 **Điều kiện ứng tuyển:**
- Tốt nghiệp Đại học tại Việt Nam (hoặc Cao đẳng với tối thiểu 3 năm kinh nghiệm làm việc).
- Chứng chỉ TOCFL tối thiểu A2 (Khuyên dùng B1 để tỷ lệ Visa cao nhất).
- Chuyên ngành đăng ký Thạc sĩ nên tương đồng với ngành đã học ở bậc Đại học.

👉 *Học Thạc sĩ giúp bạn có cơ hội định cư và làm việc lâu dài tại Đài Loan với mức lương kĩ sư/quản lý hấp dẫn!*""",
        "buttons": [
            {"text": "✍️ Tư vấn chọn ngành", "callback": "start_lead_form"},
            {"text": "📞 Gặp tư vấn viên", "callback": "show_contact"}
        ]
    },

    "he_ngon_ngu_detail": {
        "text": """🗣️ **HỆ NGÔN NGỮ (Học Tiếng Trung tại Đài Loan)**

Lựa chọn linh hoạt cho các bạn muốn nâng cao trình độ ngoại ngữ trước khi học lên chuyên ngành hoặc đi làm.

📅 **Kỳ nhập học:** Cực kỳ linh hoạt, bình quân 3 tháng một lần (tháng 3-7-9-12). Một số trường như Minh Truyền có thể mở lớp hàng tháng nếu đủ 10-15 SV.
⏳ **Thời gian học:** Tối thiểu 3 tháng, tối đa 2 năm. Mỗi kỳ học kéo dài 3 tháng.

💰 **Chi phí dự kiến:**
- Học phí: ~28.000 – 32.000 TWD/kỳ.
- Ký túc xá/Thuê nhà: ~5.000 - 12.000 TWD/tháng.

📋 **Lưu ý:**
- Điều kiện đầu vào: GPA cấp 3 từ 6.0, chứng chỉ TOCFL A1.
- Sau 6 tháng (2 kỳ học), bạn được cấp thẻ lao động để làm thêm 20h/tuần.
- Sau khi đạt trình độ A2, bạn có thể xin báo danh lên các chương trình Đại học hoặc Thạc sĩ tại Đài Loan.

👉 *Đây là con đường an toàn nhất để làm quen với cuộc sống tại Đài Loan trước khi quyết định học dài hạn!*""",
        "buttons": [
            {"text": "🚀 Đăng ký kỳ bay sớm nhất", "callback": "start_lead_form"}
        ]
    },

    "tai_chinh_goi_dich_vu": {
        "text": """💰 **CÁC GÓI DỊCH VỤ DỊCH VỤ TƯ VẤN TRỌN GÓI TẠI SIGE**

Viện SIGE cung cấp các gói dịch vụ minh bạch, cam kết không phát sinh ẩn phí trong quá trình xử lý:

1️⃣ **Gói Dịch vụ Cơ bản (36.000.000 VNĐ):**
- Xử lý hồ sơ báo danh 2 nguyện vọng.
- Dịch thuật, công chứng, hợp thức hóa hồ sơ.
- Luyện phỏng vấn trường và phỏng vấn Visa.
- Khám sức khỏe tại Việt Nam & Lệ phí Visa lần 1.

2️⃣ **Gói Dịch vụ VIP (55.000.000 VNĐ):**
- Bao gồm toàn bộ danh mục trọn gói của Gói Cơ bản.
- **Tặng thêm:** Gói đào tạo tiếng Trung online/offline đạt trình độ A1-A2.
- **Tặng thêm:** Vé máy bay 1 chiều sang Đài Loan.
- **Hỗ trợ tại Đài Loan:** Thẻ lưu trú, thẻ lao động, bảo hiểm 6 tháng đầu, trọn bộ tư trang (chăn, ga, gối).

3️⃣ **Gói Du học bằng Tiếng Anh (70.000.000 VNĐ):**
- Bao gồm toàn bộ danh mục của Gói VIP.
- **Đặc biệt:** Đào tạo tiếng Anh IELTS cam kết đầu ra 5.0.

👇 *Nhấn nút bên dưới để xem bảng ước tính tổng tài chính cần chuẩn bị khi sang Đài Loan!*""",
        "buttons": [
            {"text": "📊 Bảng phí chi tiết", "callback": "ask_tai_chinh_tong_quan"},
            {"text": "📞 Tư vấn gói phù hợp", "callback": "start_lead_form"}
        ]
    },

    "tai_chinh_tong_quan": {
        "text": """📊 **ƯỚC TÍNH TỔNG TÀI CHÍNH DU HỌC ĐÀI LOAN (KỲ 2026)**

Ngoài phí dịch vụ tại Việt Nam, đây là những khoản bạn cần chuẩn bị để khởi hành chuyên nghiệp:

1. **Phí Dịch vụ tại SIGE:** 36M - 55M VNĐ (Tùy chọn gói).
2. **Chứng minh tài chính:** Sổ tiết kiệm 150M - 180M VNĐ (Chi phí làm dịch vụ STK mất khoảng 500k - 4M nếu gia đình không có sẵn sổ).
3. **Tiền học phí & KTX kỳ 1 (Đóng tại ĐL):** 
   - Học phí: ~36M - 41M VNĐ.
   - KTX & Tạp phí: ~9M - 12M VNĐ.
   *(Lưu ý: Các khoản này sẽ được giảm/miễn nếu bạn có học bổng).*
4. **Tiền ăn uống & tiêu vặt (2 tháng đầu):** ~10M VNĐ.

✨ **TỔNG CỘNG:** Dao động từ **120M - 130M VNĐ** cho chi phí ban đầu khi sang đến Đài Loan (trong trường hợp không có học bổng miễn học phí).

👉 *Hãy liên hệ SIGE để được tư vấn các ngôi trường có mức Học bổng tốt nhất nhằm giảm thiểu gánh nặng tài chính!*""",
        "buttons": [
            {"text": "💼 Tìm học bổng giảm phí", "callback": "ask_hoc_bong_chung"}
        ]
    },

    "ho_so_chuan_bi": {
        "text": """📂 **DANH MỤC HỒ SƠ CẦN CHUẨN BỊ (7 BƯỚC CHUYÊN NGHIỆP)**

Để kịp kỳ bay tháng 3/2026, bạn nên chuẩn bị sớm các giấy tờ sau:

1️⃣ **Hồ sơ Học thuật:** Bằng tốt nghiệp THPT (hoặc bằng CĐ/ĐH) và Học bạ/Bảng điểm gốc.
2️⃣ **Hồ sơ Cá nhân:** Hộ chiếu, CCCD, Giấy khai sinh bản sao mẫu mới nhất.
3️⃣ **Lý lịch tư pháp:** Bản số 2 (do Sở Tư pháp cấp).
4️⃣ **Sức khỏe:** Khám sức khỏe tổng quát theo mẫu du học tại các bệnh viện chỉ định.
5️⃣ **Tài chính:** Sổ tiết kiệm gốc (từ 150 - 180 triệu VNĐ) mang tên SV hoặc Bố/Mẹ.
6️⃣ **Chứng chỉ ngoại ngữ:** Bản gốc chứng chỉ TOCFL hoặc IELTS tương ứng với hệ du học.

👉 *Viện SIGE sẽ hỗ trợ bạn scan, dịch thuật, công chứng và nộp hồ sơ xin giấy phép từ các cơ quan ban ngành tại Đài Loan.*""",
        "buttons": [
            {"text": "🚀 Bắt đầu làm hồ sơ", "callback": "ask_quy_trinh_chi_tiet"}
        ]
    },

    "quy_trinh_chi_tiet": {
        "text": """🚀 **QUY TRÌNH HỒ SƠ CHUẨN TẠI VIỆN SIGE (7 BƯỚC)**

Bạn sẽ được cán bộ chuyên trách của Viện hỗ trợ từng bước một:

1. **Bước 1 (Ghi danh):** Ký hợp đồng tư vấn, nộp tiền cọc (10-20M) và điền form online.
2. **Bước 2 (Nộp hồ sơ):** SV nộp 5 mục hồ sơ cơ bản (Bằng, học bạ, hộ chiếu...).
3. **Bước 3 (Luyện phỏng vấn):** SV viết tự truyện, kế hoạch học tập và phỏng vấn với trường bên Đài Loan.
4. **Bước 4 (Nộp Visa):** Sau khi có thông báo đỗ trường, SV đi khám sức khỏe và chuẩn bị sổ tiết kiệm gốc để nộp Visa.
5. **Bước 5 (Phỏng vấn Visa):** Tùy hệ du học, SV có thể phải phỏng vấn trực tiếp tại Văn phòng Kinh tế & Văn hóa Đài Bắc (VPDB).
6. **Bước 6 (Tập kết & Bay):** Sau khi có Visa, Viện xuất vé máy bay và hướng dẫn SV tập kết tại sân bay Nội Bài/Tân Sơn Nhất.
7. **Bước 7 (Hạ cánh):** Trường đón SV tại sân bay Đài Loan, đưa về KTX và hỗ trợ làm thẻ cư trú.

👉 *Toàn bộ quy trình thường kéo dài từ 3-4 tháng. Hãy bắt đầu ngay hôm nay!*""",
        "buttons": [
            {"text": "✍️ Đăng ký tư vấn lộ trình", "callback": "start_lead_form"}
        ]
    },

    "hoc_bong_chung": {
        "text": """💰 **CHÍNH SÁCH HỌC BỔNG & HỖ TRỢ TÀI CHÍNH TẠI SIGE**

SIGE cam kết giúp sinh viên tối ưu hóa chi phí thông qua quỹ học bổng doanh nghiệp và chính sách của nhà trường:

- **Học bổng 100%:** Dành cho sinh viên ưu tú hệ VHVL hoặc các trường như Đài Cương, John...
- **Học bổng Chính phủ (Hệ 1+4):** Miễn phí năm đầu tiên cho hầu hết sinh viên.
- **Gói Hỗ trợ SIGE:** Giảm phí dịch vụ cho SV có thành tích xuất sắc hoặc hoàn cảnh khó khăn.

⚠️ **Lưu ý:** Ngay khi sang Đài Loan, sinh viên vẫn nên chuẩn bị một khoản tiền nhỏ (~40M) để đóng các tạp phí ban đầu, sau đó nhà trường sẽ xét duyệt hồ sơ và hoàn lại tiền học bổng theo quy định.

👇 *Để biết chính xác mức Học bổng bạn có thể đạt được dựa trên GPA hiện tại, hãy nhấn nút phía dưới!*""",
        "buttons": [
            {"text": "💰 Tính phí ưu đãi", "callback": "start_lead_form"},
            {"text": "📞 Gặp tư vấn viên", "callback": "show_contact"}
        ]
    },

    "co_hoi_viec_lam": {
        "text": """💼 **THỰC TẬP & CƠ HỘI VIỆC LÀM TẠI ĐÀI LOAN (Kỳ 2026)**

Du học Đài Loan không chỉ là học tập, mà còn là bước khởi đầu cho sự nghiệp quốc tế bền vững.

🔹 **Trong quá trình học:** 
- Bạn được phép đi làm thêm 20h/tuần (thu nhập ~15-18 triệu VNĐ/tháng).
- Hệ VHVL thực tập tại doanh nghiệp đối tác với mức lương hỗ trợ lên đến 22 triệu VNĐ/tháng.

🔹 **Sau khi tốt nghiệp:**
- SIGE cam kết kết nối sinh viên với các doanh nghiệp tại Đài Loan để làm việc chính thức.
- Mức lương khởi điểm cho kĩ sư/biên dịch trình độ đại học từ **31.150 TWD/tháng** (~25 triệu VNĐ) trở lên.
- Hỗ trợ thủ tục chuyển đổi sang Visa lao động dài hạn hoặc định cư.

👉 *Đài Loan đang rất thiếu nhân lực chất lượng cao trong các ngành Công nghệ, Dịch vụ và Y tế!*""",
        "buttons": [
            {"text": "💼 Tìm việc làm lương cao", "callback": "start_lead_form"}
        ]
    },

    "du_hoc_dai_loan": {
        "text": """🇹🇼 **HỆ SINH THÁI DU HỌC SIGE - TẦM NHÌN 20 NĂM**

Chào mừng bạn đến với SIGE AI - hệ thống hỗ trợ du học chuyên sâu được vận hành bởi Viện Khoa học Giáo dục Toàn Cầu.

✨ **Tại sao bạn nên chọn SIGE?**
- **Đối tác Chiến lược:** Liên kết trực tiếp với các trường đại học hàng đầu, đảm bảo tỷ lệ đỗ trường 99%.
- **Bảo trợ Trọn đời:** Chúng tôi có văn phòng tại Đài Loan để hỗ trợ bạn những lúc gặp khó khăn trong sinh hoạt, ốm đau hay chuyển công tác.
- **Minh bạch:** Phí dịch vụ rõ ràng, lộ trình đào tạo bài bản.

✨ **Vibe từ Viện trưởng:**
> *"Với mạng lưới 20 năm tâm huyết tại Đài Loan của tôi, SIGE không chỉ đưa bạn đi học, mà là đưa bạn vào một hệ sinh thái bảo trợ trọn đời. Sự thành công của sinh viên là thước đo giá trị lớn nhất của Viện SIGE."* 
— **ThS. Nguyễn Thị Điệp** (Viện trưởng SIGE)

📞 Hotline tư vấn: **0938491111**
📍 Địa chỉ: Tầng 4, Tòa VINATA 2B, 289 Khuất Duy Tiến, TP. Hà Nội.
🌐 Website: **www.sige.edu.vn**""",
        "buttons": [
            {"text": "🚀 Đăng Ký Tư Vấn VIP 1-1", "url": "https://zalo.me/0938491111"}
        ]
    }
}

# Mapping of common phrase patterns to keys
# Each regex aims to capture the "core" intent with minimal word overhead
QUERY_MAPPING = {
    r"trường|danh sách|đại học|list trường": "danh_sach_truong",
    r"1\+4|dự bị|học tiếng trước": "hoc_bong_14",
    r"vhvl|vừa học làm|vừa học vừa làm|thực tập có lương": "he_vhvl_detail",
    r"thạc sĩ|thạc sỹ|sau đại học|master": "he_thac_si_detail",
    r"học tiếng|ngôn ngữ|trung tâm hoa ngữ|lớp tiếng": "he_ngon_ngu_detail",
    r"hồ sơ|thủ tục|giấy tờ|điều kiện|yêu cầu": "ho_so_chuan_bi",
    r"quy trình|các bước|lộ trình|phải làm gì": "quy_trinh_chi_tiet",
    r"học bổng|miễn phí|giảm phí|ưu đãi": "hoc_bong_chung",
    r"việc làm|làm gì xong|cơ hội nghề": "co_hoi_viec_lam",
    r"du học đài loan|tìm hiểu sige": "du_hoc_dai_loan",
    r"chi phí|giá|bao nhiêu tiền|tổng tiền|tài chính": "tai_chinh_tong_quan",
    r"gói dịch vụ|gói tư vấn|trọn gói": "tai_chinh_goi_dich_vu"
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
