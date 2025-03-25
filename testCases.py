import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import factExtraction

resultsList = [0, 0, 0]

#all true text test
# resultsList.append(factExtraction.fullFactCheckTest("allTrueTest.txt"))
resultsList[0] = factExtraction.fullFactCheckTest("allTrueTest.txt")

#all fake text test
# resultsList.append(factExtraction.fullFactCheckTest("allFakeTest.txt"))
resultsList[1] = factExtraction.fullFactCheckTest("allFakeTest.txt")

#some true some fake text test
# resultsList.append(factExtraction.fullFactCheckTest("someTrueSomeFaketest.txt"))
resultsList[2] = factExtraction.fullFactCheckTest("someTrueSomeFaketest.txt")

if resultsList[0] >= 80 and resultsList[1] <= 35 and (resultsList[2] <= 80 and resultsList[2] >= 30):
    print("===========================================")
    print("Tests pass")
    print(f"allTrueTest expected score >80%, actual score: {resultsList[0]}")
    print(f"allFakeTest expected score <35%, actual score: {resultsList[1]}")
    print(f"someTrueSomeFaketest 35% < expected score <80%, actual score: {resultsList[2]}")
else:
    print("===========================================")
    print("At least 1 test failed")
    print(f"allTrueTest expected score >80%, actual score: {resultsList[0]}")
    print(f"allFakeTest expected score <35%, actual score: {resultsList[1]}")
    print(f"someTrueSomeFaketest 35% < expected score <80%, actual score: {resultsList[2]}")

# x = factExtraction.fullFactCheckTest("allTrueTest.txt")
# print(x)
