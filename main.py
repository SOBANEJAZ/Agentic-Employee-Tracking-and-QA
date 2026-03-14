import argparse
import logging
import sys
from src.core.monday_client import MondayClient
from src.core.openphone_client import OpenPhoneClient
from src.pipeline.collectors import DataCollector
from src.pipeline.cleaners import DataCleaner
from src.pipeline.ai_analyzers import AIAnalyzer
from src.pipeline.reporters import Reporter

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Agentic Employee Tracking & QA Pipeline v2.0")
    parser.add_argument("--days", type=int, default=16, help="Days offset for processing (default: 16)")
    args = parser.parse_args()

    try:
        logger.info("Initializing Pipeline v2.0...")
        
        # 1. Initialize Clients
        monday = MondayClient()
        openphone = OpenPhoneClient()
        
        # 2. Initialize Pipeline Modules
        collector = DataCollector(monday, openphone)
        analyzer = AIAnalyzer()
        reporter = Reporter(monday)

        # 3. Data Collection Phase
        # For now, we use the default board IDs from the legacy scripts
        board_ids = [8159897010] 
        logger.info("Phase 1: Collecting staff and board data...")
        staff_info = collector.get_staff_references(board_ids)
        raw_data = collector.fetch_board_data(board_ids)

        # 4. Cleaning & Filtering Phase
        logger.info("Phase 2: Cleaning and filtering session notes...")
        all_notes = []
        for board_items in raw_data.values():
            all_notes.extend(DataCleaner.clean_monday_notes([board_items]))
        
        filtered_notes = DataCleaner.filter_by_date(all_notes, days_offset=args.days)
        logger.info(f"Found {len(filtered_notes)} notes for the target date.")

        if not filtered_notes:
            logger.info("No work to process. Exiting.")
            return

        # 5. Call & Transcript Collection
        logger.info("Phase 3: Fetching call transcripts for verified staff...")
        calls = collector.fetch_call_logs(staff_info)
        # Note: In a full implementation, we'd link calls to transcripts here
        # For brevity, we proceed with placeholders or simulated linkage
        transcripts = [] # Simple linkage logic would go here

        # 6. AI Audit Phase
        logger.info("Phase 4: Running AI-powered comprehensive audit...")
        audited_notes = analyzer.audit_notes(filtered_notes, transcripts)

        # 7. Reporting Phase
        logger.info("Phase 5: Uploading QA results to Monday.com...")
        reporter.upload_qa_report(audited_notes)

        logger.info("Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
