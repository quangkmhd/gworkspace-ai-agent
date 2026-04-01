# Hướng dẫn đọc Code GWorkspace AI Agent

Dưới đây là sơ đồ và thứ tự khuyến nghị để bạn đọc từ đầu đến cuối toàn bộ codebase của dự án. Thứ tự này giúp bạn đi từ nền tảng cấu hình, cấu trúc dữ liệu cơ bản, đến việc xử lý request (route, middleware), logic service, các tích hợp API, rồi kết thúc tại trái tim của hệ thống (Agent và HITL).

---

## Tầng 1: Cấu hình và Khởi tạo (Config & App Entrypoint)
*Nên đọc đầu tiên để hiểu ứng dụng chạy lên thế nào và phụ thuộc vào những biến môi trường nào.*

1. **`backend/config.py`**
   - **Nhiệm vụ:** Định nghĩa cấu hình hệ thống bằng Pydantic. 
   - **Thành phần chính:** Phân tích class `Settings`, `Environment` và hàm `get_settings`. File này chứa các biến chỉ mục tới thư mục dữ liệu, gốc dự án, v.v.

2. **`backend/main.py`**
   - **Nhiệm vụ:** Điểm khởi đầu của ứng dụng FastAPI.
   - **Hàm chính:** 
     - `create_app`: Tạo instances, gắn các file router API config vào FastAPI. 
     - `lifespan`: Thiết lập lifecycle của app.
     - `_register_routes`: Cài đặt các API endpoints.

---

## Tầng 2: Cấu trúc dữ liệu (Schemas / Data Models)
*Nắm vững schema giúp bạn hiểu mọi dữ liệu luân chuyển giữa các layer.*

3. **`backend/schemas/common.py`**
   - **Nhiệm vụ:** Định nghĩa Enum (`RiskLevel`, `ApprovalStatus`, v.v.) và các hàm base chung.
   - **Hàm chính:** `generate_id`, `generate_task_id`, `generate_request_id` phục vụ cho việc random chuỗi định danh.

4. **`backend/schemas/envelope.py`**
   - **Nhiệm vụ:** Bọc response thống nhất (`ResponseEnvelope`), trả về kết quả chuẩn theo format cấu trúc JSON.
   
5. **`backend/schemas/action.py`**
   - **Nhiệm vụ:** Định nghĩa payload cho Task (`CreateTaskRequest`), Approval (`ApprovalPayload`), Request từ chối (`RejectRequest`).

---

## Tầng 3: Middlewares (Can thiệp vào Luồng Request)
*Hiểu cách hệ thống xử lý tính bảo mật, theo dõi và log dữ liệu trên bề mặt.*

6. **`backend/middleware/request_id.py`**
   - **Nhiệm vụ:** Inject Unique Request ID cho mỗi HTTP request, dễ dàng trace log lỗi sau này.
7. **`backend/middleware/logging_middleware.py`**
   - **Nhiệm vụ:** Log lại thời gian xử lý, method, URL của mọi request được gọi lên ứng dụng.
8. **`backend/middleware/auth.py`**
   - **Nhiệm vụ:** Hàm `verify_api_key` kiểm tra header Authorization.
9. **`backend/middleware/idempotency.py`**
   - **Nhiệm vụ:** Chống việc gọi API lặp nhiều lần bằng Idempotency-Key header.

---

## Tầng 4: Routes (API Endpoints)
*Giúp bạn biết ứng dụng phơi bày những chức năng nào cho Client.*

10. **`backend/routes/system.py`**
    - Các hàm `health_check`, `readiness_check` kiểm tra trạng thái sống của app.
11. **`backend/routes/auth.py`**
    - **Nhiệm vụ:** Giao tiếp OAuth 2.0. Có các router: `oauth_start`, `oauth_callback`, `oauth_refresh`, `oauth_revoke`.
12. **`backend/routes/hitl.py` & `backend/routes/audit.py`**
    - Xử lý các API thao tác duyệt/từ chối của con người (`approve`, `reject`, `list_approvals`) và lịch sử `audit`.
13. **`backend/routes/agent.py` & `backend/routes/tools.py`**
    - Endpoint tạo task cho Agent (`create_task`) và endpoint xem tool.
