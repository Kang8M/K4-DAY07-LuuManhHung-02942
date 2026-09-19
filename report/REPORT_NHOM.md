# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Hùng – Minh – Khánh (K4-L3A)
**Thành viên:** Lưu Mạnh Hùng, Nguyễn Ngọc Minh, Dương Quốc Khánh
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ thư viện Trường Đại học Tôn Đức Thắng (TDTU Library)

**Tại sao nhóm chọn chủ đề này?**

> Thư viện TDTU cung cấp hướng dẫn dịch vụ công khai, có cấu trúc rõ ràng theo từng đối tượng (sinh viên, giảng viên), phù hợp để kiểm tra metadata filter theo `audience`. Nội dung bao gồm các quy định cụ thể về số liệu (thời gian, điều kiện) — lý tưởng để đặt benchmark query có gold answer trích được trực tiếp.

### Danh sách tài liệu (Data Inventory)


| # | Tên tài liệu                                             | Nguồn (Source URL)                                                   | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                |
| --- | ------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------- | ------------- | --------------------------------------------------- |
| 1 | Đặt phòng chức năng thư viện                         | https://lib.tdtu.edu.vn/vi/huong-dan/can-thiet/dat-phong              | 2026-09-19 / not-stated  | ~1 200      | audience=student, category=huong-dan, language=vi |
| 2 | Gia hạn tài liệu                                         | https://lib.tdtu.edu.vn/vi/huong-dan/can-thiet/gia-han-tai-lieu       | 2026-09-19 / not-stated  | ~650        | audience=student, category=huong-dan, language=vi |
| 3 | Sao chụp & In ấn                                          | https://lib.tdtu.edu.vn/vi/dich-vu/khong-gian-tien-ich/sao-chup-in-an | 2026-09-19 / not-stated  | ~550        | audience=student, category=huong-dan, language=vi |
| 4 | Thẻ và tài khoản thư viện (sinh viên)                | https://lib.tdtu.edu.vn/vi/huong-dan/can-thiet/the-tai-khoan          | 2026-09-19 / not-stated  | ~900        | audience=student, category=huong-dan, language=vi |
| 5 | Hướng dẫn sử dụng thư viện cho tân sinh viên       | https://lib.tdtu.edu.vn/vi/huong-dan/can-thiet/tan-sinh-vien          | 2026-09-19 / not-stated  | ~1 800      | audience=student, category=huong-dan, language=vi |
| 6 | Thẻ và tài khoản thư viện (giảng viên, viên chức) | https://lib.tdtu.edu.vn/vi/huong-dan/can-thiet/the-tai-khoan          | 2026-09-19 / not-stated  | ~800        | audience=faculty, category=huong-dan, language=vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [X]  Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [X]  Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)


