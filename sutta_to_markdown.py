import re
import requests
from bs4 import BeautifulSoup, NavigableString
import html2text

# Unicode ideographic space for indenting
IDEOGRAPHIC_SPACE = "　"
INDENT_TAG = "[INDENT]"

# Map verse classes to number of ideographic spaces for indenting
INDENT_MAP = {f"v{i}": INDENT_TAG*i for i in range(1, 9)}

VERSE_BREAK_TAG = "[VERSE-ADD]"

SUPERSCRIPT_TAG = "[SUPERSCRIPT]"

def process_verse_div(verse_div):
    """
    Process a <div class="verse"> element:
      - For each <p> inside that has one of the classes "v1" to "v8", prepend the
        corresponding number of INDENT_TAG's.
      - Mark verse breaks with VERSE_BREAK_TAG
    """
    # Process any <p> elements that require extra indentation.
    for p in verse_div.find_all("p"):
        classes = p.get("class", [])
        for cls in classes:
            if cls in INDENT_MAP:
                # Replace the paragraph text with the indented text.
                p.insert(0, NavigableString(INDENT_MAP[cls]))
                break
    for div in verse_div.find_all("div", class_="verse-add"):
        first_line = div.find("p")
        first_line.string = VERSE_BREAK_TAG + first_line.string

def process_dhammatalks_sutta_to_markdown(html, url):
    soup = BeautifulSoup(html, "html.parser")

    # Remove header and footer elements so that only the body remains.
    for tag in soup.find_all(["header", "footer"]):
        tag.decompose()

    # Assume the main sutta content is in a div with id="sutta"
    main_content = soup.find("div", id="sutta")
    if main_content is None:
        main_content = soup.body

    # Remove any linebreaks in the heading, as these confuse the
    # hyperlinking to the original sutta page
    heading = main_content.find("h1")
    for br in heading.select("br"):
        br.replace_with(":")

    # Hyperlink the heading to the original sutta page
    heading.wrap(soup.new_tag("a", href=url))

    title = heading.string

    # Process all <div class="verse"> elements.
    for verse_div in main_content.find_all("div", class_="verse"):
        process_verse_div(verse_div)
        # Create a new blockquote element to hold the quoted text.
        blockquote_tag = soup.new_tag("blockquote")
        verse_div.wrap(blockquote_tag)

    # Superscript and de-link any footnotes
    for fn_span in main_content.find_all("span", class_="fn"):
        fn_span.string = f"{SUPERSCRIPT_TAG}{fn_span.get_text()}"

    # Convert the modified HTML (only the main content) to Markdown.
    converter = html2text.HTML2Text()
    converter.baseurl = "https://www.dhammatalks.org/"
    converter.body_width = 0  # Do not wrap lines arbitrarily.
    markdown = converter.handle(str(main_content))
    markdown = markdown.replace(INDENT_TAG, IDEOGRAPHIC_SPACE)
    markdown = markdown.replace(SUPERSCRIPT_TAG, "^")
    markdown = re.sub("\n> \n", "\n", markdown)
    markdown = markdown.replace("\n", "  \n") # Ensure line breaks
    markdown = re.sub("\n(Notes?)  \n", "\n## \\1  \n", markdown)
    return title, markdown.replace("> "+VERSE_BREAK_TAG, ">\n> ")

def get_random_dhammatalks_sutta_html():
    url = "https://www.dhammatalks.org/random_sutta.php"
    response = requests.get(url)
    response.raise_for_status()
    return response.content, response.url

def get_random_dhammatalks_sutta_markdown():
    return process_dhammatalks_sutta_to_markdown(
        *get_random_dhammatalks_sutta_html()
    )
    
def main():
    print(get_random_dhammatalks_sutta_markdown()[1])

if __name__ == "__main__":
    main()
