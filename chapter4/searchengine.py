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

    def calculate_pagerank(self, iterations=20):
        self.con.execute('DROP TABLE IF EXISTS pagerank')
        self.con.execute('CREATE TABLE pagerank(urlid PRIMARY KEY, score)')

        # initialize with 1
        self.con.execute('INSERT INTO pagerank SELECT rowid, 1.0 FROM urllist')
        self.dbcommit()

        for i in range(iterations):
            print 'Iteration %d' % (i)
            for (urlid,) in self.con.execute('SELECT rowid FROM urllist'):
                pr = 0.15

                for (linker,) in self.con.execute('select distinct fromid from link where toid=%d' % urlid):
                    linking_pr = self.con.execute('select score from pagerank where urlid=%d' % linker).fetchone()[0]
                    linking_count = self.con.execute('select count(1) from link where fromid=%d' % linker).fetchone()[0]
                    pr += 0.85 * (linking_pr / linking_count)
                self.con.execute('update pagerank set score=%f where urlid=%d' % (pr, urlid))
            self.dbcommit()


class Searcher:
    def __init__(self, dbname):
        self.con = sqlite3.connect(dbname)

    def __del__(self):
        self.con.close()

    def get_match_rows(self, q):
        # Strings to build query
        field_list = 'w0.urlid'
        table_list = ''
        clause_list = ''
        word_ids = []

        # Split words by spaces
        words = q.split(' ')
        table_number = 0

        for word in words:
            word_row = self.con.execute("select rowid from wordlist where word='%s'" % word).fetchone()

            if word_row is not None:
                word_id = word_row[0]
                word_ids.append(word_id)

                if table_number > 0:
                    table_list += ','
                    clause_list += ' and '
                    clause_list += 'w%d.urlid=w%d.urlid and ' % (table_number - 1, table_number)

                field_list += ', w%d.location' % table_number
                table_list += 'wordlocation w%d' % table_number
                clause_list += 'w%d.wordid = %d' % (table_number, word_id)
                table_number += 1

        # Create the query from the separate parts
        full_query = 'select %s from %s where %s ' % (field_list, table_list, clause_list)
        cur = self.con.execute(full_query)
        rows = [row for row in cur]

        return rows, word_ids

    def get_scored_list(self, rows, word_ids):
        total_scores = dict([(row[0], 0) for row in rows])

        weights = [(1.0, self.frequency_score(rows)),
                   (1.0, self.location_score(rows)),
                   (1.0, self.pagerank_score(rows))]

        for (weight, scores) in weights:
            for url in total_scores:
                total_scores[url] += weight * scores[url]

        return total_scores

    def get_url_name(self, id):
        return self.con.execute("select url from urllist where rowid=%d" % id).fetchone()[0]

    def query(self, q):
        rows, word_ids = self.get_match_rows(q)

        scores = self.get_scored_list(rows, word_ids)
        ranked_scores = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
        for (score, url_id) in ranked_scores[0:10]:
            print '%f\t%s' % (score, self.get_url_name(url_id))

    def normalize_scores(self, scores, small_is_better=True):
        very_small = 0.0001  # Avoid division by 0

        if small_is_better:
            min_score = min(scores.values())
            return dict([(u, float(min_score) / max(very_small, l)) for (u, l) in scores.items()])
        else:
            max_score = max(scores.values())
            return dict([(u, float(c) / max_score) for (u, c) in scores.items()])

    def frequency_score(self, rows):
        counts = dict([(row[0], 0) for row in rows])
        for row in rows:
            counts[row[0]] += 1
        return self.normalize_scores(counts, small_is_better=False)

    def location_score(self, rows):
        locations = dict([(row[0], 1000000) for row in rows])
        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]:
                locations[row[0]] = loc

        return self.normalize_scores(locations, small_is_better=True)

    def distance_score(self, rows):
        if len(rows[0]) <= 2:
            return dict([(row[0], 1.0) for row in rows])

        min_distance = dict([(row[0], 1000000) for row in rows])

        for row in rows:
            distance = sum([abs(row[i] - row[i - 1]) for i in range(2, len(row))])
            if distance < min_distance[row[0]]:
                min_distance[row[0]] = distance

        return self.normalize_scores(min_distance, small_is_better=True)

    def inbound_link_score(self, rows):
        unique_urls = set([row[0] for row in rows])
        inbound_count = dict([(u, self.con.execute('select count(1) from link where toid=%d' % u).fetchone()[0]) \
                              for u in unique_urls])

        return self.normalize_scores(inbound_count)

    def pagerank_score(self, rows):
        pageranks = dict([(row[0], self.con.execute('select score from pagerank where urlid=%d' % \
                                                    row[0]).fetchone()[0]) for row in rows])
        max_rank = max(pageranks.values())
        normalized_scores = dict([(u, float(1) / max_rank) for (u, l) in pageranks.items()])
        return normalized_scores