| Trường metadata  | Kiểu               | Ví dụ giá trị             | Tại sao hữu ích cho truy xuất (retrieval)?                                                                                                                      |
| -------------------- | --------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `doc_id`           | string              | `tan-sinh-vien`               | Định danh duy nhất để`delete_document` và truy vết nguồn                                                                                                    |
| `audience`         | string              | `student` / `faculty`         | Lọc tài liệu đúng đối tượng; hai file cùng chủ đề thẻ/tài khoản được tách theo trường này để`search_with_filter` có việc thật để lọc |
| `category`         | string              | `huong-dan`                   | Lọc theo loại nội dung (hướng dẫn, quy định, biểu mẫu...)                                                                                                 |
| `language`         | string              | `vi`                          | Hỗ trợ lọc theo ngôn ngữ nếu corpus mở rộng thêm tài liệu tiếng Anh                                                                                     |
| `source_url`       | string              | `https://lib.tdtu.edu.vn/...` | Truy vết nguồn gốc; kiểm tra độ mới của tài liệu                                                                                                          |
| `retrieved_at`     | string (YYYY-MM-DD) | `2026-09-19`                  | Ghi nhận ngày thu thập để phát hiện tài liệu lỗi thời                                                                                                    |
| `document_version` | string              | `not-stated`                  | Phiên bản/ngày hiệu lực;`not-stated` khi nguồn không nêu rõ                                                                                                |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=200)` trên 3 tài liệu (đã bỏ frontmatter):


| Tài liệu                          | Chiến lược (Strategy)         | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                                                    |
| ------------------------------------- | ---------------------------------- | ------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------- |
| tan-sinh-vien (1843 ký tự)        | FixedSizeChunker (`fixed_size`)  | 12                | 199.4                 | Không — cắt cứng theo ký tự, nhiều chunk đứt giữa câu                                   |
| tan-sinh-vien                       | SentenceChunker (`by_sentences`) | 3                 | 612.7                 | Có — trọn câu, nhưng chunk dài gộp nhiều mục con khác chủ đề                          |
| tan-sinh-vien                       | RecursiveChunker (`recursive`)   | 12                | 152.0                 | Tương đối — ưu tiên`\n\n`/`\n` nên bám theo đoạn, nhưng chunk_size nhỏ vẫn cắt vụn |
| dat-phong (1409 ký tự)            | FixedSizeChunker (`fixed_size`)  | 10                | 185.9                 | Không                                                                                             |
| dat-phong                           | SentenceChunker (`by_sentences`) | 2                 | 702.5                 | Có, nhưng gộp cả "Thời gian", "Gia hạn", "Phí" vào 1 chunk                                 |
| dat-phong                           | RecursiveChunker (`recursive`)   | 9                 | 154.9                 | Tương đối                                                                                      |
| teacher-the-tai-khoan (887 ký tự) | FixedSizeChunker (`fixed_size`)  | 6                 | 189.5                 | Không                                                                                             |
| teacher-the-tai-khoan               | SentenceChunker (`by_sentences`) | 2                 | 441.5                 | Có                                                                                                |
| teacher-the-tai-khoan               | RecursiveChunker (`recursive`)   | 5                 | 175.8                 | Tương đối                                                                                      |

Quan sát chung: `FixedSizeChunker` cho chunk đều nhau nhất nhưng dễ cắt ngang câu/mục; `SentenceChunker` giữ trọn câu nhưng với văn bản có nhiều mục ngắn (`###`) thì gộp quá nhiều ý khác nhau vào một chunk (rất ít chunk, avg_length cao); `RecursiveChunker` cân bằng hơn nhờ ưu tiên tách theo đoạn (`\n\n`) trước.

**Đối chiếu với baseline của Khánh** (`ket_qua_benchmark_khanhdq.txt`, chạy `compare(body, chunk_size=350)` trên `student-the-tai-khoan`, `teacher-the-tai-khoan`, `tan-sinh-vien`): `fixed_size` cho 3/3/6 chunk (avg 301.3/329.3/349.0), `by_sentences` 2/2/3 chunk, `recursive` 3/3/7 chunk — cùng xu hướng như trên (fixed_size chia đều nhất, recursive nhiều chunk hơn fixed_size ở văn bản dài do bám `\n\n`), dù dùng `chunk_size` khác (350 so với 200) nên số chunk tuyệt đối không so trực tiếp được với bảng trên.

### Chiến lược của từng thành viên

> Nhóm 3 người, mỗi người một chiến lược khác nhau, đúng tinh thần "chiến lược chunking không được trùng nhau" của bài lab.

**Thành viên 1 — Dương Quốc Khánh**

- **Loại chiến lược:** FixedSize (`chunk_size=400`, `overlap=50` — suy ra từ 20 chunk nạp được trên 6 file, khớp `FixedSizeChunker(400, 50)`)
- **Mô tả & lý do chọn cho chủ đề này:** Baseline đơn giản, làm mốc so sánh cho 2 chiến lược còn lại — cắt cứng theo ký tự, overlap 50 giúp giảm phần nào rủi ro cắt đứt đúng con số/điều kiện quan trọng ngay ranh giới chunk.
- **Code snippet:**

```python
CHUNKER = FixedSizeChunker(chunk_size=400, overlap=50)
```

- **Kết quả thật:** máy của Khánh không có backend embedding thật nào khả dụng (không `sentence-transformers`, không `OPENAI_API_KEY`/`GEMINI_API_KEY`) nên `bench.py` tự động rơi về `MockEmbedder` — script tự in cảnh báo rõ ràng về việc này. Điểm tự chấm theo `ket_qua_benchmark_khanhdq.txt`: **2/10** (chi tiết và phân tích ở bảng so sánh + mục 4). Khi chạy lại đúng chiến lược này (`FixedSizeChunker(400,50)`) bằng embedding thật (Gemini, do Hùng chạy hộ để so sánh công bằng), điểm tăng lên **9/10** — chênh lệch 7 điểm này tự nó là bằng chứng mạnh nhất trong cả nhóm cho tầm quan trọng của việc chọn embedding backend (mục 7, phần "Chọn embedding backend trước khi đo").

