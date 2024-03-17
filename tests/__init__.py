import os

test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
if not os.path.isdir(test_data_dir):
    os.makedirs(test_data_dir)


def get_test_data_path(file_name: str) -> str:
    return os.path.join(test_data_dir, file_name)


def load_test_data(file_name: str) -> str:
    full_path = get_test_data_path(file_name)
    if not os.path.isfile(full_path):
        raise FileNotFoundError(
            f"{file_name} not found, availible files are: {os.listdir(test_data_dir)}"
        )
    with open(full_path, encoding="utf-8") as f:
        return f.read()


def write_temp_to_test_data(data: str):
    full_path = get_test_data_path("temp.txt")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(data)
