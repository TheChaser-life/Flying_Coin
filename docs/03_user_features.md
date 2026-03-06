# 👤 Tính Năng Người Dùng & Mô Tả Giao Diện

## 1. Đăng Ký & Đăng Nhập (Auth)

### Luồng sử dụng
```
Truy cập website → Đăng ký (email/password hoặc Google OAuth)
→ Xác thực email → Đăng nhập → Vào Dashboard
```

### Chức năng chi tiết

| # | Chức năng | Mô tả |
|---|-----------|-------|
| 1 | **Đăng ký (Register)** | Email + password, xác thực email |
| 2 | **Đăng nhập (Login)** | Email/password → JWT access token + refresh token |
| 3 | **Đăng xuất (Logout)** | Hủy token, blacklist refresh token |
| 4 | **Quên mật khẩu** | Gửi email reset password |
| 5 | **OAuth 2.0** | Đăng nhập qua Google, GitHub (tùy chọn) |
| 6 | **Phân quyền (RBAC)** | Vai trò: Free User, Premium User, Admin |
| 7 | **API Key Management** | Tạo/quản lý API keys cho external access |
| 8 | **Rate Limiting** | Giới hạn request theo vai trò |

### Mô tả giao diện
- **Trang đăng nhập:** Form đơn giản (email + password), nút "Đăng nhập Google", link "Quên mật khẩu"
- **Trang đăng ký:** Form (tên, email, password, confirm password), nút đăng ký Google
- **Dark theme** mặc định, glassmorphism card, animation khi submit

---

## 2. Dashboard Tổng Quan

### Luồng sử dụng
```
Đăng nhập → Trang chủ Dashboard hiện ra tổng quan thị trường
```

### Người dùng thấy

| Thành phần | Nội dung | Vị trí |
|------------|----------|--------|
| **Market Summary** | VN-Index, S&P 500, Bitcoin, Vàng — tăng/giảm % | Header / Top row |
| **Top Gainers** | 5-10 mã tăng giá mạnh nhất hôm nay | Card bên trái |
| **Top Losers** | 5-10 mã giảm giá mạnh nhất hôm nay | Card bên phải |
| **Sentiment Gauge** | Đồng hồ Fear & Greed Index | Card trung tâm |
| **Alerts Panel** | Thông báo cảnh báo gần nhất | Sidebar phải |
| **Quick Search** | Thanh tìm kiếm mã chứng khoán/coin | Top navigation |

### Mô tả giao diện
- **Layout:** 3 cột (sidebar trái + nội dung chính + sidebar phải)
- **Cards:** Glassmorphism, bo góc, shadow nhẹ
- **Số liệu:** Màu xanh = tăng, màu đỏ = giảm, cập nhật real-time
- **Animations:** Số liệu giá nhấp nháy khi cập nhật, biểu đồ mini sparkline

---

## 3. Tra Cứu & Phân Tích Tài Sản

### Luồng sử dụng
```
Gõ mã (VD: "AAPL", "BTC") vào thanh tìm kiếm → Xem trang phân tích chi tiết
```

### Người dùng thấy

| Phần | Mô tả |
|------|-------|
| **Biểu đồ nến (Candlestick)** | Tương tác: zoom, kéo, xem theo 1D/1W/1M/1Y |
| **Chỉ báo kỹ thuật** | Bật/tắt SMA, EMA, RSI, MACD, Bollinger Bands |
| **Thông tin cơ bản** | Giá hiện tại, % thay đổi, volume, market cap |
| **Đường dự báo ML** | Đường nét đứt = giá dự báo 7-30 ngày tới |
| **Sentiment Bar** | Thanh từ 🔴 Tiêu cực ←→ 🟢 Tích cực |
| **Tin tức liên quan** | Danh sách tin mới nhất về mã đang xem |

