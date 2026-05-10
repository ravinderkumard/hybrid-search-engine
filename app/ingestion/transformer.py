import re
from html import unescape


class DocumentTransformer:
    def clean_html(self, text: str) -> str:
        text = unescape(text)

        # remove code blocks
        text = re.sub(
            r'<code>.*?</code>',
            '',
            text,
            flags=re.DOTALL
        )

        # remove html tags
        text = re.sub(r'<.*?>', '', text)

        # normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def transform(self, raw_doc):
        title = self.clean_html(
            raw_doc["title"]
        )

        content = self.clean_html(
            raw_doc["body"]
        )

        # quality filtering
        if not title:
            return None

        if len(content) < 40:
            return None

        return {
            "id": raw_doc["id"],
            "title": title,
            "content": content,
            "source": "stackoverflow",
            "category": "programming"
        }