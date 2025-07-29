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


import os
import requests
from urllib.parse import urlparse

def download_stroke_order_images(stroke_data, download_dir="stroke_order_images"):
    """Download stroke order images and return local paths"""
    try:
        # Create download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            click.echo(f"📁 Created directory: {download_dir}")
        
        downloaded_files = {}
        
        # Download animated GIF
        if stroke_data.get('animated_gif') and not stroke_data['animated_gif'].startswith('['):
            gif_url = stroke_data['animated_gif']
            gif_filename = extract_filename_from_url(gif_url)
            gif_path = os.path.join(download_dir, gif_filename)
            
            if download_image(gif_url, gif_path):
                downloaded_files['animated_gif'] = gif_filename
                click.echo(f"🎬 Downloaded animated GIF: {gif_filename}")
            else:
                downloaded_files['animated_gif'] = '[download failed]'
        
        # Download step-by-step PNG
        if stroke_data.get('step_by_step') and not stroke_data['step_by_step'].startswith('['):
            png_url = stroke_data['step_by_step']
            png_filename = extract_filename_from_url(png_url)
            png_path = os.path.join(download_dir, png_filename)
            
            if download_image(png_url, png_path):
                downloaded_files['step_by_step'] = png_filename
                click.echo(f"📝 Downloaded step-by-step PNG: {png_filename}")
            else:
                downloaded_files['step_by_step'] = '[download failed]'
        
        return downloaded_files
        
    except Exception as e:
        click.echo(f"❌ Error downloading images: {e}")
        return {'animated_gif': '[download error]', 'step_by_step': '[download error]'}

def extract_filename_from_url(url):
    """Extract filename from URL"""
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return filename if filename else 'unknown_file'

