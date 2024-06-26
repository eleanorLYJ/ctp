import re

def parse_log(file_path):
    log_data = []
    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(r'.*value=(\d+), version=(\d+)', line)
            if match:
                value, version = map(int, match.groups())
                log_data.append((value, version))
    return log_data

def verify_logs(writer_log, reader_log, output_log):
    writer_data = parse_log(writer_log)
    reader_data = parse_log(reader_log)
    
    writer_dict = {version: value for value, version in writer_data}
    
    with open(output_log, 'w') as output:
        for value, version in reader_data:
            if version not in writer_dict:
                output.write(f"Error: Read version {version} not found in writer log\n")
            elif writer_dict[version] != value:
                output.write(f"Error: Read value {value} does not match written value {writer_dict[version]} for version {version}\n")
            else:
                output.write(f"Success: Read value {value} matches written value for version {version}\n")

if __name__ == "__main__":
    verify_logs("writer_log.txt", "reader_log.txt", "output_log.txt")

