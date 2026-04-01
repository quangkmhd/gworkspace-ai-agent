# Tai lieu thiet ke Agent LangChain tich hop Google Workspace

## 1) Muc tieu
Xay dung mot AI Agent co the thao tac tren toan bo Google Workspace pho bien gom:
- Gmail
- Google Calendar
- Google Docs
- Google Sheets
- Google Drive

Agent can:
- Hieu yeu cau tu nhien tu nguoi dung
- Chon dung cong cu (tool) de thuc thi
- Dam bao an toan du lieu, kiem soat quyen, va kha nang audit

---

## 2) Kien truc tong quan

### 2.1 Cac lop chinh
- **Authentication Layer (OAuth 2.0)**  
  Chiu trach nhiem xac thuc nguoi dung Google, cap va lam moi token.
- **Service Layer (Google API Client)**  
  Tao va quan ly cac service theo tung API (Gmail, Calendar, Docs, Sheets, Drive).
- **Tool Layer (LangChain Tools/Toolkits)**  
  Chuyen cac thao tac API thanh tool de LLM goi duoc.
- **Agent Layer (LangChain/LangGraph)**  
  Dieu phoi suy luan, chon tool, goi tool, tong hop ket qua tra ve nguoi dung.

### 2.2 Luong xu ly chuan
- Nguoi dung gui yeu cau tu nhien
- Agent phan tich y dinh
- Agent chon 1 hoac nhieu tool
- Tool goi Google API tuong ung
- Tra ket qua ve Agent
- Agent tong hop ket qua de hieu cho nguoi dung
- Ghi log day du de theo doi/audit

---

## 3) Pham vi chuc nang theo tung Workspace app

### 3.1 Gmail
- Doc danh sach email
- Tim kiem email theo dieu kien
- Doc noi dung chi tiet email
- Soan va gui email
- Tra loi/forward email
- Gan nhan, danh dau da doc/chua doc
- Luu y: thao tac gui/xoa can xac nhan an toan

### 3.2 Google Calendar
- Xem lich theo ngay/tuan/thang
- Tao su kien hop
- Cap nhat thoi gian, dia diem, nguoi tham du
- Huy su kien
- Tim khung gio trong
- Luu y: chuan hoa mui gio va dinh dang thoi gian

### 3.3 Google Docs
- Tao tai lieu moi
- Ghi them noi dung
- Cap nhat cau truc co ban (tieu de/doan)
- Doc noi dung tai lieu
- Chia se tai lieu (neu can quyen Drive lien quan)

### 3.4 Google Sheets
- Doc du lieu theo vung
- Ghi du lieu theo vung
- Them dong du lieu moi
- Cap nhat gia tri o
- Truy van du lieu de phuc vu bao cao nhanh

### 3.5 Google Drive
- Tim kiem tep theo ten/loai/chu so huu
- Lay metadata tep
- Quan ly quyen chia se co ban
- Dieu huong cau truc thu muc
- Luu y: tuan thu quyen truy cap thuc te cua user

---

## 4) Thiet ke Tool Layer

### 4.1 Nguyen tac thiet ke tool
- Moi tool lam mot viec ro rang
- Input/output chat che, de kiem tra
- Ten tool phan anh hanh dong nghiep vu
- Co mo ta ngan de model chon dung tool
- Tool ghi log request/response da an du lieu nhay cam

### 4.2 Nguon tool
- **Toolkit co san**: Gmail, Calendar (dung nhanh, chuan hoa tot)
- **Custom tool**: Docs, Sheets, Drive (linh hoat theo nghiep vu that)

### 4.3 Chinh sach an toan tool
- Tac vu rui ro cao phai xac nhan truoc:
  - Gui email
  - Xoa/huy lich
  - Ghi de du lieu bang tinh
  - Chia se tep cho nguoi ngoai domain

---

## 5) Thiet ke Agent Layer

