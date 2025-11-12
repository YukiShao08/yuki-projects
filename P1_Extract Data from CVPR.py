#run in jupyter

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def extract_cvpr2024_papers(url):
    """
    Extract paper information from CVPR 2024 proceedings page
    """
    try:
        # Send GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        papers = []
        
        # Find all paper title elements
        paper_titles = soup.find_all('dt', class_='ptitle')
        
        for title_element in paper_titles:
            paper_info = {}
            
            # Extract paper title
            title_link = title_element.find('a')
            if title_link:
                paper_info['title'] = title_link.get_text(strip=True)
                paper_info['abstract_link'] = urljoin(url, title_link['href'])
            else:
                continue
            
            # Navigate to the next elements for authors and links
            current_element = title_element.find_next_sibling()
            
            # Extract authors (first dd element after title)
            authors = []
            if current_element and current_element.name == 'dd':
                author_forms = current_element.find_all('form', class_='authsearch')
                for form in author_forms:
                    author_link = form.find('a')
                    if author_link:
                        author_name = author_link.get_text(strip=True).rstrip(',')
                        authors.append(author_name)
                paper_info['authors'] = authors
            
            # Extract PDF and supplementary links (second dd element)
            current_element = current_element.find_next_sibling('dd') if current_element else None
            
            if current_element:
                # Find PDF link
                pdf_link = current_element.find('a', href=re.compile(r'.*\.pdf$'))
                if pdf_link and '/papers/' in pdf_link.get('href', ''):
                    paper_info['pdf_link'] = urljoin(url, pdf_link['href'])
                
                # Find supplementary link
                supp_link = current_element.find('a', href=re.compile(r'.*supplemental.*\.pdf$'))
                if supp_link:
                    paper_info['supplementary_link'] = urljoin(url, supp_link['href'])
                
                # Find arXiv link if present
                arxiv_link = current_element.find('a', href=re.compile(r'arxiv\.org'))
                if arxiv_link:
                    paper_info['arxiv_link'] = arxiv_link['href']
            
            papers.append(paper_info)
        
        return papers
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return []

def save_papers_to_file(papers, filename='cvpr2024_papers.json'):
    """Save extracted papers to a JSON file"""
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(papers)} papers to {filename}")

# Main execution
if __name__ == "__main__":
    url = "https://openaccess.thecvf.com/CVPR2024?day=all"
    
    print("Extracting papers from CVPR 2024 proceedings...")
    papers = extract_cvpr2024_papers(url)
    
    if papers:
        print(f"Successfully extracted {len(papers)} papers!")
        save_papers_to_file(papers)
    else:
        print("No papers were extracted. Please check the URL and HTML structure.")
