#!/usr/bin/env python3
"""
Chinese Anki Bot - CLI for creating Anki cards from Chinese words
"""

import click
import uuid
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
import json

def fetch_dong_chinese_data(word):
    """Fetch pinyin and meaning from Dong Chinese"""
    try:
        encoded_word = quote(word)
        url = f"https://www.dong-chinese.com/wiki/{encoded_word}"
        
        click.echo(f"🔍 Fetching data from Dong Chinese...")
        click.echo(f"📍 URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        click.echo(f"✅ Got response, status: {response.status_code}")
        click.echo(f"📄 Content length: {len(response.text)} characters")
        
        return parse_dong_chinese_html(response.text)
        
    except requests.RequestException as e:
        click.echo(f"❌ Error fetching data: {e}", err=True)
        return {'pinyin': '', 'meaning': ''}

def parse_dong_chinese_html(html_content):
    """Parse HTML content from Dong Chinese to extract pinyin and meaning"""
    try:
        click.echo("🔍 Looking for JSON data in HTML...")
        
        # Look for the preloaded JSON data in the script tag
        # Pattern: window.preloadedData=[{...}]
        json_match = re.search(r'window\.preloadedData=(\[.*?\]);', html_content, re.DOTALL)
        
        if json_match:
            click.echo("✅ Found JSON match!")
            json_string = json_match.group(1)
            click.echo(f"📄 JSON string preview: {json_string[:200]}...")
            
            data = json.loads(json_string)
            click.echo(f"📊 Parsed data type: {type(data)}, length: {len(data) if data else 0}")
            
            if data and len(data) > 0:
                word_data = data[0]
                click.echo(f"🎯 Word data keys: {list(word_data.keys())}")
                
                # Extract pinyin and meaning from the structured data
                pinyin = ''
                meaning = ''
                
                # Get pinyin from items
                if 'items' in word_data and len(word_data['items']) > 0:
                    click.echo(f"📝 Found {len(word_data['items'])} items")
                    first_item = word_data['items'][0]
                    click.echo(f"🔤 First item keys: {list(first_item.keys())}")
                    pinyin = first_item.get('pinyin', '')
                    definitions = first_item.get('definitions', [])
                    if definitions:
                        meaning = '; '.join(definitions)
                        click.echo(f"📚 Found {len(definitions)} definitions")
                
                # Fallback to gloss if no definitions
                if not meaning and 'gloss' in word_data:
                    meaning = word_data['gloss']
                    click.echo("📖 Using gloss as fallback")
                
                click.echo(f"✅ Final result - Pinyin: '{pinyin}', Meaning: '{meaning}'")
                
                return {
                    'pinyin': pinyin if pinyin else '[pinyin not found]',
                    'meaning': meaning if meaning else '[meaning not found]'
                }
        else:
            click.echo("❌ No JSON match found")
            
            # Let's try to find any window.preloadedData pattern
            broader_match = re.search(r'window\.preloadedData.*?;', html_content, re.DOTALL)
            if broader_match:
                click.echo(f"🔍 Found broader pattern: {broader_match.group(0)[:300]}...")
            else:
                click.echo("❌ No window.preloadedData found at all")
        
        # If JSON parsing fails, fall back to basic HTML parsing
        click.echo("⚠️ JSON data not found, trying HTML parsing...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for pinyin in spans with tone marks
        pinyin = ''
        pinyin_spans = soup.find_all('span')
        click.echo(f"🔍 Found {len(pinyin_spans)} span elements")
        
        for span in pinyin_spans:
            text = span.get_text(strip=True)
            if re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', text):
                pinyin = text
                click.echo(f"📝 Found pinyin in HTML: '{pinyin}'")
                break
        
        if not pinyin:
            click.echo("❌ No pinyin found in HTML either")
        
        return {
            'pinyin': pinyin if pinyin else '[pinyin not found]',
            'meaning': '[meaning not found]'
        }
        
    except Exception as e:
        click.echo(f"⚠️ Error parsing data: {e}")
        import traceback
        click.echo(f"📋 Full error: {traceback.format_exc()}")
        return {
            'pinyin': '[parsing error]',
            'meaning': '[parsing error]'
        }

def generate_guid():
    """Generate a unique GUID for the Anki card"""
    return str(uuid.uuid4()).replace('-', '')[:10]

def create_anki_card_output(hanzi, yingyu="", pinyin="", fayin="", lizi="", char_explanation="", stroke_orders=""):
    """Create Anki card data matching your actual Anki field names"""
    
    # Card data structure matching your actual Anki fields
    card_data = {
        'guid': generate_guid(),
        'note_type': 'Mandarin Learning (With Example)',
        'deck': 'Mandarin::Words::Compound',
        '汉字': hanzi,
        '拼音': pinyin,
        '发音': fayin,
        '英语': yingyu,
        'Lì zi (Zhōngwén)': lizi,
        'Character Explanation': char_explanation,
        'Stroke Orders': stroke_orders,
        'tags': 'Mandarin::Words::Compound'
    }
    
    return card_data

def format_anki_import_line(card_data):
    """Format card data as tab-separated line for Anki import"""
    # Order matches your export format:
    # guid, note_type, deck, 汉字, 拼音, 发音, 英语, Lì zi, Character Explanation, Stroke Orders, tags
    
    fields = [
        card_data['guid'],
        card_data['note_type'],
        card_data['deck'],
        card_data['汉字'],
        card_data['拼音'],
        card_data['发音'],
        card_data['英语'],
        card_data['Lì zi (Zhōngwén)'],
        card_data['Character Explanation'],
        card_data['Stroke Orders'],
        card_data['tags']
    ]
    
    return '\t'.join(fields)

def create_anki_import_file(cards_data, filename="anki_import.txt"):
    """Create a complete Anki import file"""
    header = "#separator:tab\n#html:true\n#guid column:1\n#notetype column:2\n#deck column:3\n#tags column:11\n"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(header)
        for card_data in cards_data:
            f.write(format_anki_import_line(card_data) + '\n')
    
    return filename

def display_anki_card(card_data):
    """Display the card data and show import format"""
    click.echo("\n" + "="*60)
    click.echo("📚 ANKI CARD OUTPUT")
    click.echo("="*60)
    
    click.echo(f"汉字 (Chinese): {card_data['汉字']}")
    click.echo(f"英语 (English): {card_data['英语']}")
    click.echo(f"拼音 (Pinyin): {card_data['拼音']}")
    click.echo(f"发音 (Audio): {card_data['发音']}")
    click.echo(f"Lì zi (Example): {card_data['Lì zi (Zhōngwén)']}")
    click.echo(f"Character Explanation: {card_data['Character Explanation']}")
    click.echo(f"Stroke Orders: {card_data['Stroke Orders']}")
    click.echo(f"Tags: {card_data['tags']}")
    
    click.echo("\n" + "-"*60)
    click.echo("📄 ANKI IMPORT FORMAT:")
    click.echo("-"*60)
    click.echo(format_anki_import_line(card_data))

@click.command()
def main():
    """Chinese Anki Bot - Create Anki cards from Chinese words"""
    click.echo("🎌 Welcome to Chinese Anki Bot!")
    click.echo("Enter Chinese words to create Anki cards")
    click.echo("(Press Ctrl+C to exit)")
    
    all_cards = []
    
    while True:
        try:
            # Ask user for input
            word = click.prompt("\nEnter a Chinese word or character")
            
            # Fetch data from Dong Chinese
            dong_data = fetch_dong_chinese_data(word)
            
            # Create a card with real pinyin and meaning data
            card_data = create_anki_card_output(
                hanzi=word,
                yingyu=dong_data['meaning'],
                pinyin=dong_data['pinyin'],
                fayin="[audio placeholder]",
                lizi="[example sentence placeholder]",
                char_explanation="[character explanation placeholder]",
                stroke_orders="[stroke orders placeholder]"
            )
            
            # Display the card
            display_anki_card(card_data)
            all_cards.append(card_data)
            
            # Ask if they want to save and exit
            if click.confirm("\nSave cards to import file and exit?", default=False):
                filename = create_anki_import_file(all_cards)
                click.echo(f"✅ Saved {len(all_cards)} card(s) to {filename}")
                click.echo("You can import this file into Anki!")
                break
            
        except KeyboardInterrupt:
            if all_cards and click.confirm("\n💾 Save cards before exiting?", default=True):
                filename = create_anki_import_file(all_cards)
                click.echo(f"✅ Saved {len(all_cards)} card(s) to {filename}")
            click.echo("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()