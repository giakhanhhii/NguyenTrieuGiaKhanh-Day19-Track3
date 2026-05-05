# Phần 1 - Nghiên cứu và chuẩn bị

## 2.1. Quy trình xử lý dữ liệu đồ thị

### 1. Entity Extraction là gì?

Entity Extraction là bước dùng mô hình ngôn ngữ để đọc văn bản và xác định:

- đâu là thực thể
- đâu là quan hệ
- đâu là thuộc tính hoặc mốc thời gian liên quan

Trong bài này, thực thể thường gồm:

- công ty
- con người
- sản phẩm
- địa điểm
- năm

Ví dụ:

- Input: `OpenAI was founded by Sam Altman and Elon Musk in 2015.`
- Output dưới dạng triples:
  - `(OpenAI, FOUNDED_BY, Sam Altman)`
  - `(OpenAI, FOUNDED_BY, Elon Musk)`
  - `(OpenAI, FOUNDED_IN, 2015)`

Điểm mạnh của LLM là có thể đọc câu tự nhiên và rút ra các mối quan hệ ngay cả khi câu được viết theo nhiều cách khác nhau.

### 2. Graph Construction và vì sao cần Deduplication

Sau khi có triples, hệ thống sẽ xây đồ thị tri thức:

- mỗi thực thể là một node
- mỗi quan hệ là một edge

Tuy nhiên, trong dữ liệu thực tế, cùng một thực thể có thể xuất hiện dưới nhiều dạng tên khác nhau. Ví dụ:

- `Meta`
- `Facebook`
- `Meta Platforms`

Nếu không xử lý khử trùng lặp, hệ thống có thể tạo ra nhiều node cho cùng một đối tượng, dẫn đến:

- đồ thị bị phân mảnh
- mất liên kết giữa các thực thể
- truy vấn BFS đi sai hoặc không đi được đến đáp án
- giảm độ chính xác của GraphRAG

Vì vậy cần có bước chuẩn hóa tên thực thể và gộp các alias về một tên chuẩn trước khi thêm vào graph.

### 3. Query Answering: BFS khác gì vector search?

Trong GraphRAG, truy vấn được thực hiện theo hướng duyệt đồ thị:

- bắt đầu từ một node trung tâm được trích từ câu hỏi
- duyệt các node lân cận theo 1-hop hoặc 2-hop
- gom các quan hệ liên quan để tạo ngữ cảnh trả lời

Trong Flat RAG, hệ thống không dùng cấu trúc graph mà dùng vector search để tìm những đoạn văn giống nghĩa với câu hỏi.

Khác biệt chính:

- Flat RAG mạnh ở câu hỏi fact đơn giản
- GraphRAG mạnh ở câu hỏi cần suy luận qua nhiều bước quan hệ

Ví dụ:

- Câu hỏi: `Who founded the company that acquired Instagram?`
- Flat RAG có thể lấy được đoạn về `Instagram` hoặc `Meta`, nhưng dễ không nối được chuỗi quan hệ đầy đủ
- GraphRAG có thể đi theo chuỗi:
  - `Instagram <- ACQUIRED - Meta`
  - `Meta - FOUNDED_BY -> Mark Zuckerberg`

Vì vậy GraphRAG suy ra được đáp án đúng là `Mark Zuckerberg`.

## 2.2. Tìm hiểu công cụ

### NetworkX

- Là thư viện Python phù hợp để nghiên cứu mạng lưới và xây dựng graph nhanh
- Hữu ích cho việc prototype, duyệt BFS và xử lý logic truy vấn

### Neo4j

- Là cơ sở dữ liệu đồ thị chuyên dụng
- Có giao diện trực quan như Neo4j Browser hoặc Bloom
- Phù hợp khi cần trực quan hóa đẹp và thao tác với graph quy mô lớn hơn

### NodeRAG

- Là framework hỗ trợ xây dựng GraphRAG
- Giúp đơn giản hóa một số bước tích hợp
- Tuy nhiên trong bài này, hướng tự xây bằng NetworkX kết hợp xuất dữ liệu sang Neo4j giúp giải thích pipeline rõ hơn

## Chiến lược làm bài để đạt điểm cao

1. Trích xuất triples rõ ràng, nhất quán và có bước chuẩn hóa thực thể
2. Xây graph thể hiện được các quan hệ quan trọng như `FOUNDED_BY`, `CEO_OF`, `ACQUIRED`, `HEADQUARTERED_IN`
3. Cài đặt truy vấn theo 2-hop đúng như yêu cầu đề bài
4. Chuẩn bị 20 câu benchmark có cả câu hỏi single-hop, two-hop và multi-hop
5. Chứng minh được các trường hợp Flat RAG trả lời sai nhưng GraphRAG trả lời đúng
6. Có ảnh đồ thị, bảng kết quả và phần phân tích ngắn về thời gian và token usage

## File này dùng để làm gì?

File này đóng vai trò là phần trả lời cho mục `Research` trong đề bài. Nó giúp:

- giải thích bạn hiểu quy trình GraphRAG như thế nào
- chứng minh bạn nắm được sự khác biệt giữa Flat RAG và GraphRAG
- làm tài liệu tham khảo khi viết báo cáo hoặc thuyết trình

## Có bắt buộc nộp file này không?

Không phải lúc nào cũng bắt buộc nộp riêng file này, vì trong ảnh phần deliverables cuối cùng không ghi rõ phải nộp `research_notes.md`.

Tuy nhiên, file này vẫn có ích vì:

- giúp bạn có sẵn nội dung để trả lời khi thầy hỏi phần lý thuyết
- có thể trích từ đây sang báo cáo chính
- làm bài nhìn chỉn chu và đầy đủ hơn

Nếu muốn nộp gọn, bạn có thể:

- giữ file này trong project
- không cần tách riêng khi nộp
- hoặc chép phần nội dung quan trọng của file này vào báo cáo tổng hợp
