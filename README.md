# Pub-Sub Log Aggregator Terdistribusi (Docker Compose)
**Idempotent Consumer • Strong Deduplication • Transactions/Concurrency Control • Persistent Storage • k6 Load Test**

Sistem ini adalah *distributed log aggregator* berbasis arsitektur **publish–subscribe** untuk mengumpulkan event log dari banyak sumber, memprosesnya secara **at-least-once**, namun tetap konsisten melalui:
- **Idempotent consumer** (event yang sama tidak diproses ulang)
- **Strong deduplication** (persisten, tahan restart/recreate container)
- **Transaksi & kontrol konkurensi** (mencegah race condition / double-process)
- Seluruh layanan berjalan **lokal di Docker Compose** (tanpa layanan eksternal publik)

> **Tema UAS:** Pub-Sub Log Aggregator Terdistribusi dengan Idempotent Consumer, Deduplication, dan Transaksi/Kontrol Konkurensi (Docker Compose Wajib)

---

## ✨ Fitur Utama
- **API Aggregator**
  - `POST /publish` menerima single/batch event (validasi skema JSON)
  - `GET /events?topic=...` menampilkan event unik yang sudah diproses
  - `GET /stats` metrik: received, unique_processed, duplicate_dropped, uptime, topics
- **At-least-once delivery**: publisher sengaja mengirim duplikasi, sistem tetap konsisten
- **Idempotency & dedup persisten**: dedup gate disimpan di database (unique constraint)
- **Transaksi & kontrol konkurensi**: pemrosesan event dilakukan dalam transaksi untuk mencegah race condition
- **Multi-worker consumer**: beberapa worker memproses paralel tanpa double-process
- **Persistensi aman**: data tetap ada walau container dihapus (volume)
- **Observability**: logging unique vs duplicate + endpoint stats
- **Performa minimum**: target ≥ 20.000 event (≥ 30% duplikasi) tetap responsif
- **Load test**: k6 script tersedia

---

## 🧱 Arsitektur Sistem
### Komponen (Docker Compose)
- **aggregator**: REST API + internal consumer workers
- **publisher**: simulator/generator event (termasuk duplikasi)
- **broker**: Redis (internal network)
- **storage**: PostgreSQL (persisten via volume)

### Alur Data (End-to-End)
1. `publisher` mengirim event (termasuk duplikasi) ke `aggregator: /publish`
2. `aggregator` validasi & enqueue ke Redis (queue)
3. Worker consumer memproses queue → transaksi DB:
   - dedup gate `processed_events(topic,event_id)` (unik)
   - insert event ke tabel `events`
   - update statistik secara atomik
4. User mengambil hasil melalui `GET /events` dan `GET /stats`

---

## 🧾 Model Event (JSON)
Format minimal:
```json
{
  "topic": "string",
  "event_id": "string-unik",
  "timestamp": "ISO8601",
  "source": "string",
  "payload": { "any": "object" }
}

---

## 🔁 Idempotency & Strong Deduplication (Persisten)

Dedup dilakukan di database menggunakan **constraint unik**:

- Tabel `processed_events` memiliki **PRIMARY KEY (topic, event_id)**.
- Saat consumer memproses event, dilakukan pola:
  - `INSERT ... ON CONFLICT DO NOTHING`
  - Jika insert sukses → event diproses & disimpan (**unique**).
  - Jika conflict → dianggap **duplicate** dan **tidak ada side-effect ganda**.

Dengan model ini, meskipun event:
- diterima berkali-kali (**at-least-once**),
- worker paralel memproses bersamaan,
- container aplikasi di-restart atau di-recreate,

hasil akhir tetap **konsisten** dan **unik**.

---

## 🔒 Transaksi & Kontrol Konkurensi (Bab 8–9)

### Strategi Utama (Anti Race Condition)

Pemrosesan **1 event** dilakukan dalam **satu transaksi** agar bebas race condition:

1. `received` di-*increment* (atomik).
2. Dedup gate: `INSERT` ke `processed_events`.
3. Jika **unique** → `INSERT` ke `events` + *increment* `unique_processed`.
4. Jika **duplicate** → *increment* `duplicate_dropped`.

### Idempotent Write Pattern

- `INSERT ... ON CONFLICT DO NOTHING` → dedup atomik.
- Update counter `count = count + 1` → aman dari **lost-update**.

### Isolation Level

- **Dipakai:** `READ COMMITTED` (default Postgres).
- **Alasan:** dedup & konflik ditangani oleh **unique constraint/upsert**, lebih ringan daripada `SERIALIZABLE`.
- **Opsional:** untuk kasus **batch atomic/outbox** yang kompleks dapat dipertimbangkan `SERIALIZABLE` + retry.

---

## 🚀 Cara Menjalankan

### Prasyarat

- Docker + Docker Compose v2
- (Opsional) k6 untuk load test

### 1) Jalankan semua service

```bash
docker compose up --build