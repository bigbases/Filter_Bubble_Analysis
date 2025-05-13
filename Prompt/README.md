# News Article Annotation Prompt Collection

This directory contains prompt templates for analyzing political leanings and stances on specific topics in news articles.

## File Structure

- **prompt_role_opposed_left.txt**: Prompt for an annotator with a left-leaning political perspective opposed to the query
- **prompt_role_supportive_right.txt**: Prompt for an annotator with a right-leaning political perspective supportive of the query
- **prompt_role_supportive_left.txt**: Prompt for an annotator with a left-leaning political perspective supportive of the query
- **prompt_role_opposed_right.txt**: Prompt for an annotator with a right-leaning political perspective opposed to the query

## Prompt Functionality

These prompts analyze news articles according to the following evaluation criteria:

1. **Political**
   - Definition: The political leanings of the article
   - Label: [Left, Center, Right]
   - Score: From -1 (extreme Left) to 1 (extreme Right), including decimal values

2. **Stance**
   - Definition: The article's position on the specific topic ({query})
   - Label: [Against, Neutral, Support]
   - Score: From -1 (extreme Against) to 1 (extreme Support), including decimal values

## Usage

Each prompt contains a {query} placeholder that should be replaced with the specific topic being analyzed (e.g., "Biden", "Trump", "immigration", etc.).

Results are output in the following JSON format:

```json
{
  "Political": {
    "label": "[label]",
    "score": [decimal score]
  },
  "Stance": {
    "label": "[label]",
    "score": [decimal score]
  },
  "Reasoning": "[brief explanation of 50 tokens or less]"
}
```

## Examples

The prompt files include examples of analyzing news articles on topics such as "Biden", "Trump", and "immigration". 