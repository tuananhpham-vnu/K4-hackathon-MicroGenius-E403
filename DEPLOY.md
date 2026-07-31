# Deploy lên Render

App phục vụ frontend và API trong cùng một Web Service. Render tự cấp HTTPS và
biến môi trường `PORT`; không cần deploy `frontend/` riêng.

## 1. Chuẩn bị repository

1. Đảm bảo repository GitHub là **private** vì thư mục `data/` có dữ liệu dùng
   cho hackathon.
2. Không commit `.env` hoặc API key. `.gitignore` đã loại các file này.
3. Commit và push `render.yaml`, `requirements-deploy.txt` cùng mã nguồn.

## 2. Tạo dịch vụ

1. Đăng nhập <https://dashboard.render.com/>.
2. Chọn **New > Blueprint**.
3. Kết nối GitHub và chọn repository này.
4. Render đọc `render.yaml` và tạo service `microgenius-admissions`.
5. Khi được hỏi secret `GEMINI_API_KEY`, nhập key trong dashboard, không ghi
   vào source code.
6. Chọn **Apply** và chờ health check `/api/health` thành công.

Website có URL dạng:

```text
https://microgenius-admissions.onrender.com
```

Kiểm tra:

```text
https://microgenius-admissions.onrender.com/api/health
```

## 3. Tính năng tùy chọn

Local retrieval hoạt động ngay từ các file đã commit trong `Tailieutubtc/` và
`data/`. Nếu dùng Firecrawl, bỏ comment `firecrawl-py` trong
`requirements-deploy.txt` rồi thêm `FIRECRAWL_API_KEY` trong Render Environment.

Nếu dùng Weaviate, bỏ comment `sentence-transformers` và `weaviate-client`, sau
đó thêm `WEAVIATE_URL`, `WEAVIATE_API_KEY`, `WEAVIATE_COLLECTION` và
`EMBEDDING_MODEL_NAME`. Các gói embedding khá nặng; không nên bật trên free
instance nếu chỉ cần demo local retrieval.

## 4. Lưu ý production

- Render Free có thể sleep khi không có traffic; lượt mở đầu tiên sẽ chậm.
- Filesystem là tạm thời. `/tmp/mas.jsonl` chỉ dùng để debug và sẽ mất khi
  restart/redeploy.
- `/api/logs` và `/api/audit` bị tắt mặc định vì có thể chứa câu hỏi và profile.
  Chỉ đặt `EXPOSE_TRACE_API=true` trong môi trường demo nội bộ.
- `GEMINI_API_KEY` chỉ là secret cấu hình. Agent hiện cần có adapter Gemini trong
  code thì mới thực sự gọi model; không nên tuyên bố đang dùng Gemini chỉ vì đã
  thêm key.