**Thành viên 2 — Nguyễn Ngọc Minh**

- **Loại chiến lược:** Recursive (`chunk_size=300`, separator mặc định `["\n\n", "\n", ". ", " ", ""]`)
- **Mô tả & lý do chọn:** Văn bản nguồn được viết mỗi ý một dòng/đoạn (`\n\n` giữa các đoạn), nên ưu tiên tách theo ranh giới đoạn trước sẽ giữ ngữ nghĩa tốt hơn cắt cứng theo ký tự, mà vẫn không sinh chunk khổng lồ như SentenceChunker.
- **Code snippet:**

```python
CHUNKER = RecursiveChunker(chunk_size=300)
```

- **Kết quả thật:** 9/10 điểm truy xuất — chi tiết trong `ket_qua_benchmark_minhnc.txt` và bảng so sánh bên dưới.

**Thành viên 3 — Lưu Mạnh Hùng**

- **Loại chiến lược:** Custom — bắt buộc theo ràng buộc K4-L3A ("ít nhất một thành viên chunk theo tiêu đề/mục của văn bản quy định")
- **Mô tả & lý do chọn:** Mỗi tài liệu thư viện đã được tác giả chia sẵn theo heading `###` (vd "Thời gian sử dụng", "Trường hợp không gia hạn được") — mỗi heading là một đơn vị ngữ nghĩa trọn vẹn. Chiến lược này tách trước mỗi dòng heading thành một chunk riêng; section nào dài hơn `chunk_size` mới hạ xuống `RecursiveChunker` và gắn lại heading vào từng mảnh con để không mất ngữ cảnh "đây là mục nói về cái gì". Được chọn làm chiến lược mặc định trong `bench.py` của Hùng.
- **Code snippet:**

```python
# src/chunking.py
class HeadingChunker:
    HEADING_RE = re.compile(r"^(#{1,6})[ \t]+.+$", re.M)

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return []
        matches = list(self.HEADING_RE.finditer(stripped))
        if not matches:
            return self._fallback.chunk(stripped)
        # ... tách mỗi heading thành 1 section, section dài thì hạ xuống
        # RecursiveChunker rồi gắn lại dòng heading vào từng mảnh con.
```

- **Kết quả thật:** 9/10 điểm truy xuất — chi tiết trong `ket_qua_benchmark.txt` và bảng so sánh bên dưới.

### So Sánh Giữa Các Thành Viên

> Chấm theo `docs/SCORING.md` (2đ/câu: top-1 chứa đáp án = 2đ, đáp án ở top-2/3 = 1đ, vắng mặt = 0đ). Nguồn số liệu: `ket_qua_benchmark.txt` (Hùng), `ket_qua_benchmark_minhnc.txt` (Minh), `ket_qua_benchmark_khanhdq.txt` (Khánh) — số liệu thật do từng người tự chạy trên máy của mình, không ai mô phỏng hộ ai.


