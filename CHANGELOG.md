# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-03-14

### Changed
- **Major Refactor**: Consolidated 20+ flat Python scripts into a clean package structure.
- **Legacy Sanitization**: Renamed all files in the `legacy/` directory from numerical prefixes (e.g., `10_ai_1_*.py`) to descriptive names (e.g., `transcript_analyzer.py`) for better readability.
- Optimized `main.py` to use direct function calls instead of `subprocess.run`.
- Improved data flow by eliminating intermediate JSON disk writes for internal pipeline stages.
- Unified API client usage across the entire project.

### Added
- Created `src/pipeline` modular structure.
- Introduced `AIAnalyzer` using OpenAI Structured Outputs for comprehensive auditing.
- Added `DataCollector`, `DataCleaner`, and `Reporter` classes to centralize logic.
- New Mermaid-based architecture diagram in `README.md`.
- **New Documentation**: Added `agent.md` to detail the AI Auditor's decision logic and capabilities.

### Removed
- Removed 22 legacy procedural scripts (`01_*.py` through `14_*.py`, `remover.py`, `reporter.py`).

## [1.0.0] - 2024-10-01
- Initial release with procedural script-based pipeline.
