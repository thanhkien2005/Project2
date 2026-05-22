# Thông tư nội bộ TT-03

## Quy trình định giá theo phương pháp DCF (Discounted Cash Flow)

**Mã hiệu:** TT-03/ACBS/2025
**Ngày ban hành:** 28/03/2025
**Phòng ban áp dụng:** Phòng Phân tích Cơ bản
**Người duyệt:** Giám đốc Phân tích

### 1. Mục đích

Chuẩn hóa các bước định giá doanh nghiệp theo phương pháp Chiết khấu dòng tiền tự do của doanh nghiệp (DCF — Discounted Cash Flow), áp dụng cho doanh nghiệp phi tài chính.

### 2. Phạm vi áp dụng

Áp dụng cho phân tích định giá tất cả ngành ngoại trừ ngân hàng, bảo hiểm, chứng khoán (3 ngành này dùng phương pháp riêng: P/B, Embedded Value, P/E forward).

### 3. Quy trình 5 bước

**Bước 1 — Dự phóng dòng tiền tự do FCFF (Free Cash Flow to Firm):**
Công thức: FCFF = EBIT × (1 − Thuế suất) + Khấu hao − CapEx − ΔWC
Trong đó:
- EBIT: Lợi nhuận trước lãi vay và thuế
- ΔWC: Thay đổi vốn lưu động ròng
- CapEx: Chi đầu tư tài sản cố định

Dự phóng 5 năm chi tiết (Year 1 đến Year 5). Tốc độ tăng trưởng năm Year 1-3 dựa trên kế hoạch doanh nghiệp + nhận định ngành. Year 4-5 hội tụ về tăng trưởng dài hạn ngành. Dự phóng phải có ít nhất 3 kịch bản: bear case, base case, bull case.

**Bước 2 — Tính Chi phí vốn bình quân gia quyền (WACC):**
Công thức: WACC = (E/V) × Re + (D/V) × Rd × (1 − T)
Trong đó:
- Re (chi phí vốn chủ sở hữu) = Rf + β × Risk Premium
  - Rf = lãi suất Trái phiếu Chính phủ kỳ hạn 10 năm
  - β = beta cổ phiếu (so với VN-Index, lấy 5 năm)
  - Risk Premium thị trường VN: 7%-8%
- Rd (chi phí nợ vay) = lãi suất vay bình quân doanh nghiệp (sau thuế)
- E/V và D/V: tỷ trọng vốn chủ và nợ trên tổng vốn (theo giá thị trường)
- T: thuế suất TNDN hiệu dụng (thường 20%)

WACC điển hình DN VN: 11%-15%. WACC dưới 10% phải có lý do chính đáng (DN nhà nước, ngành ổn định cao).

**Bước 3 — Tính Giá trị cuối kỳ (Terminal Value):**
TV = FCFF Year 6 / (WACC − g)
Với g là tăng trưởng dài hạn ổn định, thường lấy 2.5%-3.5% (gần với GDP tiềm năng VN dài hạn). g KHÔNG được vượt quá WACC trừ 200bps.

**Bước 4 — Phân tích độ nhạy (Sensitivity Analysis):**
Lập ma trận 2 chiều: WACC (±1%) × g (±0.5%). Báo cáo dải giá mục tiêu (low-base-high case). Phải có ít nhất bảng 3×3 hoặc 5×5 trong phụ lục báo cáo.

**Bước 5 — Tính Giá mục tiêu/cổ phiếu:**
Equity Value = Σ PV(FCFF Year 1-5) + PV(Terminal Value) − Nợ ròng + Tiền và các khoản tương đương tiền
Giá mục tiêu = Equity Value / Số cổ phiếu lưu hành (đã pha loãng)

Trong đó Nợ ròng = Tổng nợ vay − Tiền và tương đương tiền − Đầu tư tài chính ngắn hạn.

### 4. Ghi chú

- Mọi giả định phải được nêu rõ trong báo cáo (Assumptions table).
- Khi định giá ra giá mục tiêu chênh lệch trên 30% so với giá thị trường, phải re-check giả định và xin ý kiến Giám đốc Phân tích trước khi phát hành.
- Cập nhật mô hình DCF tối thiểu mỗi 6 tháng hoặc khi có sự kiện trọng yếu (M&A, thay đổi cơ cấu vốn lớn, thay đổi chính sách thuế).
- Đối với doanh nghiệp có chu kỳ kinh doanh ngắn (FMCG, bán lẻ), nên dự phóng 7-10 năm thay vì 5 năm.
