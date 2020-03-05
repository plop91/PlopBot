from bs4 import BeautifulSoup
import os
import tools.ScanOS.ScanOS as ScanOS
import re

"""

"""
def basicsoup():
    cwd = os.getcwd()
    links = []
    wikis = ScanOS.search("en.wikipedia.org", dir=(cwd + ScanOS.getosslash() + "html-dump"))
    if wikis is not None:
        for path in wikis:
            with open(cwd + ScanOS.getosslash() + "html-dump" + ScanOS.getosslash() + path) as f:
                soup = BeautifulSoup(f, 'html.parser')
            textdump = []
            for tag in soup.find(attrs={'class': 'mw-parser-output'}).find_all('p'):
                text = tag.get_text()
                if not text.isspace():
                    textdump.append(text)
            print(soup.title.string)
            print(textdump[0])
            #with open(cwd + ScanOS.getosslash() + "text-dump" + ScanOS.getosslash() + path, 'w') as f:
            #    f.write(soup.title.string + '\n' + textdump[0] + '\n')

            for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
                links.append(link.get('href'))

        print(links[0])
    if len(links) > 0 :
        with open(cwd + ScanOS.getosslash() + "urls2.txt", 'w') as f:
            for link in links:
                f.write(link.encode('utf-8').strip()+'\n')
