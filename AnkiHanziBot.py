#!/usr/bin/env python3
"""
Chinese Anki Bot - CLI for creating Anki cards from Chinese words
"""

import click
import uuid
import requests
import re
import json
import traceback
from urllib.parse import quote
from bs4 import BeautifulSoup

config = {
    #"DEFINITION_MODE": "ADVANCED",
    "DEFINITION_MODE": "SIMPLE",
}

# Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_dong_chinese_data(word):
    """Fetch pinyin and meaning from Dong Chinese"""
    try:
        url = f"https://www.dong-chinese.com/wiki/{quote(word)}"
        click.echo(f"🔍 Fetching from Dong Chinese: {word}")
    
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        return parse_dong_chinese_html(response.text)
        
    except requests.RequestException as e:
        click.echo(f"❌ Error fetching data: {e}", err=True)
        return {'pinyin': '[error]', 'meaning': '[error]', 'etymology': '[error]'}

def fetch_single_character_data(char):
    """Fetch data for a single character only - no recursion"""
    try:
        url = f"https://www.dong-chinese.com/wiki/{quote(char)}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Parse JSON data
        json_match = re.search(r'window\.preloadedData=(\[.*?\]|\{.*?\});', response.text, re.DOTALL)
        if not json_match:
            return None
            
        data = json.loads(json_match.group(1))
        
        # Only handle single character format (dict)
        if isinstance(data, dict):
            pinyin = data.get('pinyinFrequencies', [{}])[0].get('pinyin', '')
            meaning = data.get('gloss', '')
            hint = data.get('hint', '')
            
            return {
                'char': char,
                'pinyin': pinyin,
                'meaning': meaning,
                'hint': hint
            }
        
        return None
        
    except Exception as e:
        click.echo(f"⚠️ Error fetching data for {char}: {e}")
        return None

def create_compound_etymology(compound_word):
    """Create etymology breakdown for compound words"""
    etymology_parts = []
    
    click.echo(f"🔍 Building etymology for compound word: {' + '.join(compound_word)}")
    
    for i, char in enumerate(compound_word):
        click.echo(f"  📖 Looking up character {i+1}/{len(compound_word)}: {char}")
        
        char_data = fetch_single_character_data(char)
        if char_data:
            part = f"{char_data['char']} ({char_data['pinyin']}) - {char_data['meaning']}"
            if char_data['hint']:
                part += f" | {char_data['hint']}"
            etymology_parts.append(part)
        else:
            etymology_parts.append(f"{char} - [data not found]")
    
    return " || MANUALLY ENTER NEW-LINE HERE || ".join(etymology_parts)

def parse_dong_chinese_html(html_content):
    """Parse HTML content from Dong Chinese to extract pinyin and meaning"""
    try:
        # Look for JSON data in window.preloadedData
        json_match = re.search(r'window\.preloadedData=(\[.*?\]|\{.*?\});', html_content, re.DOTALL)
        
        if not json_match:
            click.echo("⚠️ No JSON data found, trying HTML parsing...")
            return fallback_html_parsing(html_content)
        
        click.echo("✅ JSON match found!")
        data = json.loads(json_match.group(1))
        
        # Initialize variables to avoid scope issues
        pinyin = ''
        meaning = ''
        etymology = ''
        
        # Handle single character (dict) vs compound word (list)
        if isinstance(data, dict):
            pinyin = data.get('pinyinFrequencies', [{}])[0].get('pinyin', '')
            etymology = data.get('hint', '') 
            meaning = data.get('gloss', '')

            # Advanced definition mode or fallback
            if (not meaning and 'words' in data) or config['DEFINITION_MODE'] == 'ADVANCED':
                char = data.get('char', '')
                for word_entry in data['words']:
                    if word_entry.get('simp') == char or word_entry.get('trad') == char:
                        if 'items' in word_entry and word_entry['items']:
                            definitions = word_entry['items'][0].get('definitions', [])
                            if definitions:
                                meaning = '; '.join(definitions)
                                break
                        elif 'gloss' in word_entry:
                            meaning = word_entry['gloss']
                            break
            else:
                click.echo("📚 Got main meaning!")
                            
        elif isinstance(data, list) and data:
            word_data = data[0]
            
            if 'items' in word_data and word_data['items']:
                first_item = word_data['items'][0]
                pinyin = first_item.get('pinyin', '')
                definitions = first_item.get('definitions', [])                
                if definitions:
                    meaning = '; '.join(definitions)

                # Create etymology for compound word
                compound_word = word_data.get('simp', '')
                if len(compound_word) > 1:
                    etymology = create_compound_etymology(compound_word)
                else:
                    etymology = '[single character in compound format]'

            # Fallback to gloss
            if not meaning:
                meaning = word_data.get('gloss', '')
        
        return {
            'pinyin': pinyin or '[not found]',
            'meaning': meaning or '[not found]',
            'etymology': etymology or '[not found]'
        }
        
    except Exception as e:
        click.echo(f"⚠️ Error parsing Dong Chinese data: {e}")
        click.echo(f"📋 Full error: {traceback.format_exc()}")
        return {'pinyin': '[error]', 'meaning': '[error]', 'etymology': '[error]'}