def download_image(url, local_path):
    """Download a single image file"""
    try:
        # Check if file already exists
        if os.path.exists(local_path):
            click.echo(f"📁 File already exists: {os.path.basename(local_path)}")
            return True
        
        click.echo(f"⬇️ Downloading: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Save the file
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        click.echo(f"✅ Downloaded: {os.path.basename(local_path)} ({len(response.content)} bytes)")
        return True
        
    except Exception as e:
        click.echo(f"❌ Failed to download {url}: {e}")
        return False

def create_stroke_order_html_with_downloads(downloaded_files):
    """Create HTML for stroke orders using downloaded filenames"""
    html_parts = []
    
    # Add animated GIF if available
    if downloaded_files.get('animated_gif') and not downloaded_files['animated_gif'].startswith('['):
        gif_filename = downloaded_files['animated_gif']
        # Extract character from filename for alt text (e.g., "21710.gif" -> character from context)
        html_parts.append(f'<img alt="Stroke Order Animation" src="{gif_filename}">')
    
    # Add step-by-step PNG if available
    if downloaded_files.get('step_by_step') and not downloaded_files['step_by_step'].startswith('['):
        png_filename = downloaded_files['step_by_step']
        html_parts.append(f'<img alt="Standard stroke order" src="{png_filename}">')
    
    # Join with <br> if we have multiple images
    if len(html_parts) > 1:
        return '<br>'.join(html_parts)
    elif len(html_parts) == 1:
        return html_parts[0]
    else:
        return '[stroke order images not available]'

# Updated fetch_stroke_order_data function
def fetch_stroke_order_data(word):
    """Fetch stroke order images and download them locally"""
    # For compound words (more than 1 character), fetch stroke order for each character
    if len(word) > 1:
        click.echo(f"🖌️ Detected compound word '{word}' with {len(word)} characters")
        click.echo(f"📝 Fetching stroke order for each character: {' + '.join(list(word))}")
        
        all_downloaded_files = []
        
        for i, char in enumerate(word):
            click.echo(f"\n--- Processing character {i+1}/{len(word)}: '{char}' ---")
            char_stroke_data = fetch_single_character_stroke_order(char)
            
            # Download images for this character
            downloaded_files = download_stroke_order_images(char_stroke_data)
            all_downloaded_files.append(downloaded_files)
        
        # Create combined HTML for all characters
        html_parts = []
        for downloaded_files in all_downloaded_files:
            char_html = create_stroke_order_html_with_downloads(downloaded_files)
            if not char_html.startswith('['):
                html_parts.append(char_html)
        
        return {
            'stroke_order_html': '<br>'.join(html_parts) if html_parts else '[stroke order not available for compound words]'
        }
    else:
        # Single character - fetch and download normally
        char_stroke_data = fetch_single_character_stroke_order(word)
        
        # Download images
        downloaded_files = download_stroke_order_images(char_stroke_data)
        
        # Create HTML with downloaded filenames
        stroke_order_html = create_stroke_order_html_with_downloads(downloaded_files)
        
        return {
            'stroke_order_html': stroke_order_html
        }

def fetch_single_character_stroke_order(char):
    """Fetch stroke order for a single character"""
    try:
        encoded_char = quote(char)
        url = f"https://www.strokeorder.com/chinese/{encoded_char}"
        
        click.echo(f"🖌️ Fetching stroke order for '{char}' from StrokeOrder.com...")
        click.echo(f"📍 URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        click.echo(f"✅ Got stroke order response for '{char}', status: {response.status_code}")
        
        return parse_stroke_order_html(response.text, url)
        
    except requests.RequestException as e:
        click.echo(f"❌ Error fetching stroke order for '{char}': {e}", err=True)
        return {'animated_gif': '[animated stroke order not found]', 'step_by_step': '[step-by-step guide not found]'}

def parse_stroke_order_html(html_content, base_url):
    """Parse HTML content from StrokeOrder.com to extract stroke order images"""
    try:
        click.echo("🖌️ Parsing stroke order HTML...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        animated_gif = ''
        step_by_step = ''
        
        # Look for images within stroke-article-content divs
        content_divs = soup.find_all('div', class_='stroke-article-content')
        click.echo(f"🔍 Found {len(content_divs)} stroke-article-content divs")
        
        # DEBUG: Let's see all images we find
        all_images = soup.find_all('img')
        click.echo(f"🔍 DEBUG: Found {len(all_images)} total images on page")
        
        for i, img in enumerate(all_images):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            click.echo(f"🖼️ DEBUG Image {i}: src='{src}', alt='{alt}', title='{title}'")
        
        for div_idx, div in enumerate(content_divs):
            img = div.find('img')
            if img:
                src = img.get('src', '')
                alt = img.get('alt', '')
                title = img.get('title', '')
                
                click.echo(f"🖼️ Processing div {div_idx}: src='{src}', alt='{alt}', title='{title}'")
                
                # More robust filename extraction
                filename = ''
                if src:
                    # Handle different src formats
                    if '/' in src:
                        filename = src.split('/')[-1]
                    else:
                        filename = src
                    click.echo(f"📁 Extracted filename: '{filename}'")
                
                # Check for animated stroke order GIF
                # Look for .gif files OR specific alt/title text
                is_animation = (
                    filename.endswith('.gif') or
                    'animation' in alt.lower() or 
                    'animation' in title.lower() or
                    'stroke order animation' in alt.lower() or
                    'stroke order animation' in title.lower()
                )
                
                if is_animation and not animated_gif:
                    if filename.endswith('.gif'):
                        animated_gif = f"https://www.strokeorder.com/assets/bishun/animation/{filename}"
                        click.echo(f"🎬 Found animated stroke order: {animated_gif}")
                    else:
                        click.echo(f"⚠️ Found animation indicator but no .gif file: {filename}")
                
                # Check for step-by-step handwriting guide  
                # Look for .png files with (1) OR specific alt/title text
                is_step_by_step = (
                    ('(1).png' in filename) or
                    'standard stroke order' in alt.lower() or
                    'standard stroke order' in title.lower() or
                    'handwriting guide' in alt.lower() or
                    'handwriting guide' in title.lower() or
                    'step-by-step' in alt.lower() or
                    'step-by-step' in title.lower()
                )
                
                if is_step_by_step and not step_by_step:
                    if filename.endswith('.png'):
                        step_by_step = f"https://www.strokeorder.com/assets/bishun/guide/{filename}"
                        click.echo(f"📝 Found step-by-step guide: {step_by_step}")
                    else:
                        click.echo(f"⚠️ Found step-by-step indicator but no .png file: {filename}")
        
        # Enhanced fallback with better debugging
        if not animated_gif or not step_by_step:
            click.echo("🔍 Fallback: Enhanced image search across all images...")
            
            # Search ALL images on the page, not just in content divs
            for img in all_images:
                src = img.get('src', '')
                if not src:
                    continue
                    
                filename = src.split('/')[-1] if '/' in src else src
                click.echo(f"🔍 Fallback checking: {filename}")
                
                # Look for stroke order GIF pattern (numbers.gif)
                if not animated_gif and filename.endswith('.gif'):
                    import re
                    # Match pure number.gif patterns (21710.gif, 23383.gif, etc.)
                    if re.match(r'^\d+\.gif$', filename):
                        animated_gif = f"https://www.strokeorder.com/assets/bishun/animation/{filename}"
                        click.echo(f"🎬 Fallback found animated: {animated_gif}")
                
                # Look for step-by-step PNG pattern (numbers(1).png)  
                if not step_by_step and filename.endswith('.png'):
                    import re
                    # Match number(1).png patterns (21710(1).png, 23383(1).png, etc.)
                    if re.match(r'^\d+\(1\)\.png$', filename):
                        step_by_step = f"https://www.strokeorder.com/assets/bishun/guide/{filename}"
                        click.echo(f"📝 Fallback found step-by-step: {step_by_step}")
                
                # Stop if we found both
                if animated_gif and step_by_step:
                    break
        
        # Final debug output
        click.echo(f"🎯 FINAL RESULTS:")
        click.echo(f"   Animated GIF: {animated_gif if animated_gif else '[NOT FOUND]'}")
        click.echo(f"   Step-by-step: {step_by_step if step_by_step else '[NOT FOUND]'}")
        
        return {
            'animated_gif': animated_gif if animated_gif else '[animated stroke order not found]',
            'step_by_step': step_by_step if step_by_step else '[step-by-step guide not found]'
        }
        
    except Exception as e:
        click.echo(f"⚠️ Error parsing stroke order data: {e}")
        import traceback
        click.echo(f"📋 Full error: {traceback.format_exc()}")
        return {
            'animated_gif': '[parsing error]',
            'step_by_step': '[parsing error]'
        }

def parse_dong_chinese_html(html_content):
    """Parse HTML content from Dong Chinese to extract pinyin and meaning"""
    try:
        click.echo("🔍 Looking for JSON data in HTML...")
        
        # Look for the preloaded JSON data in the script tag
        # Pattern: window.preloadedData=[{...}] or window.preloadedData={...}
        json_match = re.search(r'window\.preloadedData=(\[.*?\]|\{.*?\});', html_content, re.DOTALL)
        
        if json_match:
            click.echo("✅ Found JSON match!")
            json_string = json_match.group(1)
            click.echo(f"📄 JSON string preview: {json_string[:200]}...")
            
            data = json.loads(json_string)
            click.echo(f"📊 Parsed data type: {type(data)}")
            
            # Handle single character data (object format)
            if isinstance(data, dict):
                click.echo("🔤 Processing single character data...")
                click.echo(f"🎯 Character data keys: {list(data.keys())}")
                
                pinyin = ''
                meaning = ''
                
                # Get pinyin from pinyinFrequencies
                if 'pinyinFrequencies' in data and len(data['pinyinFrequencies']) > 0:
                    pinyin = data['pinyinFrequencies'][0].get('pinyin', '')
                    click.echo(f"📝 Found pinyin: '{pinyin}'")
                
                # Get meaning from gloss
                if 'gloss' in data:
                    meaning = data['gloss']
                    click.echo(f"📚 Found gloss: '{meaning}'")
                
                # If no gloss, try to get from words array
                if not meaning and 'words' in data and len(data['words']) > 0:
                    # Look for the word that matches the character
                    char = data.get('char', '')
                    for word_entry in data['words']:
                        if word_entry.get('simp') == char or word_entry.get('trad') == char:
                            if 'items' in word_entry and len(word_entry['items']) > 0:
                                definitions = word_entry['items'][0].get('definitions', [])
                                if definitions:
                                    meaning = '; '.join(definitions)
                                    click.echo(f"📚 Found definitions from words: '{meaning}'")
                                    break
                            elif 'gloss' in word_entry:
                                meaning = word_entry['gloss']
                                click.echo(f"📖 Found gloss from words: '{meaning}'")
                                break
                
                click.echo(f"✅ Single character result - Pinyin: '{pinyin}', Meaning: '{meaning}'")
                
                return {
                    'pinyin': pinyin if pinyin else '[pinyin not found]',
                    'meaning': meaning if meaning else '[meaning not found]'
                }
            
            # Handle compound word data (array format)
            elif isinstance(data, list) and len(data) > 0:
                click.echo("🔤 Processing compound word data...")
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
                
                click.echo(f"✅ Compound word result - Pinyin: '{pinyin}', Meaning: '{meaning}'")
                
                return {
                    'pinyin': pinyin if pinyin else '[pinyin not found]',
                    'meaning': meaning if meaning else '[meaning not found]'
                }
            
            else:
                click.echo("❌ Unexpected data format")
                
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

def create_anki_card_output(hanzi, yingyu="", pinyin="", fayin="", lizi="", char_explanation="", stroke_order_html=""):
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
        'Stroke Orders': stroke_order_html,
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
            
            # Fetch stroke order data AND download images
            stroke_data = fetch_stroke_order_data(word)
            
            # Create a card with real pinyin, meaning, and downloaded stroke order images
            card_data = create_anki_card_output(
                hanzi=word,
                yingyu=dong_data['meaning'],
                pinyin=dong_data['pinyin'],
                fayin="[audio placeholder]",
                lizi="[example sentence placeholder]",
                char_explanation="[character explanation placeholder]",
                stroke_order_html=stroke_data['stroke_order_html']
            )
            
            # Display the card
            display_anki_card(card_data)
            all_cards.append(card_data)
            
            # Ask if they want to save and exit
            if click.confirm("\nSave cards to import file and exit?", default=False):
                filename = create_anki_import_file(all_cards)
                click.echo(f"✅ Saved {len(all_cards)} card(s) to {filename}")
                click.echo("📁 Image files are in the 'stroke_order_images' directory")
                click.echo("📋 Copy the image files to your Anki media folder before importing!")
                click.echo("   Anki media folder is usually at:")
                click.echo("   • Windows: %APPDATA%\\Anki2\\[Profile]\\collection.media\\")
                click.echo("   • Mac: ~/Library/Application Support/Anki2/[Profile]/collection.media/")
                click.echo("   • Linux: ~/.local/share/Anki2/[Profile]/collection.media/")
                break
            
        except KeyboardInterrupt:
            if all_cards and click.confirm("\n💾 Save cards before exiting?", default=True):
                filename = create_anki_import_file(all_cards)
                click.echo(f"✅ Saved {len(all_cards)} card(s) to {filename}")
                click.echo("📁 Don't forget to copy images from 'stroke_order_images' to Anki!")
            click.echo("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()