14. **`backend/routes/workspace/*.py`** (Gồm calendar, docs, drive, gmail, sheets)
    - Cung cấp API trực tiếp gọi vào các dịch vụ Google. Các hàm tiêu biểu: `create_document`, `gmail_send`, `search_files`, v.v.

---

## Tầng 5: Business Services (Logic Tầng API)
*Kết nối Route xuống những xử lý cốt lõi, DB.*

15. **`backend/services/token_store.py` & `backend/services/oauth_service.py`**
    - Giải quyết logic lưu trữ token được đánh mã hóa an toàn bằng Fernet, và thực hiện trao đổi, lấy token từ Google thông qua OAuth.
16. **`backend/services/policy_service.py`**
    - Chứa `PolicyService`: có hàm `evaluate`, `get_risk_level`, `requires_hitl` để xem xét thao tác nào rủi ro, cần Human-in-the-Loop hay chỉ yêu cầu scope nhỏ.
17. **`backend/services/agent_service.py` & `backend/services/tool_invoke_service.py`**
    - Cầu nối cho Route agent và Route tool, giúp điều phối, resume, và quản lý list các task đang xử lí.

---

## Tầng 6: Tích hợp Tools Adapter (LangChain/Google Workspace)
*Cách Agent kết nối vật lý bằng code vào Google Services thông qua LangChain Tools.*

18. **`tools/base.py` & `tools/registry.py`**
    - **Nhiệm vụ:** Nền tảng cấu trúc tool (`BaseTool`) và kho chứa (`ToolRegistry`) giúp load, validate đầu vào các tool từ manifest một cách linh hoạt.
19. **`tools/*/adapter.py`**
    - Trong thư mục `sheets`, `docs`, `calendar`, `gmail`, `drive`. Bạn sẽ thấy các Tool cụ thể được triển khai dựa trên BaseTool (ví dụ: `CalendarCreateEventTool`, `DriveUploadFileTool`), chứa các hàm `execute` và `mock_execute`.
20. **`tools/*/mock.py`**
    - Các class mock dữ liệu trong môi trường unit testing, không gọi real API.

---

## Tầng 7: Cốt lõi của hệ thống (Agent & HITL)
*Đây là trái tim AI của project.*

**👉 Đọc về quy trình Kế hoạch (Agent)**
21. **`agent/schemas.py` & `agent/prompts.py`**
    - Định nghĩa cấu trúc State của LangGraph (`AgentState`), cấu trúc Response và các Prompts cho Model.
22. **`agent/planner.py`**
    - Nơi chứa `Planner` và phương thức `create_plan`. Giao tiếp với LLM phân rã yêu cầu của user thành từng Step.
23. **`agent/risk_evaluator.py`**
    - Hàm `evaluate_batch`. Chấm điểm Risk (high, medium, low) vào từng Step để báo cáo bảo mật.
24. **`agent/executor.py`**
    - Trung tâm vận hành LangGraph của agent (`AgentExecutor`). Các hàm `build_langgraph`, `execute_plan`, `resume_after_approval` giúp chạy tuần tự qua các node của quy trình Agent.

**👉 Đọc về quy trình Duyệt (HITL)**
25. **`hitl/state_machine.py` & `hitl/queue.py`**
    - Quản lý trạng thái (`StateMachine`: `can_transition`) của yêu cầu duyệt (Pending -> Approved / Rejected) và lưu trữ queue vào db cục bộ.
26. **`hitl/policy_engine.py`**
    - Quyết định việc approval (tự động hay thủ công) ở cấp độ quy trình (`should_approve_batch`).
27. **`hitl/audit.py`**
    - Ghi log (Trail Log) toàn bộ lịch sử thao tác (`AuditLogger`).
28. **`hitl/workflow.py`**
    - Nhạc trưởng điều phối (`HITLWorkflow`). Tổng hợp Policy, State Machine, Audit và Executor vào thành một luồng Approval chuẩn chỉnh. Các hàm: `create_proposal`, `approve`, `reject`, `edit_approve`.

---

**Chúc bạn đọc code vui vẻ!** Thứ tự này đi từ ngoài vào trong, từ định nghĩa sơ cấp vào tới tư duy ra quyết định của mô hình AI.