### 5.1 Mo hinh agent
- Dung agent theo phong cach tool-calling hien dai
- Khuyen nghi API moi (`create_agent`) thay cho luong cu (`create_react_agent`)
- Co the mo rong sang LangGraph khi can workflow nhieu buoc/phe duyet nguoi dung

### 5.2 Trach nhiem cua agent
- Nhan yeu cau nguoi dung
- Chuan hoa thong tin con thieu (thoi gian, id tai lieu, email nguoi nhan)
- Chon dung tool theo ngu canh
- Xu ly da cong cu trong mot yeu cau
- Tra loi ngan gon + minh bach cac hanh dong da thuc hien

### 5.3 Guardrails
- Khong tu dong thuc hien hanh dong pha huy neu chua xac nhan
- Khong suy doan email/nguoi nhan khi thieu chac chan
- Khong lo token/credential trong phan hoi
- Luon uu tien principle of least privilege

---

## 6) Xac thuc va phan quyen (OAuth 2.0)

### 6.1 Tai san xac thuc
- `credentials.json`: thong tin client tu Google Cloud
- `token.json`: access/refresh token cua nguoi dung sau khi consent

### 6.2 Scope chien luoc
- Chi cap scope can thiet theo use-case
- Tach profile user theo moi truong (dev/staging/prod)
- Khi mo rong chuc nang moi, review lai pham vi scope

### 6.3 Quan ly token production
- Khong luu token plain text tren may cuc bo khi trien khai that
- Luu token trong secret store hoac DB ma hoa
- Co co che rotate/revoke token dinh ky

---

## 7) Error handling va do tin cay

### 7.1 Nhom loi chinh
- Loi xac thuc/token het han
- Loi quyen (scope thieu hoac khong du permission)
- Loi du lieu dau vao (ID sai, dinh dang thoi gian sai)
- Loi quota/rate limit
- Loi mang/tam thoi tu Google API

### 7.2 Chinh sach xu ly
- Retry co kiem soat cho loi tam thoi
- Tra loi than thien, huong dan cach sua cho user
- Khong retry cac loi logic khong the thanh cong (vi du ID khong ton tai)
- Luon log ma loi chuan de debug

---

## 8) Quan sat he thong (Observability)

### 8.1 Can log
- User request (da mask thong tin nhay cam)
- Tool duoc goi va tham so chinh
- API response status
- Thoi gian xu ly tung buoc
- Trace ID xuyen suot phien

### 8.2 Chi so nen theo doi
- Ti le thanh cong theo tung tool
- Do tre trung binh/p95
- Ti le loi auth/quyen/quota
- So lan can xac nhan truoc hanh dong rui ro

---

## 9) Bao mat va tuan thu

- Nguyen tac toi thieu quyen truy cap
- Ma hoa thong tin nhay cam khi luu tru
- An du lieu PII trong log
- Tach tenant/user ro rang neu he thong multi-user
- Co co che thu hoi quyen nguoi dung ngay khi yeu cau

---

## 10) Kiem thu va nghiem thu

### 10.1 Kiem thu chuc nang
- Gmail: doc/tim/gui/reply
- Calendar: tao/cap nhat/huy su kien
- Docs: tao + them noi dung + doc
- Sheets: doc/ghi/them dong
- Drive: tim tep + lay metadata

### 10.2 Kiem thu phi chuc nang
- Token het han tu refresh
- Hanh vi khi thieu scope
- Chiu tai voi nhieu yeu cau lien tiep
- Do chinh xac chon tool cua agent

### 10.3 Tieu chi Go-live
- Ti le thanh cong API on dinh
- Khong co loi ro ri credential
- Co audit trail day du
- Co rollback/ke hoach xu ly su co

---

## 11) Lo trinh mo rong

- Tich hop phan quyen theo vai tro (RBAC)
- Bo sung approval workflow cho hanh dong nhay cam
- Ho tro domain policy cho to chuc (Workspace Admin constraints)
- Tu dong tao bao cao tong hop tu Gmail + Calendar + Sheets
- Ket hop memory ngu canh theo user de tang trai nghiem tro ly ca nhan