def fallback_html_parsing(html_content):
    """Fallback HTML parsing for pinyin when JSON is not available"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for pinyin in spans with tone marks
        for span in soup.find_all('span'):
            text = span.get_text(strip=True)
            if re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', text):
                return {
                    'pinyin': text, 
                    'meaning': '[meaning not found]',
                    'etymology': '[not found]'
                }
        
        return {
            'pinyin': '[not found]', 
            'meaning': '[not found]',
            'etymology': '[not found]'
        }
        
    except Exception:
        return {'pinyin': '[error]', 'meaning': '[error]', 'etymology': '[error]'}

def create_anki_card(hanzi, dong_data):
    """Create Anki card data - stroke orders will be handled by the card template"""
    wordType = "Single" if len(hanzi) == 1 else "Compound"
    return {
        'guid': str(uuid.uuid4()).replace('-', '')[:10],
        'note_type': 'Mandarin Learning (Online Stroke Order)',
        'deck': f'Mandarin::Words::{wordType}',
        '汉字': hanzi,
        '拼音': dong_data['pinyin'],
        '发音': '[audio placeholder]',
        '英语': dong_data['meaning'],
        'Lì zi (Zhōngwén)': '[example placeholder]',
        'Character Explanation': dong_data['etymology'],
        'tags': f'Mandarin::Words::{wordType}'
    }

def display_card(card_data):
    """Display the card data"""
    click.echo("\n" + "="*60)
    click.echo("📚 ANKI CARD")
    click.echo("="*60)
    click.echo(f"汉字: {card_data['汉字']}")
    click.echo(f"拼音: {card_data['拼音']}")
    click.echo(f"英语: {card_data['英语']}")
    click.echo(f"Character Explanation: {card_data['Character Explanation']}")
    click.echo("🖌️ Stroke orders: Will be loaded dynamically by card template")

def save_cards(cards):
    """Save cards to Anki import file"""
    header = "#separator:tab\n#html:true\n#guid column:1\n#notetype column:2\n#deck column:3\n#tags column:11\n"
    
    with open("anki_import.txt", 'w', encoding='utf-8') as f:
        f.write(header)
        for card in cards:
            fields = [
                card['guid'], card['note_type'], card['deck'],
                card['汉字'], card['拼音'], card['发音'], card['英语'],
                card['Lì zi (Zhōngwén)'], card['Character Explanation'],
                card['tags']
            ]
            f.write('\t'.join(fields) + '\n')
    
    return "anki_import.txt"

@click.command()
def main():
    """Chinese Anki Bot - Create Anki cards from Chinese words"""
    click.echo("🎌 Welcome to Chinese Anki Bot!")
    click.echo("📱 Stroke orders will be loaded dynamically from the web")
    click.echo("🧠 Etymology breakdowns for compound words")
    click.echo("Enter Chinese words to create Anki cards (Ctrl+C to exit)\n")
    
    all_cards = []
    
    while True:
        try:
            word = click.prompt("Enter a Chinese word or character")
            
            # Fetch data from Dong Chinese
            dong_data = fetch_dong_chinese_data(word)
            
            # Create and display card
            card = create_anki_card(word, dong_data)
            display_card(card)
            all_cards.append(card)
            
            # Save option
            if click.confirm("\nSave cards and exit?", default=False):
                filename = save_cards(all_cards)
                click.echo(f"✅ Saved {len(all_cards)} card(s) to {filename}")
                click.echo("🌐 Stroke orders will load automatically from strokeorder.com")
                break
            
        except KeyboardInterrupt:
            if all_cards and click.confirm("\n💾 Save cards before exiting?", default=True):
                filename = save_cards(all_cards)
                click.echo(f"✅ Saved {len(all_cards)} card(s) to {filename}")
            click.echo("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()