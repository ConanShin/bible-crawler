import os
import glob
import re
from validator import BibleValidator
from config import OUTPUT_DIR, TOTAL_VERSES_EXPECTED

def validate_all():
    print(f"🔍 Scanning {OUTPUT_DIR} for JSON files...")
    json_files = glob.glob(os.path.join(OUTPUT_DIR, "*.json"))
    
    if not json_files:
        print("No JSON files found.")
        return

    print("\n" + "="*110)
    print(f"{'File':<25} | {'Verses':<8} | {'Status':<8} | {'Details'}")
    print("="*110)

    for json_file in sorted(json_files):
        filename = os.path.basename(json_file)
        
        # Skip test files if needed, or include them (bible_data_test.json)
        # validator = BibleValidator(json_file)
        validator = BibleValidator(json_file)
        
        # Run validation steps safely suppressing internal logging if desired, 
        # but here we just rely on the validator object state
        if not validator.load_data():
            status = "❌ LOAD"
            details = validator.errors[0] if validator.errors else "Unknown Load Error"
            print(f"{filename:<25} | {'-':<8} | {status:<8} | {details}")
            continue

        validator.validate_structure()
        validator.validate_completeness()
        
        verse_count = len(validator.data)
        
        if validator.errors:
            status = "❌ FAIL"
            details = f"{len(validator.errors)} structural errors"
        elif validator.warnings:
            status = "⚠️ WARN"
            # Summarize warnings
            missing_books_msgs = [w for w in validator.warnings if "Missing data for book" in w]
            low_count = [w for w in validator.warnings if "Total verse count" in w]
            
            detail_msgs = []
            if missing_books_msgs:
                # Extract book names from warnings: "Missing data for book: 창세기 (창)"
                names = [re.search(r': (.*) \(', m).group(1) for m in missing_books_msgs if re.search(r': (.*) \(', m)]
                detail_msgs.append(f"Missing: {', '.join(names)}")
            if low_count:
                detail_msgs.append(f"Low Count (<{int(TOTAL_VERSES_EXPECTED * 0.9)})")
            
            if not detail_msgs:
                detail_msgs.append(f"{len(validator.warnings)} warnings")
                
            details = ", ".join(detail_msgs)
        else:
            status = "✅ PASS"
            details = "Perfect"

        print(f"{filename:<25} | {verse_count:<8} | {status:<8} | {details}")

    print("="*110 + "\n")

if __name__ == "__main__":
    validate_all()
