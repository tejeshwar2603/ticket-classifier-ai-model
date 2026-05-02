#regular expressions

def classify_log(log):
    import re
    if re.search(r'ERROR', log):
        return 'Error'
    elif re.search(r'WARNING', log):
        return 'Warning'
    elif re.search(r'INFO', log):
        return 'Info'
    else:
        return 'Unknown'
    
# Example usage
log_entry = "2024-06-01 12:00:00 ERROR Something went wrong"
classification = classify_log(log_entry)
print(f"The log entry is classified as: {classification}")