### Mô tả giao diện
- **Chart:** Chiếm 60% diện tích, sử dụng TradingView Lightweight Charts
- **Toolbar trên chart:** Chọn timeframe, bật/tắt indicators, full screen
- **Panel phải:** Thông tin giá, sentiment, tin tức
- **Responsive:** Chart thu nhỏ trên mobile, panels chuyển thành tabs

---

## 4. Xem Dự Báo Giá (AI Forecasting)

### Luồng sử dụng
```
Trang phân tích tài sản → Tab "Dự báo AI"
→ Chọn khung thời gian (7/14/30 ngày) → Xem kết quả
```

### Người dùng thấy

| Thông tin | Ví dụ |
|-----------|-------|
| **Giá dự báo** | "BTC dự báo: $72,500 sau 7 ngày" |
| **Xu hướng** | 🟢 TĂNG (78% confidence) |
| **Khoảng dự báo** | $70,000 — $75,000 |
| **Biểu đồ** | Đường forecast + vùng confidence interval |
| **Tín hiệu** | 🟢 MUA / 🟡 GIỮ / 🔴 BÁN |
| **Model info** | "XGBoost — Accuracy 71%, MAPE 3.2%" |

### Mô tả giao diện
- **Forecast chart:** Đường thực = giá lịch sử, đường đứt = dự báo, vùng mờ = confidence
- **Signal badge:** Badge lớn hiển thị MUA/GIỮ/BÁN với màu tương ứng
- **Model selector:** Dropdown chọn mô hình (XGBoost, LSTM, Ensemble)
- **Comparison table:** So sánh kết quả nhiều mô hình cạnh nhau

---

## 5. Theo Dõi Tin Tức & Tâm Lý Thị Trường

### Luồng sử dụng
```
Tab "Tin tức & Sentiment" → Xem news feed + sentiment tracking
```

### Người dùng thấy

| Thành phần | Mô tả |
|------------|-------|
| **News Feed** | Danh sách tin, mỗi tin có badge 🟢/🟡/🔴 sentiment |
| **Sentiment Timeline** | Biểu đồ đường sentiment theo thời gian |
| **Fear & Greed Index** | Đồng hồ: 0 (Extreme Fear) → 100 (Extreme Greed) |
| **Word Cloud** | Đám mây từ khóa nổi bật |
| **Trending Topics** | "#Bitcoin", "#Fed_rate", "#AI_stocks" |

### Mô tả giao diện
- **Layout:** 2 cột — News Feed bên trái, Charts bên phải
- **News card:** Tiêu đề + nguồn + thời gian + sentiment badge + snippet
- **Fear & Greed:** Đồng hồ bán nguyệt với animation khi cập nhật
- **Word Cloud:** Interactive — click vào từ khóa để xem tin liên quan
- **Filter:** Lọc theo nguồn, sentiment, thời gian, mã cụ thể

---

## 6. Quản Lý & Tối Ưu Danh Mục Đầu Tư

### Luồng sử dụng
```
Tab "Danh mục" → Nhập tài sản đang nắm giữ
→ Chọn mức rủi ro (Thấp/Trung bình/Cao) → Bấm "Tối ưu hóa"
→ Nhận gợi ý phân bổ
```

### Người dùng thấy

**Bảng so sánh:**

| Tài sản | Hiện tại | Gợi ý tối ưu | Thay đổi |
|---------|----------|---------------|----------|
| AAPL | 35% | 30% | ↓ -5% |
| BTC | 40% | 25% | ↓ -15% |
| Vàng | 25% | 30% | ↑ +5% |
| ETH | 0% | 15% | ↑ +15% (mới) |

**Metrics:**

| Metric | Hiện tại | Sau tối ưu |
|--------|----------|------------|
| Expected Return | 12.5%/năm | 14.2%/năm |
| Volatility | 28.3% | 18.7% |
| Sharpe Ratio | 0.44 | 0.76 |
| Max Drawdown | -35% | -22% |