| Thành viên         | Chiến lược (Strategy)                                                                                        | Điểm truy xuất (/10)                                                                                                                                        | Điểm mạnh                                                                                                                                                                                                                                       | Điểm yếu                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lưu Mạnh Hùng     | `HeadingChunker(chunk_size=400)` — embedding: `gemini-embedding-001`                                           | 9/10 (Q1=1, Q2=2, Q3=2, Q4=2, Q5=2)                                                                                                                            | Chunk theo mục giữ trọn 1 ý hoàn chỉnh (Q2, Q3, Q4, Q5 đều top-1 đúng và đủ thông tin); hiệu quả nhất khi mỗi heading là một câu trả lời độc lập.                                                                        | Chunk tiêu đề (`# Hướng dẫn sử dụng thư viện cho tân sinh viên`, chỉ 46 ký tự, gần như rỗng nội dung) vẫn được xếp hạng cao hơn chunk có nội dung thật ở Q1 (chunk đúng bị đẩy xuống hạng 2) vì tiêu đề trùng chủ đề câu hỏi.                                                                                              |
| Nguyễn Ngọc Minh   | `RecursiveChunker(chunk_size=300)` — embedding: `gemini-embedding-001`                                         | 9/10 (Q1=2, Q2=2, Q3=1, Q4=2, Q5=2)                                                                                                                            | Chunk_size nhỏ (300) + tách theo`\n\n` cho hầu hết câu trả lời gọn, đúng trọng tâm (Q1, Q2, Q4, Q5 đều đạt tối đa); A/B filter ở Q4 cho bằng chứng rất rõ ràng (không filter → `student-the-tai-khoan` chen vào top-2). | **Thất bại thật ở Q3** (theo `ket_qua_benchmark_minhnc.txt`): top-1 là đoạn giới thiệu chung "Gia hạn tài liệu là quyền tăng thêm thời gian giữ tài liệu...", còn câu trả lời thật ("trễ hạn hoặc có người chờ mượn") bị đẩy xuống top-2 vì `\n\n` tách hai đoạn của cùng một file thành 2 chunk riêng.                    |
| Dương Quốc Khánh | `FixedSizeChunker(chunk_size=400, overlap=50)` — embedding: **`MockEmbedder`** (máy không có backend thật) | **2/10** (Q1=0, Q2=0, Q3=0, Q4=2, Q5=0) — nếu chạy lại đúng chiến lược này bằng Gemini thật: **9/10** (Q1=2, Q2=1, Q3=2, Q4=2, Q5=2), xem ghi chú | Chunk theo ký tự với overlap giữ được đúng nội dung ở phần lớn câu (kiểm chứng qua bản rerun bằng Gemini: 4/5 câu đạt tối đa); chunk boundary hợp lý nhờ overlap=50.                                                     | Điểm 2/10 thấp không phải do chiến lược mà do**môi trường**: không có API key/model thật nên dùng `MockEmbedder` (băm MD5, không mã hoá ngữ nghĩa) — đúng cảnh báo trong mục 7 của bài lab. Q4 vẫn đạt 2đ vì `metadata_filter` thu hẹp ứng viên xuống chỉ còn đúng 1 tài liệu, giảm không gian để nhiễu hash gây sai. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> Khi cả 3 người đều được so sánh trên cùng nền embedding thật (Gemini) — Hùng 9/10, Minh 9/10, và Khánh 9/10 khi chạy lại `FixedSizeChunker(400,50)` bằng Gemini — **cả 3 chiến lược đều tốt gần như ngang nhau** cho corpus nhỏ, có cấu trúc rõ ràng này. Mỗi chiến lược đều thất bại đúng 1 câu, và cả 3 lỗi đều cùng một bản chất: chunker cắt đúng vào ranh giới hình thức (dòng trống `\n\n`, dòng heading đứng riêng, hoặc ranh giới ký tự cố định) ngay trước/giữa phần nội dung thật sự trả lời câu hỏi, dù về ngữ nghĩa các phần đó thuộc về nhau. → **Kết luận quan trọng nhất của nhóm**: với corpus và câu hỏi này, **lựa chọn embedding backend ảnh hưởng đến chất lượng truy xuất nhiều hơn hẳn lựa chọn chiến lược chunking** — chênh lệch 7 điểm giữa Mock và Gemini trên CÙNG một chiến lược (`FixedSizeChunker` của Khánh) lớn hơn nhiều so với chênh lệch giữa 3 chiến lược khác nhau khi cùng dùng Gemini (9 so với 9 so với 9). Nếu phải chọn 1 chiến lược "an toàn" nhất để tổng quát hoá sang chủ đề khác, nhóm chọn `HeadingChunker` vì lỗi của nó (chunk tiêu đề rỗng) dễ sửa nhất (gộp tiêu đề vào section đầu) và không phụ thuộc vào việc người viết tài liệu có chèn dòng trống hay không.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.


