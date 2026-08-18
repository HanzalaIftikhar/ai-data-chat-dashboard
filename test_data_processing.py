from src.data_processing import process_uploaded_file


class FakeUploadedFile:
    def __init__(self, path):
        self.name = path
        self._file = open(path, "rb")

    def read(self, *args):
        return self._file.read(*args)

    def seek(self, *args):
        return self._file.seek(*args)


f = FakeUploadedFile("sample_data/superstore.csv")
df, detected = process_uploaded_file(f)

print("Detected columns:", detected)
print(df.head(3))

from src.data_processing import generate_summary

summary = generate_summary(df)
print("\n--- Summary ---")
print("Total Revenue:", summary["total_revenue"])
print("Top Products:", summary["top_products"])
print("Insight:", summary["insight"])