### Mô tả giao diện
- **Input form:** Bảng nhập tài sản (dropdown mã + số lượng + giá mua)
- **Risk slider:** Thanh kéo chọn mức rủi ro với 3 preset
- **Pie charts:** 2 pie chart cạnh nhau (hiện tại vs tối ưu)
- **Efficient Frontier:** Scatter plot, điểm đỏ = hiện tại, điểm xanh = tối ưu
- **Action buttons:** "Áp dụng gợi ý", "Xuất PDF", "Chia sẻ"

---

## 7. Backtesting

### Luồng sử dụng
```
Tab "Backtesting" → Chọn chiến lược & khoảng thời gian
→ Bấm "Chạy Backtest" → Xem kết quả lịch sử
```

### Người dùng thấy

| Metric | Ví dụ |
|--------|-------|
| Lợi nhuận tổng | +27.3% |
| Lợi nhuận/năm | +22.1% |
| Max Drawdown | -12.5% |
| Win Rate | 64% |
| So với Buy & Hold | Tốt hơn 8.2% |

### Mô tả giao diện
- **Input:** Dropdown chiến lược + Date range picker + Portfolio selector
- **Equity Curve:** Biểu đồ đường tăng trưởng tài sản
- **Drawdown chart:** Biểu đồ vùng hiển thị các đợt sụt giảm
- **Trade log:** Bảng liệt kê từng giao dịch backtest

---

## 8. Cài Đặt Cảnh Báo (Alerts)

### Luồng sử dụng
```
Tạo cảnh báo → Chọn điều kiện → Nhận thông báo qua email/web push
```

### Các loại cảnh báo

| Loại | Ví dụ |
|------|-------|
| **Giá** | "Thông báo khi BTC vượt $75,000" |
| **Sentiment** | "Thông báo khi AAPL sentiment < -0.5" |
| **AI Signal** | "Thông báo khi AI phát tín hiệu MUA mạnh" |
| **Danh mục** | "Thông báo khi cần tái cân bằng" |
| **Tin tức** | "Thông báo khi có breaking news về crypto" |

### Mô tả giao diện
- **Alert builder:** Form step-by-step (chọn loại → chọn mã → chọn điều kiện → chọn kênh)
- **Alert list:** Danh sách cảnh báo đang hoạt động với toggle bật/tắt
- **Alert history:** Log lịch sử cảnh báo đã trigger

---

## 9. User Journey Tổng Thể

```
Đăng ký / Đăng nhập
    │
    ▼
Dashboard (Tổng quan thị trường) ◄──── Cảnh báo 🔔
    │
    ├──► Tra cứu tài sản → Xem biểu đồ + chỉ báo kỹ thuật
    │         │
    │         ├──► Xem dự báo AI → Tín hiệu MUA/GIỮ/BÁN
    │         │
    │         └──► Xem tin tức + Sentiment
    │
    ├──► Quản lý danh mục → Tối ưu hóa → Gợi ý phân bổ
    │         │
    │         └──► Backtesting → Kiểm tra chiến lược
    │
    └──► Cài đặt cảnh báo → Nhận thông báo
```

---

## 10. Yêu Cầu UI/UX Chung

| Yêu cầu | Mô tả |
|----------|-------|
| **Dark mode** | Mặc định, phù hợp giao diện tài chính |
| **Responsive** | Desktop, tablet, mobile |
| **Real-time** | WebSocket cập nhật giá, sentiment, alerts |
| **Interactive charts** | Zoom, pan, tooltip, crosshair |
| **Glassmorphism** | Cards với blur, transparency, borders tinh tế |
| **Micro-animations** | Hover effects, loading skeletons, số nhảy khi cập nhật |
| **Drag & Drop** | Tùy chỉnh layout dashboard |
| **Typography** | Google Fonts (Inter / Outfit), hierarchy rõ ràng |
| **Color palette** | Xanh lá = tăng, đỏ = giảm, xanh dương/tím = accent |
