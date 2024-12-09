SENTIMENT_ANALYSE = """
### Context
The text has not been classified with a sentiment. The possible categories of sentiments
are "Positive", "Negative", "Mixed", "Neutral". Please categorize the text to the correct sentiment.
If the text is only positive, classify as "Positive",
if the text is only negative, classify as "Negative",
if there are some positives and some negatives, classify as "Mixed",
if there is no clear sentiment in the text, classify as "Neutral"

### The text:
{text}

### Task
From the text, identify the correct sentiment. 

### Expected output
sentiment: STR
Wrap it in a JSON object and remove \n.
Do not talk, explain, summarize, or make up information. Do not say anything before or after the JSON object. Think step-by-step.

"""