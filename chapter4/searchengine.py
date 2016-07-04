import urllib2
from BeautifulSoup import *
from urlparse import urljoin
import sqlite3

ignore_words = set(['the', 'of', 'to', 'and', 'a', 'an', 'in', 'is', 'it'])


class Crawler:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    def get_entry_id(self, table, field, value, create_new=True):
        # Gets entry id or create new one if doesn't exists
        cur = self.con.execute("select rowid from %s where %s = '%s'" % (table, field, value))
        result = cur.fetchone()
        if result is None:
            cur = self.con.execute("insert into %s (%s) values ('%s')" % (table, field, value))
            return cur.lastrowid
        else:
            return result[0]

    def add_to_index(self, url, soup):
        if self.is_indexed(url):
            return

        print 'Indexing %s' % url

        text = self.get_text_only(soup)
        words = self.separate_words(text)

        urlid = self.get_entry_id('urllist', 'url', url)

        # Link each word to this url
        for i in range(len(words)):
            word = words[i]
            if word in ignore_words:
                continue
            wordid = self.get_entry_id('wordlist', 'word', word)
            self.con.execute("insert into wordlocation(urlid, wordid, location) values (%d, %d, %d)" \
                             % (urlid, wordid, i))

    # Extract HTML text
    def get_text_only(self, soup):
        v = soup.string
        if v is None:
            c = soup.contents
            result_text = ''
            for t in c:
                subtext = self.get_text_only(t)
                result_text += subtext + '\n'
            return result_text
        else:
            return v.strip()

    # Separate words by non-whitespace characters
    def separate_words(self, text):
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != '']

    def is_indexed(self, url):
        u = self.con.execute("select rowid from urllist where url='%s'" % url).fetchone()
        if u is not None:
            # check if it's been crawled
            v = self.con.execute('select * from wordlocation where urlid=%d' % u[0]).fetchone()
            return v is not None
        return False

    # Add link reference between two pages
    def add_link_ref(self, url_from, url_to, link_text):
        words = self.separate_words(link_text)
        from_id = self.get_entry_id('urllist', 'url', url_from)
        to_id = self.get_entry_id('urllist', 'url', url_to)

        if from_id == to_id:
            return

        cur = self.con.execute("insert into link(fromid, toid) values (%d, %d)" % (from_id, to_id))
        link_id = cur.lastrowid

        for word in words:
            if word in ignore_words:
                continue
            word_id = self.get_entry_id('wordlist', 'word', word)
            self.con.execute("insert into linkwords(linkid, wordid) values (%d, %d)" % (link_id, word_id))

    # Starting the first page, breadth first search to a given depth, indexing page as we go
    def crawl(self, pages, depth=2):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    c = urllib2.urlopen(page)
                except:
                    print "Could not open %s" % page
                    continue
                soup = BeautifulSoup(c.read())
                self.add_to_index(page, soup)

                links = soup('a')
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url = urljoin(page, link['href'])
                        if url.find("'") != -1:
                            continue
                        url = url.split('#')[0]  # Remove location portion
                        if url[0:4] == 'http' and not self.is_indexed(url):
                            newpages.add(url)
                        link_text = self.get_text_only(link)
                        self.add_link_ref(page, url, link_text)
                self.dbcommit()
            pages = newpages

    # Create db table
    def create_index_tables(self):
        self.con.execute('CREATE TABLE urllist(url)')
        self.con.execute('CREATE TABLE wordlist(word)')
        self.con.execute('CREATE TABLE wordlocation(urlid, wordid, location)')
        self.con.execute('CREATE TABLE link(fromid INTEGER, toid INTEGER)')
        self.con.execute('CREATE TABLE linkwords(wordid, linkid)')
        self.con.execute('CREATE INDEX wordidx ON wordlist(word)')
        self.con.execute('CREATE INDEX urlidx ON urllist(url)')
        self.con.execute('CREATE INDEX wordurlidx ON wordlocation(wordid)')
        self.con.execute('CREATE INDEX urltoidx ON link(toid)')
        self.con.execute('CREATE INDEX urlfromidx ON link(fromid)')
        self.dbcommit()