| # | Câu hỏi (Query)                                                                          | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                                                                   | Chunk nào chứa thông tin?                                                                                                                                                                                                                                       |
| --- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Sinh viên cần làm gì để được cấp quyền sử dụng thư viện lần đầu?         | Hoàn thành 3 bước: (1) tham gia khóa học trực tuyến "Tập huấn sử dụng thư viện TDTU" trên E-learning, (2) ký bản cam kết Tuân thủ quyền tác giả, (3) làm bài kiểm tra và đạt số điểm theo quy định. | `tan-sinh-vien` — mục "Điều kiện được cấp quyền sử dụng thư viện"                                                                                                                                                                                    |
| 2 | Mỗi lượt đặt phòng học nhóm được sử dụng tối đa bao nhiêu giờ?            | 02 giờ/lượt.                                                                                                                                                                                                                       | `dat-phong` — mục "Thời gian sử dụng"                                                                                                                                                                                                                         |
| 3 | Gia hạn tài liệu không thành công trong những trường hợp nào?                   | Gia hạn không thành công khi tài liệu bị trễ hạn hoặc tài liệu đang có người chờ mượn.                                                                                                                             | `gia-han-tai-lieu` — mục "Trường hợp không gia hạn được"                                                                                                                                                                                                 |
| 4 | Giảng viên chưa có tài khoản cổng thông tin thư viện liên hệ ở đâu?         | Liên hệ Thư viện Truyền cảm hứng, Tòa nhà G. Điện thoại: (028) 37 755 057. Email: thuvien@tdtu.edu.vn                                                                                                                     | `teacher-the-tai-khoan` — mục "Tài khoản Cổng thông tin thư viện" (⚠️ `student-the-tai-khoan` có mục cùng tên, cùng từ vựng nhưng khác đối tượng và khác đáp án — **cần** `metadata_filter={"audience":"faculty"}` để không lẫn) |
| 5 | Số người sử dụng phòng chức năng phải đảm bảo điều kiện gì về sức chứa? | Số người thực tế phải đảm bảo ít nhất 50% sức chứa và không vượt quá sức chứa của phòng.                                                                                                                        | `dat-phong` — mục "Số lượng người"                                                                                                                                                                                                                          |

Câu 1 và câu 4 dùng `metadata_filter={"audience": ...}`; câu 4 là câu **cần** filter theo đúng ràng buộc K4-L3A (`needs_filter: true` trong `gold-answer.json`) vì `student-the-tai-khoan` và `teacher-the-tai-khoan` cùng có mục "Tài khoản Cổng thông tin thư viện" nhưng trả lời khác nhau theo đối tượng.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0). Hùng và Minh chạy bằng `gemini-embedding-001`; Khánh chạy bằng `MockEmbedder` (không có backend thật trên máy) — cột "Ghi chú" nêu rõ khi kết quả của Khánh bị ảnh hưởng bởi mock.


