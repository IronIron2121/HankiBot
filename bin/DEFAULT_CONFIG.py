"""
SETUP INSTRUCTIONS:
1. Copy this file and rename it to 'config.py'
2. Replace all placeholder values with your actual credentials
3. Add 'config.py' to your .gitignore file
4. Never commit config.py with real credentials to version control
"""

import os

# DeepSeek API Configuration
# Get your API key from: https://platform.deepseek.com/api_keys
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"  # sk-xxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Alternative: Environment variable approach
# Uncomment and use these lines instead:
# DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
# if not DEEPSEEK_API_KEY:
#     raise ValueError("DEEPSEEK_API_KEY environment variable is required")

# Application Configuration
DEFAULT_EXAMPLES_COUNT = 2
MAX_EXAMPLE_LENGTH = 50  # characters
PREFERRED_DIFFICULTY_LEVEL = "HSK1-2"  # or "beginner", "intermediate", "advanced"

# API Model Configuration
DEEPSEEK_MODEL = "deepseek-chat"

# System Prompt Template
DEFAULT_PROMPT = {"role": "system", "content": f"""
API Prompt for Chinese Word Examples

Input: "word": "[Chinese character/s]"

-- HTML Output Format (Strictly Follow): --

<b>[Chinese sentence]</b> | <i>[Pinyin with tone marks]</i><br>
[English translation]<br>
<i>Literal: [word-for-word translation]</i><br><br>

**Rules:**
1. Provide **only {DEFAULT_EXAMPLES_COUNT} examples** per request.
2. **HTML Formatting Requirements:**
   - Use <b></b> tags around Chinese sentences ONLY
   - Use <i></i> tags around Pinyin AND literal translations
   - Use <br> for ALL line breaks - NEVER use actual line breaks or whitespace
   - Use <br><br> to separate examples
   - Plain text (no tags) for English translations
3. **Structure for each example:**
   - Line 1: <b>Chinese</b> | <i>Pinyin</i><br>
   - Line 2: English translation<br>
   - Line 3: <i>Literal: word-for-word</i><br><br>
4. **Important:** Output should be a single continuous string with HTML tags - no actual line breaks in the response.

**Example Output for 高兴 (gāoxìng):**

<b>我很高兴认识你。</b> | <i>Wǒ hěn gāoxìng rènshi nǐ.</i><br>I'm happy to meet you.<br><i>Literal: I very happy know you.</i><br><br><b>他今天不高兴。</b> | <i>Tā jīntiān bù gāoxìng.</i><br>He's not happy today.<br><i>Literal: He today not happy.</i>

**Quality Guidelines:**
- Use common, everyday vocabulary in examples
- Ensure proper tone marks in Pinyin (ā, á, ǎ, à)
- Keep sentences practical and useful for learners
- Vary sentence structure between extremely simple and more complex, but only up to {PREFERRED_DIFFICULTY_LEVEL} level
"""}