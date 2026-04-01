# Chi tiết các thành phần hệ thống (Component Breakdown)

Dưới đây là chi tiết các thành phần quan trọng đã được tạo ra trong hệ thống **GWorkspace AI Agent**:

### 1. Lõi Agent (Agent Core - `agent/`)
Đây là "bộ não" điều khiển mọi hoạt động của AI:
- **`planner.py`**: Lập kế hoạch các bước thực thi dựa trên yêu cầu người dùng.
- **`executor.py`**: Điều phối việc gọi các công cụ (tools) và xử lý kết quả trả về bằng LangGraph.
- **`risk_evaluator.py`**: Tự động đánh giá mức độ rủi ro của một hành động (ví dụ: xóa file là rủi ro cao, đọc email là rủi ro thấp).
- **`prompts.py`**: Chứa các "chỉ thị" (System Prompts) tối ưu để AI hoạt động chính xác.
- **`schemas.py`**: Định nghĩa cấu trúc dữ liệu cho trạng thái của Agent (AgentState).

### 2. Hệ thống Backend & API (`backend/`)
Cung cấp giao diện kết nối giữa người dùng và Agent:
- **`main.py`**: Khởi chạy ứng dụng FastAPI và đăng ký các routes.
- **`config.py`**: Quản lý cấu hình hệ thống (biến môi trường, cài đặt ứng dụng).
- **`routes/`**: Các cổng kết nối (Endpoints):
    - `agent`: Giao tiếp trực tiếp với AI Agent.
    - `auth`: Quy trình đăng nhập Google OAuth2 (start, callback, refresh).
    - `hitl`: Quản lý việc phê duyệt các hành động từ phía con người.
    - `audit`: Truy xuất lịch sử hoạt động và log bảo mật.
    - `workspace/`: Các API wrapper cho Gmail, Calendar, Drive, Docs, Sheets.
- **`middleware/`**: Các lớp xử lý trung gian như Xác thực (Auth), Logging, Request ID, và Idempotency (chống trùng lặp).
- **`services/`**: Logic nghiệp vụ cốt lõi:
    - `oauth_service.py` & `token_store.py`: Quản lý Token Google một cách an toàn.
    - `policy_service.py`: Kiểm tra quyền hạn và chính sách bảo mật.
    - `agent_service.py`: Quản lý vòng đời của các Task vụ Agent.

### 3. Công cụ tích hợp Google Workspace (`tools/`)
Bộ công cụ giúp AI tương tác trực tiếp với dữ liệu Google:
- **Modules**: `gmail`, `calendar`, `drive`, `docs`, `sheets`.
- **`adapter.py`**: Tích hợp thực tế với Google API thông qua LangChain hoặc thư viện client.
- **`mock.py`**: Giả lập dữ liệu để phục vụ việc kiểm thử mà không tốn tài nguyên hoặc ảnh hưởng dữ liệu thực.
- **`registry.py`**: Trung tâm đăng ký và quản lý tất cả các Tools sẵn có.

### 4. Cơ chế Kiểm soát & Phê duyệt (`hitl/` - Human-In-The-Loop)
Đảm bảo an toàn tuyệt đối khi AI thực hiện các tác vụ quan trọng:
- **`workflow.py`**: Quy trình phối hợp giữa việc tạo yêu cầu phê duyệt và thực thi sau khi được duyệt.
- **`state_machine.py`**: Quản lý các trạng thái luân chuyển (Pending -> Approved/Rejected).
- **`policy_engine.py`**: Tự động quyết định xem một hành động có cần sự can thiệp của con người hay không dựa trên Risk Score.
- **`audit.py`**: Ghi log chi tiết mọi thao tác nhạy cảm để phục vụ kiểm tra sau này.

### 5. Cấu hình & Hạ tầng (`configs/`)
- **`oauth_scopes.yaml`**: Định nghĩa các phạm vi quyền hạn (Scopes) cần thiết.
- **`risk_policy.yaml`**: Quy tắc phân loại rủi ro cho từng loại hành động.
- **`tool_manifest.json`**: Mô tả kỹ thuật của các công cụ để LLM có thể hiểu và gọi lệnh đúng.

### 6. Hệ thống Kiểm thử (`tests/`)
Hệ thống test đa tầng đảm bảo độ tin cậy:
- **`unit/`**: Kiểm tra các logic cô lập (Risk Evaluator, State Machine).
- **`integration/`**: Kiểm định luồng làm việc giữa các Service (Auth flow, HITL flow).
- **`e2e/`**: Thử nghiệm các kịch bản thực tế phức tạp từ đầu đến cuối.
