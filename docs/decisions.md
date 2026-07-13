# Decisions log

Format: `YYYY-MM-DD | decision | why`

- 2026-07-13 | Fix `.env.example` key to `GROQ_API_KEY` (brief typo `GROQ_API_KEEY_OPTIONAL`) | Valid env name
- 2026-07-13 | M1 timeseries uses Chronos when installed, else residual z-score | Offline-reproducible detection without heavy downloads
- 2026-07-13 | Drop librosa in M1; stdlib wave + numpy log-mel proxy | Avoid numba pin conflicts on Python 3.11/3.12
- 2026-07-13 | Compose publishes high host ports (15432, 11883, 18000) | Reduce collisions with common local stacks
- 2026-07-13 | Verify via GitHub Actions, not developer workstation Docker | Multi-machine workflow; no interference with local WSL services
- 2026-07-13 | Public repo `H3Xobit/factorypulse` | Public product repo; secrets only via env
- 2026-07-13 | Switch DB image to `pgvector/pgvector:pg16` for M2 RAG | Need vector + HNSW; keep high host ports
- 2026-07-13 | Use deterministic hashing embeddings (384-d) offline; bge-m3 optional later | Avoid multi-GB model download on CI/dev machines
- 2026-07-13 | Default `FP_OFFLINE_LLM=1` with cited template diagnosis | Demos/CI work without API keys; live providers when keys set
- 2026-07-13 | Publish web UI on host port 13000 | Avoid clashing with common :3000 services
- 2026-07-13 | Prefer Kaggle download script over committing IMS archives | Keep repo light; delete local downloads after use
- 2026-07-13 | Deploy static Next.js showcase to GitHub Pages at `/factorypulse` | Public website without hosting MQTT/DB on this workstation; full stack remains `make demo`
- 2026-07-13 | Web console falls back to showcase demo data when API health fails | Site stays browsable online while repo keeps full backend wiring
