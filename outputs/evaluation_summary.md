# Evaluation Summary

## Accuracy

- Flat RAG: 8/20
- GraphRAG: 20/20

## Build time

- Flat RAG build time: 0.01s
- GraphRAG build time: 117.83s

## Token usage estimate

- Flat RAG answer tokens (rough): 257
- GraphRAG answer tokens (rough): 264

## Cost analysis

- Flat RAG re index nhanh hon nhung de nham khi cau hoi can noi quan he qua nhieu chunk.
- GraphRAG ton cong hon o buoc indexing va graph construction.
- Doi lai, GraphRAG dat loi the ro o cau hoi two-hop va multi-hop.

## Cases where GraphRAG beats Flat RAG

- Q2: When was OpenAI founded?
  Flat RAG: 1994
  GraphRAG: 2015
- Q7: Who founded the company that acquired Instagram?
  Flat RAG: Meta
  GraphRAG: Mark Zuckerberg
- Q9: Who founded the company that acquired YouTube?
  Flat RAG: Insufficient retrieved context.
  GraphRAG: Larry Page, Sergey Brin
- Q10: Who founded the company that acquired LinkedIn?
  Flat RAG: Microsoft
  GraphRAG: Bill Gates, Paul Allen
- Q11: Which city is the company that launched ChatGPT headquartered in?
  Flat RAG: Seattle
  GraphRAG: San Francisco
- Q12: Which company acquired the company founded by Kevin Systrom?
  Flat RAG: Insufficient retrieved context.
  GraphRAG: Meta
- Q13: Who is the CEO of the company that acquired the company founded by Chad Hurley?
  Flat RAG: Satya Nadella
  GraphRAG: Sundar Pichai
- Q15: Who founded the company that invested in the company that launched Claude?
  Flat RAG: Amazon
  GraphRAG: Jeff Bezos
- Q16: Which company owns the product ecosystem associated with the company acquired by Google in 2014?
  Flat RAG: Insufficient retrieved context.
  GraphRAG: Google
- Q18: Who founded the company that launched the iPhone?
  Flat RAG: Satya Nadella
  GraphRAG: Steve Jobs, Steve Wozniak, Ronald Wayne
- Q19: Which company acquired the company founded by Reid Hoffman?
  Flat RAG: Insufficient retrieved context.
  GraphRAG: Microsoft
- Q20: Which city is the company that acquired Twitch headquartered in?
  Flat RAG: San Francisco
  GraphRAG: Seattle
