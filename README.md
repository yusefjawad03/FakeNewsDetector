# sd-hwpcs

# **Knowledge Based Detection Portion**

## **Spring Sprint Goals:**

### January Sprint
- Team goal: Integrate our current portions to have a prototype for our final product ready to be improved upon
- Yusef: Integrate OpenAI GPT API for claim extraction and develop initial front-end UI design for input and results visualization from data extracted from OpenAI.
- Brendan: Set up the back-end infrastructure for API integration with previously implemented fact-checking API, and continue running and improving the machine learning pipeline for analyzing article credibility.
  
### February Sprint
- Team Goal: Finalize fact-checking pipeline and front-end-back-end integration.
- Yusef: Expand on the Google chrome extension, creating a website that provides the in-depth credibility scores that aren't currently displayed, and add functionality for displaying sources and references.
- Brendan: Finalize the set of data to be used as the main model for testing accuracy (for our machine learning model), ensuring at least 70% accuracy

### March Sprint
- Team goal:  Enhance system accuracy and scalability.
- Yusef: Develop documentation for front-end workflows and usage, assist in debugging integration between front-end and back-end 
- Brendan: Fine-tune machine learning models using defined kaggle datasets, and focus on optimizing database performance for handling high volumes of data.

### April Sprint
- Team Goal: Final testing and deployment
- Yusef: Conduct end-to-end system testing for front-end components, and prepare presentation materials, including UI walkthroughs and demos.
- Brendan: Perform back-end stress testing and optimize response times, making sure all machine learning components are stable and well-documented.


## **Overview**
This portion of the project is a fact-checking system designed to extract claims, facts, and statistics from news articles and validate them using multiple APIs, including:
- **OpenAI GPT** for extracting structured claims with context.
- **Google Fact Check API** for verifying claims against a database of fact-checked content.
- **LibrAI** for in-depth validation with supporting evidence.

The system calculates an overall credibility score for the article based on results from these sources, with greater weight given to LibrAI for detailed analysis.

---

## **Features**
1. **Fact Extraction**:
   - Uses OpenAI GPT to extract structured claims, statistics, and facts from input articles in JSON format.
2. **Fact-Checking**:
   - **Google Fact Check API**: Provides credibility scores and references from a trusted database.
   - **LibrAI Fact Checker**: Offers detailed analysis with evidential reasoning.
3. **Combined Scoring**:
   - Calculates a weighted score, with LibrAI contributing 70% and Google 30%.
4. **Result Storage**:
   - Saves combined results and details to a `results.txt` file.

---

## **Installation (for use before overall project integration)**
### **1. Prerequisites**
- Python 3.8+
- Required Python packages:
  - `openai`
  - `requests`
  - `pyyaml`
  - `time`

### **2. Clone the Repository**
```bash
git clone https://github.com/GW-CS-SD-24-25/sd-hwpcs.git
cd /knowledgeBased
```
---

## **Configuration**
API keys are setup in a `config.yaml` file:
```yaml
OPENAI_API_KEY: "your_openai_api_key"
GOOGLE_FACT_API_KEY: "your_google_fact_api_key"
LIBRAI_API_KEY: "your_librai_api_key"
```

---

## **Usage**

### **Run the Program**
1. Place your article in a `.txt` file (e.g., `allTrueTest.txt`).
2. Run the script:
   ```bash
   python factExtraction.py
   ```
3. Enter file name of .txt file where news text is.

### **Key Outputs**
- **Terminal Output**: Displays extracted facts, fact-checking results, and scores.
- **File Output**: Combined results with complete breakdown are saved in `results.txt`.

---

## **Sample Results**

### **Input Article:**
```plaintext
The Earth is 71% water. Neil Armstrong landed on the Moon in 1969.
```

### **Results:**
```plaintext
=== Combined Fact-Checking Results ===
Source: Google Fact Checker
Claim: The Earth is 71% water
Factuality: True
Publisher: Science Journal
URL: http://example.com

Source: LibrAI
Claim: The Earth is 71% water
Factuality: 0.95
Evidences:
  - Relationship: Supports
    Reasoning: Verified by multiple studies.
    URL: http://example.com

Overall fact check score: 90.5%
```

---

## **Contributors**
- Seeam
- Yusef
- Brendan
- Matt