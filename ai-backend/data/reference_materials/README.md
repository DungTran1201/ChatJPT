# Local Exam & Reference Materials Repository

This directory contains local offline PDF documents and audio files downloaded directly from Google Drive for offline study, in-app browser reading, and AI RAG knowledge retrieval.

## Statistics
- Total Files: 97 local files
- Total Size: ~1.58 GB
- Levels: N5, N4, N3, N2, N1, Kaiwa
- Manifest: `ai-backend/data/download_manifest.json`

## Synchronization
To re-download or update files from Google Drive:
```bash
python tools/download_all_drive_materials.py
python tools/sync_local_materials_to_db.py
```

