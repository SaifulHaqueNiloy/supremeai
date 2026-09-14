# SupremeAI — কম-খরচ আর্কিটেকচার প্রোটোটাইপ

আগের রোডম্যাপে বলা ৪টা আর্কিটেকচারাল কৌশলের প্রতিটার জন্য একটা ছোট, রানেবল
রেফারেন্স ইমপ্লিমেন্টেশন। উদ্দেশ্য প্রোডাকশন-রেডি কোড নয় — বরং প্রতিটা
আইডিয়ার মেকানিক্স স্পষ্ট করে দেখানো, যাতে পরে স্কেল করা যায়।

## ফাইল ম্যাপিং

| ফাইল | রোডম্যাপ আইটেম | কী করে |
|---|---|---|
| `supremeai_arch/moe.py` | Sparse MoE hybrid | Top-k gated routing + load-balancing loss + capacity-based token dropping |
| `supremeai_arch/speculative_decoding.py` | Speculative decoding cascade | Draft মডেল K-টোকেন প্রস্তাব করে, target এক পাসে verify করে (rejection sampling, quality-lossless) |
| `supremeai_arch/quant.py` | Quantization-aware training | STE-based fake-quant `nn.Linear` — INT4/INT8-এর জন্য শুরু থেকেই ট্রেইন |
| `supremeai_arch/retrieval_core.py` | RAG-native small core | ছোট cross-attention core + swappable kNN memory — নতুন জ্ঞানের জন্য re-train লাগে না |

## রান করা

**Dependency-free sanity check (এখনই রান করা হয়েছে, torch লাগে না):**
```bash
python3 smoke_test_numpy.py
```
আউটপুট প্রমাণ করে: (ক) MoE routing normalize ও load-balanced থাকে,
(খ) speculative accept/reject গাণিতিকভাবে সঠিক (baseline-এর চেয়ে বেশি
টোকেন/ফরওয়ার্ড-পাস দেয়), (গ) quantization round-trip error তাত্ত্বিক
বাউন্ডের মধ্যে থাকে।

**PyTorch-based পূর্ণাঙ্গ মডিউল (torch ইনস্টল লাগবে):**
```bash
pip install torch --break-system-packages
python3 -m supremeai_arch.moe                 # sparse routing ডেমো
python3 -m supremeai_arch.quant                # QAT INT4 লেয়ার ডেমো
python3 -m supremeai_arch.retrieval_core       # retrieval-augmented core ডেমো
```

## পরবর্তী ধাপ (স্কেল করতে গেলে)

1. **`moe.py`** → `torch.distributed` দিয়ে expert-parallelism যোগ করা (এক্সপার্ট
   ভিন্ন ভিন্ন GPU-তে রাখা), আর naive `index_add_`-এর বদলে `torch.scatter`-ভিত্তিক
   dispatch (throughput-এর জন্য)।
2. **`speculative_decoding.py`** → batched multi-sequence সাপোর্ট, KV-cache reuse
   যোগ করা যাতে draft/target উভয় মডেলই আগের computation পুনর্ব্যবহার করে।
3. **`quant.py`** → per-channel scale (per-tensor এর বদলে) — বড় মডেলে accuracy
   গ্যাপ কমায়। এক্সপোর্টের জন্য ONNX/GGUF backend যোগ করা।
4. **`retrieval_core.py`** → naive kNN-কে FAISS/pgvector দিয়ে রিপ্লেস, আর
   memory-write pipeline (embedding + chunking + dedup) যোগ করা।

## কস্ট মডেলের সাথে সংযোগ

- MoE + speculative decoding একসাথে → inference-এর per-token GPU-cost একটা
  সমমানের ডেন্স মডেলের তুলনায় মোটামুটি (top_k/n_experts) × (1/acceptance_speedup)
  ফ্যাক্টরে নামে।
- QAT → deployment মেমরি ফুটপ্রিন্ট FP16-এর তুলনায় ~২-৪x কমে (INT8/INT4)।
- Retrieval core → per-token knowledge-capacity বাড়ে re-training cost ছাড়াই —
  "knowledge update" খরচ প্রায় শূন্য (শুধু embedding+index আপডেট)।