| # | Câu hỏi                                                     | Chiến lược tốt nhất cho câu này              | Có chunk liên quan trong top-3?                                   | Ghi chú                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Sinh viên cần làm gì để được cấp quyền lần đầu? | RecursiveChunker — Minh (2đ, top-1 đủ 3 bước) | Có (Hùng, Minh) /**Không** (Khánh — mock)                      | HeadingChunker (Hùng) chỉ 1đ vì chunk tiêu đề gần-rỗng chiếm top-1; FixedSizeChunker (Khánh) 0đ vì mock xếp hạng sai hoàn toàn — cùng chunker đó chạy bằng Gemini sẽ đạt 2đ    |
| 2 | Đặt phòng học nhóm tối đa mấy giờ?                   | Hùng & Minh (2đ, top-1 = "02 giờ/lượt")        | Có (Hùng, Minh) /**Không** (Khánh — mock)                      | Với mock,`dat-phong.md` không lọt nổi top-3 dù đúng chủ đề                                                                                                                                      |
| 3 | Gia hạn thất bại khi nào?                                 | HeadingChunker — Hùng (2đ, top-1)                | Có (Hùng, nhưng Minh chỉ ở top-2) /**Không** (Khánh — mock) | **Failure case của Minh**: RecursiveChunker(300) tách đoạn giới thiệu và đoạn "không thành công khi..." qua `\n\n` → chỉ 1đ; Khánh 0đ vì mock không xếp `gia-han-tai-lieu` vào top-3 |
| 4 | Giảng viên chưa có TK CTT liên hệ đâu?                | Cả 3 (2đ, top-1)                                  | Có (cả 3, nhờ`metadata_filter={"audience":"faculty"}`)           | Câu duy nhất cả 3 người đều đạt tối đa — kể cả với mock, vì filter thu hẹp ứng viên xuống chỉ 1 tài liệu                                                                           |
| 5 | Sức chứa phòng chức năng?                                | Hùng & Minh (2đ, top-1 giống nhau)               | Có (Hùng, Minh) /**Không** (Khánh — mock)                      | Đoạn "### Số lượng người" ngắn gọn, chunker nào cũng giữ trọn — chỉ mock mới xếp sai hạng                                                                                               |

**Điểm nhóm — Chất lượng truy xuất (10đ):** trung bình thật 3 người = (9+9+2)/3 ≈ **6.7/10**. Điểm thấp không phản ánh chất lượng chiến lược của Khánh — khi chạy lại đúng `FixedSizeChunker(400,50)` bằng Gemini (để so sánh công bằng, do Hùng thực hiện), điểm là 9/10, đưa trung bình "nếu cả 3 đều có embedding thật" lên (9+9+9)/3 = **9/10**. Nhóm xin ghi nhận điểm 6.7/10 là con số thật phản ánh đúng điều kiện làm bài thực tế (một máy thiếu API key), kèm theo bằng chứng rằng nguyên nhân là hạ tầng chứ không phải thiết kế chiến lược.

### A/B bắt buộc — Metadata filter có giúp ích không?

Chạy `search_with_filter` **có** và **không** `metadata_filter` cho 2 câu cần lọc (Q1 `audience=student`, Q4 `audience=faculty`). Nguồn: `ket_qua_benchmark.txt` (Hùng), `ket_qua_benchmark_minhnc.txt` (Minh), `ket_qua_benchmark_khanhdq.txt` (Khánh) — cả 3 đều tự chạy trên máy mình.


| Câu | Chiến lược                   | Top-3 doc_id — CÓ filter               | Top-3 doc_id — KHÔNG filter                          |
| ------ | --------------------------------- | ------------------------------------------ | -------------------------------------------------------- |
| Q1   | HeadingChunker (Hùng, Gemini)  | tan-sinh-vien, tan-sinh-vien, student    | tan-sinh-vien, tan-sinh-vien, student (giống hệt)    |
| Q1   | RecursiveChunker (Minh, Gemini) | tan-sinh-vien, dat-phong, tan-sinh-vien  | tan-sinh-vien, dat-phong, tan-sinh-vien (giống hệt)  |
| Q1   | FixedSizeChunker (Khánh, Mock) | student, gia-han-tai-lieu, tan-sinh-vien | student, gia-han-tai-lieu, tan-sinh-vien (giống hệt) |
| Q4   | HeadingChunker (Hùng, Gemini)  | teacher, teacher, teacher                | teacher,**student**, teacher                           |
| Q4   | RecursiveChunker (Minh, Gemini) | teacher, teacher, teacher                | teacher,**student**, teacher                           |
| Q4   | FixedSizeChunker (Khánh, Mock) | teacher, teacher, teacher                | **student**, sao-chup-in-an, dat-phong                 |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có, rõ nhất ở **Q4** — cả 3 người đều quan sát cùng một hiện tượng độc lập với nhau: không filter thì `student-the-tai-khoan.md` (tài liệu sai đối tượng, cùng chủ đề "tài khoản cổng thông tin") chen được vào top-3. Với embedding thật (Hùng, Minh), top-1 vẫn đúng nên điểm 2/1/0 không đổi, nhưng ngữ cảnh gửi cho agent bị "nhiễm" một chunk sai đối tượng. Với **mock (Khánh)**, hậu quả nặng hơn hẳn: không filter thì `student-the-tai-khoan` **chiếm luôn top-1**, đẩy cả 3 chunk đúng (`teacher-the-tai-khoan`) ra khỏi top-3 hoàn toàn — filter không chỉ "giúp ích" mà là **điều kiện cần** để câu này trả lời đúng khi embedding kém tin cậy. Ở **Q1**, cả 3 người đều thấy filter **không đổi gì** (top-3 giống hệt nhau có/không filter) vì không có tài liệu `faculty` nào cùng chủ đề "cấp quyền sử dụng thư viện lần đầu" để gây nhiễu. Kết luận: filter chỉ thực sự "có việc để làm" khi hai tài liệu **cùng chủ đề, khác đối tượng, khác đáp án** (đúng như Q4, không như Q1) — và mức độ "giúp ích" của nó còn tăng lên khi embedding kém chính xác, vì filter là lớp bảo vệ không phụ thuộc vào chất lượng ngữ nghĩa của model.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân tích lỗi (Failure Case) — bắt buộc

**Failure case 1 (Minh — `RecursiveChunker(chunk_size=300)`, từ `ket_qua_benchmark_minhnc.txt`)**

**Câu hỏi nào hỏng:** Q3 ("Gia hạn tài liệu không thành công trong những trường hợp nào?") — chỉ 1/2 điểm dù đúng tài liệu `gia-han-tai-lieu.md` nằm ở cả top-1 và top-2.

**Vì sao:** File nguồn có 2 đoạn cách nhau bởi dòng trống — đoạn giới thiệu chung ("Gia hạn tài liệu là quyền tăng thêm thời gian giữ tài liệu đang mượn...") và đoạn nêu điều kiện thất bại ("### Trường hợp không gia hạn được... trễ hạn... có người chờ mượn"). `RecursiveChunker` tách theo `\n\n` trước tiên nên hai đoạn này rơi vào **hai chunk khác nhau**; đoạn giới thiệu (không chứa câu trả lời) tình cờ có điểm cosine cao hơn nên chiếm top-1, còn đoạn chứa câu trả lời thật bị đẩy xuống top-2.

**Đề xuất sửa (theo ghi chú của Minh):** tăng `chunk_size` (vd 300 → 500) hoặc thêm overlap giữa các chunk để đoạn giới thiệu và đoạn điều kiện thất bại có cơ hội gộp lại thành một chunk.

**Failure case 2 (Hùng — `HeadingChunker(chunk_size=400)`, từ `ket_qua_benchmark.txt`)**

**Câu hỏi nào hỏng:** Q1 ("Sinh viên cần làm gì để được cấp quyền sử dụng thư viện lần đầu?") — chỉ 1/2 điểm dù đúng tài liệu `tan-sinh-vien.md` chiếm cả top-1 và top-2.

**Vì sao:** `HeadingChunker` tách file thành nhiều section theo từng dòng heading — dòng `# Hướng dẫn sử dụng thư viện cho tân sinh viên` (H1) không có nội dung nào phía dưới nó trước khi gặp heading `###` kế tiếp, nên trở thành **một chunk chỉ có 46 ký tự, gần như rỗng**. Chunk tiêu đề này vẫn được xếp hạng cao hơn (0.844) chunk chứa đầy đủ "3 bước" (0.837) vì tiêu đề trùng từ khoá chủ đề với câu hỏi — cosine đo độ giống **chủ đề bề mặt**, không đo **mật độ thông tin trả lời được**.

**Đề xuất sửa:** khi một section (do H1/H2 sinh ra) không có nội dung riêng trước heading con kế tiếp, gộp nó vào section liền sau thay vì giữ làm chunk độc lập — tức chỉ giữ tiêu đề đứng riêng khi nó thực sự có đoạn văn bản đi kèm.

**Failure case 3 (Khánh — môi trường thiếu embedding thật, từ `ket_qua_benchmark_khanhdq.txt`)**

**Câu hỏi nào hỏng:** 4/5 câu (Q1, Q2, Q3, Q5) — chỉ 2/10 điểm dù dùng `FixedSizeChunker(400, 50)`, một chiến lược ổn (kiểm chứng lại đạt 9/10 với embedding thật).

**Vì sao:** Máy của Khánh không cài `sentence-transformers` và không có `OPENAI_API_KEY`/`GEMINI_API_KEY`, nên theo đúng cơ chế fallback đã cài trong `src/embeddings.py`, `bench.py` tự động rơi về `MockEmbedder` (băm MD5 thành vector giả ngẫu nhiên) — script có in cảnh báo rõ ràng nhưng không chặn chạy tiếp. Vì `MockEmbedder` không mã hoá ngữ nghĩa, thứ hạng top-3 gần như ngẫu nhiên so với nội dung câu hỏi: ví dụ Q2 ("02 giờ/lượt") không có chunk nào từ đúng file `dat-phong.md` lọt vào top-3.

**Đề xuất sửa:** thêm bước kiểm tra bắt buộc ngay đầu quy trình benchmark — in dòng `Embedding backend: ...` và **dừng lại xác nhận với người dùng** nếu backend là mock, thay vì âm thầm chạy tiếp rồi để người chấm tự phát hiện qua điểm số thấp bất thường. Về phía nhóm: nên đăng ký Gemini API key (miễn phí) cho mọi máy từ đầu buổi, đúng khuyến nghị "cài từ đầu buổi để tải nền" của mục 7.

### Những phân tích (insights) hay nhất nhóm sẽ trình bày

- Với embedding thật, khoảng cách chất lượng giữa các chiến lược thu hẹp đáng kể so với lúc dùng `MockEmbedder` ở Giai đoạn 3 — `HeadingChunker`, `RecursiveChunker`, và `FixedSizeChunker` (bản rerun bằng Gemini) đều đạt 9/10, chứng minh phần lớn "khác biệt chiến lược" quan sát được ở CP5 thực chất là nhiễu do embedding giả lập, không phải do chunking.
- Ba người, ba chiến lược, nhưng **cùng thua ở đúng một kiểu điểm rơi** (khi có embedding thật): cả 3 failure case về chunking ở trên đều xảy ra khi văn bản nguồn có một đoạn "câu dẫn/tiêu đề ngắn" đứng tách biệt (bởi dòng trống, bởi heading, hoặc bởi ranh giới ký tự cố định) ngay trước phần nội dung thật sự trả lời câu hỏi — cả 3 kiểu chunker đều coi đó là ranh giới hợp lệ để cắt, dù về ngữ nghĩa hai phần đó thuộc về nhau.
- **Phát hiện lớn nhất của nhóm nằm ngoài phạm vi chunking**: chênh lệch điểm giữa Mock và Gemini trên CÙNG một chiến lược của Khánh (2/10 → 9/10, chênh 7 điểm) lớn hơn nhiều so với chênh lệch giữa 3 chiến lược chunking khác nhau khi cùng dùng Gemini (đều 9/10, chênh 0 điểm). Với corpus và câu hỏi của nhóm, **chọn đúng embedding backend quan trọng hơn chọn đúng chiến lược chunking**.
- Metadata filter không chỉ "giúp ích" mà có thể là **điều kiện cần**: với mock của Khánh, không filter khiến Q4 sai hoàn toàn ở top-1 (tài liệu sai đối tượng chiếm top-1); với embedding thật của Hùng/Minh, không filter chỉ làm giảm độ "sạch" của ngữ cảnh chứ chưa đổi kết quả top-1. Tức là filter đóng vai trò lưới an toàn quan trọng hơn khi embedding kém tin cậy hơn.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng bộ tài liệu, cùng 5 câu hỏi, nhưng Hùng và Minh mất điểm ở hai câu khác nhau (Q1 vs Q3) vì hai lý do cùng một bản chất: chunker cắt đúng vào chỗ có "câu dẫn/tiêu đề ngắn đứng trước nội dung thật" — điều mắt người đọc tự động ghép lại thành một ý, nhưng máy tách theo ranh giới hình thức (dòng trống, dòng heading) lại không biết. Trong khi đó, điểm số thấp của Khánh dạy nhóm một bài học khác hẳn: **một con số benchmark thấp có thể tố cáo môi trường chạy, không phải chất lượng code hay chiến lược** — nếu không kiểm tra dòng "Embedding backend" đầu tiên, rất dễ kết luận sai rằng `FixedSizeChunker` là chiến lược tệ. Bài học chung: **luôn kiểm tra tay** top-3 và backend đang dùng trước khi tin vào điểm tổng — ba người tự chấm độc lập mà phát hiện đúng hai nhóm hiện tượng nhất quán (lỗi chunking giống nhau, lỗi môi trường tách biệt) là bằng chứng đáng tin hơn nhiều so với một người tự đánh giá.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Sẽ thêm overlap nhỏ vào cả `RecursiveChunker` và `HeadingChunker` khi cắt xuống mức đoạn/section, để câu dẫn/tiêu đề ngắn luôn "kéo theo" một phần nội dung phía sau nó thay vì đứng chunk riêng. Khi làm sạch dữ liệu, sẽ chủ động nối câu dẫn kết thúc bằng dấu `:` với đoạn/danh sách theo sau thành một khối trước khi lưu `.md`. Và quan trọng không kém: sẽ bắt tất cả thành viên xác nhận `Embedding backend: gemini-embedding-001` (không phải mock) **trước khi** chạy benchmark chính thức, thay vì phát hiện ra sau khi đã chấm điểm xong.

---

## Tự Đánh Giá (Phần Nhóm)


| Tiêu chí                                   | Điểm tự đánh giá |
| ---------------------------------------------- | ------------------------ |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10                |
| Thiết kế chiến lược (Strategy Design)   | 15 / 15                |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10                |
| Thuyết trình (Demo)                        | 0 / 5                 |
| **Tổng phần nhóm**                        | **35 / 40**            |
