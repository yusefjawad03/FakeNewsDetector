# repTester.py

from reputationExtraction import extract_reputation_data

def test_extract_reputation_data():
    sample_text = """
    Jane Smith is a renowned researcher in the field of renewable energy. You can find her work on LinkedIn at linkedin.com/in/janesmith and her publications on Google Scholar. For more information, visit her website at http://www.janesmithrenewable.com.
    """

    result = extract_reputation_data(sample_text)

    print("Website URL:", result['website_url'])
    print("LinkedIn username:", result['linkedin_username'])
    print("Scholar name:", result['scholar_name'])

if __name__ == "__main__":
    test_extract_reputation_data()
