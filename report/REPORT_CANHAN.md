# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lưu Mạnh Hùng
**Nhóm:** Hùng – Minh – Khánh (K4-L3A)
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1) nghĩa là hai vector embedding gần như "cùng hướng" trong không gian nhiều chiều, tức hai đoạn text mang ý nghĩa gần giống nhau về mặt ngữ nghĩa — kể cả khi chúng dùng từ vựng khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên cần đóng học phí trước ngày 15 hàng tháng."
- Câu B: "Hạn chót nộp tiền học cho sinh viên là ngày 15 mỗi tháng."
- Tại sao tương đồng: Hai câu dùng từ vựng khác nhau ("đóng học phí" vs "nộp tiền học", "trước ngày 15" vs "hạn chót... ngày 15") nhưng diễn đạt đúng một sự kiện và điều kiện, nên embedding sẽ đặt chúng gần nhau về ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên cần đóng học phí trước ngày 15 hàng tháng."
- Câu B: "Thư viện mở cửa từ 7 giờ sáng đến 10 giờ tối."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (tài chính học phí vs giờ hoạt động thư viện), không chia sẻ khái niệm hay ngữ cảnh chung nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo góc (hướng) giữa hai vector nên không bị ảnh hưởng bởi độ dài vector — hai đoạn text cùng ý nghĩa nhưng một câu dài, một câu ngắn (embedding có magnitude khác nhau) vẫn cho điểm tương đồng cao. Euclidean distance đo khoảng cách tuyệt đối nên bị "phạt" oan các vector có magnitude lớn dù hướng (ngữ nghĩa) giống hệt nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> Đáp án: **23 chunks**. Kiểm lại bằng `FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)` → `len(...) == 23` ✅ khớp công thức.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Tăng overlap lên 100 thì số chunk tăng từ 23 lên **25** (`ceil((10000−100)/(500−100)) = ceil(9900/400) = 25`, đã kiểm lại bằng code). Overlap lớn hơn giúp giảm rủi ro một câu/ý quan trọng bị cắt đúng ngay ranh giới hai chunk — thông tin nằm ở mép chunk sẽ xuất hiện trọn vẹn ở cả chunk trước lẫn chunk sau, đổi lại tốn thêm dung lượng lưu trữ và thời gian embedding vì có nhiều chunk hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+", text)` — lookbehind giữ lại dấu câu ở cuối câu trước thay vì để `re.split` nuốt mất nó (bẫy nêu trong bài lab). Sau khi tách câu, gom `max_sentences_per_chunk` câu liên tiếp thành một chunk bằng `" ".join(...)`. Edge case đã xử lý: text rỗng/toàn khoảng trắng trả về `[]`. Edge case biết nhưng chưa xử lý: viết tắt (`TS.`, `v.v.`) và số thập phân (`3.14`) sẽ bị regex hiểu nhầm là kết thúc câu, gây cắt sai.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` đệ quy theo danh sách separator `["\n\n", "\n", ". ", " ", ""]` theo hai chiều: (1) đệ quy xuống — nếu một phần sau khi tách bằng separator hiện tại vẫn dài hơn `chunk_size` thì gọi lại `_split` với separator kế tiếp; (2) gom lên — nối các phần nhỏ liền kề (kèm lại separator) cho tới sát `chunk_size` để tránh sinh chunk vụn vài ký tự. Ba base case: text rỗng → `[]`; phần hiện tại đã `<= chunk_size` → trả nguyên; hết separator (`remaining_separators == []`) → cắt cứng theo `chunk_size` để không bao giờ vượt kích thước.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Bỏ hẳn nhánh ChromaDB (chỉ set `self._use_chroma = False` cố định trong `__init__`) vì không test nào cần và `requirements.txt` không cài nó — tránh đúng cái bẫy "gán `True` trước khi có client" nêu trong bài lab. `_make_record` chuẩn hoá một `Document` thành record `{id, content, metadata (đã copy + có sẵn `doc_id`), embedding}` rồi append vào `self._store`. `search` gọi `_search_records`: embed câu query, tính dot product (`_dot`) với embedding từng record — vector đã chuẩn hoá nên dot product = cosine, sort giảm dần theo score, cắt `top_k`, và bỏ field `embedding` khỏi kết quả trả về.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** khi search: `search_with_filter` duyệt `self._store`, giữ lại record nào có `metadata` khớp mọi cặp key/value trong `metadata_filter`, rồi mới đưa tập ứng viên đó vào `_search_records` — nhờ vậy `top_k` slot không bao giờ bị tài liệu sai chiếm chỗ trước khi lọc. `delete_document` lọc bỏ mọi record có `metadata['doc_id'] == doc_id` bằng list comprehension, so sánh kích thước trước/sau để trả `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` lưu lại `store` và `llm_fn`. `answer` retrieve top-k chunk qua `store.search`, đánh số từng chunk `[1] [2] [3]` kèm `doc_id` làm nguồn rồi ghép thành một khối "Ngữ cảnh" duy nhất chèn vào prompt, kèm chỉ dẫn model phải trích dẫn số thứ tự khi dùng thông tin (để truy vết được — Source Traceability) và phải nói rõ "không tìm thấy" nếu ngữ cảnh không đủ thay vì bịa. Có 2 chốt chặn trước khi gọi `llm_fn`: store rỗng (`get_collection_size() == 0`) và không có kết quả retrieval nào — cả hai trả thẳng câu thông báo, không gọi LLM vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.07s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy `compute_similarity()` với embedding thật (`GeminiEmbedder`, `gemini-embedding-001`) — dự đoán được ghi **trước khi chạy**, không chỉnh sửa lại sau khi thấy kết quả.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Sinh viên cần hoàn thành tập huấn sử dụng thư viện trước khi được cấp quyền dùng thư viện." | "Trước khi được dùng thư viện, sinh viên phải hoàn tất khóa tập huấn thư viện." (paraphrase) | cao | 0.9531 | Đúng |
| 2 | "Mỗi lượt đặt phòng học nhóm tối đa 02 giờ." | "Phòng học nhóm có thể đặt trước qua website thư viện." (cùng chủ đề đặt phòng) | cao | 0.7811 | Đúng |
| 3 | "Gia hạn tài liệu thất bại khi tài liệu đang có người chờ mượn." | "Máy in đa chức năng phục vụ tại Print Station Tầng 1 và Tầng 4." (khác chủ đề, cùng domain thư viện) | thấp | 0.5928 | Đúng |
| 4 | "Giảng viên chưa có thẻ thư viện liên hệ Thư viện Truyền cảm hứng, Tòa nhà G." | "Sinh viên chưa có thẻ thư viện liên hệ Phòng CTHS-SV, Phòng A0003." (cùng cấu trúc câu, khác đối tượng/khác đáp án) | thấp | 0.7991 | **Sai** |
| 5 | "Độ tương tự cosine đo góc giữa hai vector embedding." | "Thư viện Tôn Đức Thắng mở cửa phục vụ sinh viên và giảng viên." (hai domain hoàn toàn khác nhau) | thấp | 0.5092 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 bất ngờ nhất: tôi dự đoán "thấp" vì nghĩ khác đối tượng (giảng viên vs sinh viên) và khác đáp án (khác văn phòng liên hệ) thì phải khác nghĩa, nhưng điểm thực tế lại khá cao (0.7991) — cao hơn cả cặp 2. Điều này cho thấy embedding chủ yếu bắt **cấu trúc và chủ đề bề mặt** ("[đối tượng] chưa có thẻ thư viện liên hệ [nơi]") chứ không phân biệt được chi tiết nào mới thực sự quan trọng để trả lời đúng câu hỏi. Đây chính xác là lý do câu hỏi Q4 trong benchmark **cần** `metadata_filter={"audience": "faculty"}`: nếu chỉ dựa vào độ tương tự ngữ nghĩa, hai tài liệu "thẻ sinh viên" và "thẻ giảng viên" gần nhau đến mức retrieval có thể lẫn lộn và trả lời sai đối tượng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> Chiến lược cá nhân: `HeadingChunker(chunk_size=400)`. Embedding backend: `gemini-embedding-001` (thật, không phải Mock). `llm_fn` dùng hàm demo echo giống `main.py` (không gọi model sinh văn bản thật) — cột "Câu trả lời của Agent" tóm tắt sự kiện chính mà một LLM thật sẽ trích ra từ đúng ngữ cảnh `[n]` được đưa vào prompt.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên cần làm gì để được cấp quyền lần đầu? | `# Hướng dẫn sử dụng thư viện cho tân sinh viên` (chỉ tiêu đề, gần như rỗng nội dung) | 0.844 | **Không** ở top-1; chunk đúng (đủ 3 bước) nằm ở **hạng 2**, score 0.837 | Dựa vào ngữ cảnh `[2]`: "Hoàn thành đủ 3 bước: tham gia tập huấn E-learning, ký cam kết, làm bài kiểm tra đạt điểm quy định" — agent vẫn trả lời đúng vì cả 3 chunk top-3 đều được đưa vào prompt |
| 2 | Đặt phòng học nhóm tối đa mấy giờ? | `### Thời gian sử dụng ... 02 giờ/lượt` | 0.861 | **Có**, đúng ngay top-1 | "02 giờ/lượt" (trích từ `[1]`) |
| 3 | Gia hạn thất bại khi nào? | `### Trường hợp không gia hạn được ... trễ hạn ... có người chờ mượn` | 0.885 | **Có**, đúng ngay top-1 | "Trễ hạn hoặc đang có người chờ mượn" (trích từ `[1]`) |
| 4 | Giảng viên chưa có TK CTT liên hệ đâu? | `### Tài khoản Cổng thông tin thư viện ... Liên hệ: Thư viện Truyền cảm hứng, Tòa nhà G ...` | 0.846 | **Có**, đúng ngay top-1 (nhờ `metadata_filter={"audience":"faculty"}`) | "Thư viện Truyền cảm hứng, Tòa nhà G, ĐT (028) 37 755 057, email thuvien@tdtu.edu.vn" (trích từ `[1]`) |
| 5 | Sức chứa phòng chức năng? | `### Số lượng người ... ít nhất 50% sức chứa ... không vượt quá sức chứa` | 0.834 | **Có**, đúng ngay top-1 | "Ít nhất 50% và không vượt quá sức chứa của phòng" (trích từ `[1]`) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** (4/5 câu đúng ngay top-1; câu 1 đúng ở top-2 vì chunk tiêu đề gần rỗng của `tan-sinh-vien.md` vô tình có điểm cao hơn chunk nội dung thật — xem phân tích lỗi tương tự trong `REPORT_NHOM.md` mục 2 & 4).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So kết quả của mình (`HeadingChunker`, 9/10, mất điểm ở câu 1) với kết quả thật của Minh (`RecursiveChunker(chunk_size=300)`, 9/10, mất điểm ở câu 3 — xem `ket_qua_benchmark_minhnc.txt`), điều bất ngờ nhất là hai chiến lược hoàn toàn khác nhau nhưng **cùng đạt điểm bằng nhau và cùng chỉ sai đúng một câu** — chỉ khác câu nào. Cả hai lỗi hoá ra cùng một nguyên nhân gốc: chunker cắt đúng vào ranh giới hình thức (dòng trống `\n\n` với Minh, dòng heading đứng riêng với mình) ngay trước đoạn chứa câu trả lời thật, dù về ngữ nghĩa hai phần đó thuộc về nhau.
>
> Bài học lớn hơn lại đến từ Khánh: `ket_qua_benchmark_khanhdq.txt` của bạn chỉ đạt 2/10 dù dùng `FixedSizeChunker(400,50)` — một chiến lược hoàn toàn ổn — vì máy bạn không có API key nên tự động rơi về `MockEmbedder`. Khi tôi chạy lại đúng chiến lược đó bằng Gemini, điểm nhảy lên 9/10. Bài học: **không có chiến lược nào "luôn thắng" một cách tuyệt đối**, và quan trọng hơn cả việc chọn chiến lược là phải (1) tự kiểm tra top-3 bằng mắt cho từng câu, và (2) luôn xác nhận dòng `Embedding backend: ...` trước khi tin vào điểm số — một con số thấp có thể tố cáo môi trường chạy chứ không phải chất lượng chunking.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
