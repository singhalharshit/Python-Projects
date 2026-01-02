
def scan_log():
    try:
        # Try UTF-16 which acts as default for Powershell > redirect
        with open('setup_output_v2.txt', 'r', encoding='utf-16') as f:
            for line in f:
                if 'Error' in line or 'VERIFICATION' in line or 'Skipping' in line or 'Inserting' in line:
                    print(line.strip())
    except Exception as e:
        print(f"Failed to read log: {e}")

if __name__ == "__main__":
    scan_log()
