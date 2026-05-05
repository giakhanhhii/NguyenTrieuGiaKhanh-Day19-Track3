# LAB DAY 19 - Xây dựng hệ thống GraphRAG với Tech Company Corpus

Dự án này bám sát các bước trong đề bài:

1. Research
2. Environment setup
3. Indexing
4. Graph construction
5. Querying
6. Evaluation giữa Flat RAG và GraphRAG

## Cấu trúc thư mục

- [research_notes.md](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\research_notes.md): Câu trả lời phần nghiên cứu
- [run_lab.py](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\run_lab.py): Lệnh chạy toàn bộ pipeline
- [data/tech_company_corpus.json](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\data\tech_company_corpus.json): Corpus mẫu
- [data/benchmark_questions.json](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\data\benchmark_questions.json): 20 câu benchmark
- [src/graph_rag.py](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\src\graph_rag.py): GraphRAG
- [src/flat_rag.py](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\src\flat_rag.py): Flat RAG baseline
- [src/evaluate.py](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\src\evaluate.py): Đánh giá và xuất bảng kết quả

## Cài đặt

Chạy đúng theo hướng trong đề:

```bash
pip install networkx matplotlib neo4j openai pandas
pip install langchain langchain-openai
```

## Cấu hình `.env`

Dự án đã có sẵn file [.env](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\.env). Bạn chỉ cần mở file đó và điền:

- `OPENAI_API_KEY`
- `OPENAI_MODEL=gpt-4o-mini`
- `GRAPH_EXTRACTOR_MODE=openai`

Code sẽ tự động đọc `.env`, không cần cài thêm `python-dotenv`.

Ví dụ:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
GRAPH_EXTRACTOR_MODE=openai

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
```

## Cách chạy

### 1. Chạy toàn bộ pipeline

```bash
python run_lab.py
```

Lệnh này sẽ:

- xây dựng GraphRAG
- xây dựng Flat RAG baseline
- chạy benchmark 20 câu hỏi
- xuất bảng kết quả và file tóm tắt

### 2. Chạy riêng phần GraphRAG và sinh ảnh đồ thị

```bash
python -m src.graph_rag
```

Nếu máy gặp lỗi cache của `matplotlib`, dùng:

```bash
$env:MPLCONFIGDIR="$PWD\.mplcache"
python -m src.graph_rag
```

### 3. Chạy riêng phần đánh giá

```bash
python -m src.evaluate
```

## Đầu ra dự kiến

- [outputs/triples.csv](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\outputs\triples.csv)
- [outputs/evaluation_results.csv](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\outputs\evaluation_results.csv)
- [outputs/evaluation_summary.md](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\outputs\evaluation_summary.md)
- [outputs/neo4j_import.cypher](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\outputs\neo4j_import.cypher)
- [screenshots/knowledge_graph.png](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\screenshots\knowledge_graph.png)

## Cách dùng Neo4j để có trực quan hóa đẹp hơn

Dự án đã có sẵn:

- hàm export Cypher
- hook đẩy dữ liệu sang Neo4j

Để demo bằng Neo4j:

1. Mở `Neo4j Desktop`
2. Tạo hoặc bật database local
3. Cập nhật `.env` với:
   - `NEO4J_URI`
   - `NEO4J_USERNAME`
   - `NEO4J_PASSWORD`
4. Chạy lại:

```bash
python -m src.graph_rag
```

Sau đó có thể chụp màn hình từ `Neo4j Browser` hoặc `Bloom`.

## Chế độ trích xuất triples

Phần `Entity Extraction` trong đề ưu tiên dùng LLM. Dự án hỗ trợ 2 chế độ:

- `openai`: dùng OpenAI để trích xuất triples, bám sát tinh thần đề bài nhất
- `rule_based`: chạy nhanh, ổn định, phù hợp để kiểm tra logic hoặc demo khi không muốn chờ API

Nếu muốn bám sát đề nhất, hãy để trong `.env`:

```env
GRAPH_EXTRACTOR_MODE=openai
```

Nếu muốn chạy nhanh để kiểm tra:

```env
GRAPH_EXTRACTOR_MODE=rule_based
```

## Ảnh chụp màn hình để nộp

Đề yêu cầu ảnh đồ thị tri thức đã xây dựng từ `Neo4j` hoặc `Matplotlib`.

Ảnh hiện có trong dự án:

- [screenshots/knowledge_graph.png](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\screenshots\knowledge_graph.png)

Nếu cần đúng hình thức “ảnh chụp màn hình”, bạn có thể:

1. Mở file `knowledge_graph.png`
2. Nhấn `Win + Shift + S`
3. Chụp lại màn hình
4. Lưu vào thư mục [screenshots](C:\Users\giakh\Project\NguyenTrieuGiaKhanh-Day19-Track3\screenshots)

## Deliverables khớp rubric

1. Mã nguồn `.py`
2. Ảnh đồ thị tri thức từ `Matplotlib` hoặc `Neo4j`
3. Bảng benchmark 20 câu giữa Flat RAG và GraphRAG
4. Phân tích ngắn về độ chính xác, thời gian build graph, token usage và chi phí

## Ghi chú khi chạy

- Nếu thấy dòng báo không kết nối được `localhost:7687`, nghĩa là Neo4j chưa bật. Điều này không ảnh hưởng nếu bạn đang dùng `Matplotlib`.
- Nếu chạy `openai` thì thời gian có thể khoảng 2 đến 3 phút vì phải gọi API nhiều lần.
- Nếu chỉ cần chạy nhanh để kiểm tra, chuyển sang `rule_based`.
