import json

def save_output(filename, data):
    try:
        with open(f"/output/{filename}", 'w') as f:
            json.dump(data, f, indent=4)
            return True
    except IOError as e:
        print(f"Error saving output: {e}")
        return False
        